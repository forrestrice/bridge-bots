import logging
from functools import partial
from pathlib import Path
from typing import List, Optional, Tuple, Union

import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.callbacks import History
from tensorflow.keras.layers import Dense, LSTM, concatenate
from tensorflow.keras.models import Model

from bridgebots_sequence.bidding_context_features import ContextFeature, TargetShape, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    CategoricalSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
    TargetBiddingSequence,
)
from bridgebots_sequence.dataset_pipeline import build_tfrecord_dataset
from bridgebots_sequence.feature_utils import (
    BIDDING_VOCAB_SIZE,
    SampleWeightsCalculator,
)
from bridgebots_sequence.interpreter import (
    ModelInterpreter,
    ModelInterpreterMixin,
)
from bridgebots_sequence.model_metadata import ModelMetadata
from bridgebots_sequence.sequence_schemas import ModelMetadataSchema
from bridgebots_sequence.training_utils import build_training_metrics, prepare_targets


def build_datasets(
    training_data_path: Path,
    validation_data_path: Optional[Path],
    context_features: List[ContextFeature],
    sequence_features: List[SequenceFeature],
    target: Union[ContextFeature, SequenceFeature],
    shuffle_size: Optional[int] = 1_000,
    sample_weights_calculator: SampleWeightsCalculator = None,
    bucket_boundaries: Optional[Tuple[int, ...]] = None,
    bucket_batch_sizes: Optional[Tuple[int, ...]] = None,
):
    bidding_dataset = build_tfrecord_dataset(
        training_data_path,
        context_features,
        sequence_features,
        sample_weights_calculator,
        bucket_boundaries,
        bucket_batch_sizes,
    )

    # Create X,y tuples for submission to model
    target_name = target.sequence_name if isinstance(target, ContextFeature) else target.prepared_name
    sample_weights_name = sample_weights_calculator.name if sample_weights_calculator else None

    targeted_dataset = bidding_dataset.map(
        partial(prepare_targets, target_name, sample_weights_name), num_parallel_calls=tf.data.AUTOTUNE
    ).cache()

    if shuffle_size:
        targeted_dataset = targeted_dataset.shuffle(shuffle_size, reshuffle_each_iteration=True)

    targeted_dataset = targeted_dataset.prefetch(tf.data.AUTOTUNE)

    targeted_validation_dataset = None
    if validation_data_path:
        validation_dataset = build_tfrecord_dataset(
            validation_data_path,
            context_features,
            sequence_features,
            sample_weights_calculator,
            bucket_boundaries,
            bucket_batch_sizes,
        )

        targeted_validation_dataset = (
            validation_dataset.map(
                partial(prepare_targets, target_name, sample_weights_name), num_parallel_calls=tf.data.AUTOTUNE
            )
            .cache()
            .prefetch(tf.data.AUTOTUNE)
        )

    return targeted_dataset, targeted_validation_dataset


def build_lstm(
    lstm_units: int,
    lstm_layers: int,
    dense_layers: List[Dense],
    final_layer: Dense,
    regularizer: tf.keras.regularizers.Regularizer,
    recurrent_dropout: float,
    include_metadata_features: bool,
    include_lstm_input_features: bool,
):
    one_hot_bidding = Input(shape=(None, BIDDING_VOCAB_SIZE), name="one_hot_bidding")
    bidding_mask = Input(shape=(None,), name="bidding_mask", dtype=tf.bool)
    player_position = Input(shape=(None, 4), name="one_hot_player_position")
    holding = Input(shape=(None, 52), name="holding")
    sequence_vulnerability = Input(shape=(None, 2), name="sequence_vulnerability")
    bid_alerted = Input(shape=(None, 1), name="alerted")
    bid_explained = Input(shape=(None, 1), name="explained")
    # TODO explain how vulnerability initialization works
    vulnerability = Input(shape=2, name="vulnerability")
    vulnerability_initial_state = tf.keras.layers.Reshape((2, 1))(vulnerability)
    vulnerability_initial_state = tf.keras.layers.ZeroPadding1D(
        padding=(0, lstm_units - 2), name="padded_vulnerability"
    )(vulnerability_initial_state)
    vulnerability_initial_state = tf.keras.layers.Reshape((lstm_units,))(vulnerability_initial_state)
    vulnerability_initial_state = [vulnerability_initial_state, vulnerability_initial_state]

    # TODO and dropout/regularization
    if include_lstm_input_features:
        lstm_inputs = concatenate([one_hot_bidding, player_position, sequence_vulnerability])
    else:
        lstm_inputs = one_hot_bidding
    lstm_outputs = None
    for i in range(lstm_layers):
        lstm_outputs, state_h, state_c = LSTM(
            units=lstm_units,
            return_state=True,
            return_sequences=True,
            kernel_regularizer=regularizer,
            recurrent_dropout=recurrent_dropout,
        )(lstm_inputs, mask=bidding_mask, initial_state=vulnerability_initial_state)
        if include_lstm_input_features:
            lstm_inputs = concatenate([lstm_outputs, player_position, sequence_vulnerability])
        else:
            lstm_inputs = lstm_outputs
    # TODO consider adding stace_c
    features = [lstm_outputs, player_position, holding, sequence_vulnerability]
    if include_metadata_features:
        features.extend([bid_alerted, bid_explained])
    x = concatenate(features)
    for layer in dense_layers:
        x = layer(x)
    output = final_layer(x)
    inputs = [one_hot_bidding, bidding_mask, player_position, holding, sequence_vulnerability, vulnerability]
    if include_metadata_features:
        inputs.extend([bid_alerted, bid_explained])
    return Model(
        inputs=inputs,
        outputs=output,
    )


def save_model(
    training_data_path: Path,
    validation_data_path: Optional[Path],
    context_features: List[ContextFeature],
    sequence_features: List[SequenceFeature],
    target: Union[ContextFeature, SequenceFeature],
    model_interpreter: ModelInterpreter,
    description: str,
    model: Model,
    history: History,
    save_path: Path,
):
    training_metrics = build_training_metrics(history)
    model.save(save_path)
    model_metadata = ModelMetadata(
        training_data_path,
        validation_data_path,
        context_features,
        sequence_features,
        target,
        model_interpreter,
        description,
        training_metrics,
    )
    with open(save_path / "metadata.json", "w") as metadata_file:
        metadata_file.write(ModelMetadataSchema().dumps(model_metadata))


if __name__ == "__main__":
    tf.config.run_functions_eagerly(True)
    sequence_features = [
        BiddingSequenceFeature(),
        HoldingSequenceFeature(),
        PlayerPositionSequenceFeature(),
    ]
    context_features = [Vulnerability()]

    target: Union[CategoricalSequenceFeature, ContextFeature, ModelInterpreterMixin] = TargetShape()
    if isinstance(target, SequenceFeature):
        sequence_features.append(target)
    else:
        context_features.append(target)
    sample_weights_calculator = None
    run_directory = target.name + "_toy"
    run_number = 1

    training_data_path = Path("/Users/frice/bridge/bid_learn/deals/toy/no_duplicates_train.tfrecord")
    validation_data_path = None  # Path("/Users/frice/bridge/bid_learn/deals/toy/validation.tfrecord")

    regularizer = None  # tf.keras.regularizers.L2(0.01)
    lstm_units = 128
    lstm_layers = 1
    recurrent_dropout = 0  # 0.1
    dense_layers = [
        Dense(128, "selu", kernel_regularizer=regularizer),
        Dense(96, "selu", kernel_regularizer=regularizer),
        Dense(64, "selu", kernel_regularizer=regularizer),
    ]

    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)

    if isinstance(target, TargetBiddingSequence):
        from_logits = False
        loss = tf.keras.losses.CategoricalCrossentropy(from_logits=from_logits)
        metrics = [tf.keras.metrics.CategoricalCrossentropy(from_logits=from_logits), "CategoricalAccuracy"]
        activation = "linear" if from_logits else "softmax"
        final_layer = Dense(target.num_tokens, activation=activation)
        model_interpreter = target.model_interpreter(from_logits)
    else:
        loss = tf.keras.losses.MeanSquaredError()
        metrics = ["mae", "mse"]
        final_layer = Dense(target.shape, activation="linear")
        model_interpreter = target.model_interpreter()

    weighted_metrics = None
    if sample_weights_calculator:
        weighted_metrics = metrics
        metrics = None

    model = build_lstm(
        lstm_units,
        lstm_layers,
        dense_layers,
        final_layer,
        regularizer,
        recurrent_dropout,
        include_metadata_features=False,
        include_lstm_input_features=True,
    )
    model.compile(optimizer=optimizer, loss=loss, metrics=metrics, weighted_metrics=weighted_metrics)

    bucket_boundaries = (9, 11, 15)
    bucket_batch_sizes = (64, 48, 32, 16)
    training_dataset, validation_dataset = build_datasets(
        training_data_path,
        validation_data_path,
        context_features,
        sequence_features,
        target,
        # shuffle_size=None,
        sample_weights_calculator=sample_weights_calculator,
        bucket_boundaries=bucket_boundaries,
        bucket_batch_sizes=bucket_batch_sizes,
    )
    batches = 100
    training_dataset = training_dataset.take(batches).shuffle(batches).cache()

    for entry in training_dataset:
        print(entry)
        break

    callbacks = [
        tf.keras.callbacks.TensorBoard(log_dir=f"./logs/{run_directory}/run_{run_number}"),
        # tf.keras.callbacks.EarlyStopping(patience=100),
        # tf.keras.callbacks.ModelCheckpoint(
        #    filepath=f"drive/MyDrive/bid_learn/models/{run_directory}/run_{run_number}_checkpoints", save_best_only=True
        # ),
    ]

    logging.info(model.summary())
    history = model.fit(
        training_dataset,
        epochs=200,
        validation_data=validation_dataset,
        callbacks=callbacks,
    )

    description = (
        "Predict the bid of the next player to act. Uses the bidding so far, the holding of the player, and the "
        "vulnerability of each side as features."
    )

    save_model(
        training_data_path,
        validation_data_path,
        context_features,
        sequence_features,
        target,
        model_interpreter,
        description,
        model,
        history,
        save_path=Path(f"/Users/frice/bridge/models/{run_directory}/run_{run_number}"),
    )
