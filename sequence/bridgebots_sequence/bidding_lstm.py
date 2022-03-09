from functools import partial
from pathlib import Path
from typing import List, Union

import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.layers import Dense, LSTM, concatenate
from tensorflow.keras.models import Model

from bridgebots_sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    CategoricalSequenceFeature, HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
    TargetBiddingSequence,
)
from bridgebots_sequence.dataset_pipeline import build_tfrecord_dataset
from bridgebots_sequence.feature_utils import BIDDING_VOCAB_SIZE


def build_lstm(target: Union[ContextFeature,CategoricalSequenceFeature], sequence_features: List[SequenceFeature], lstm_units=128):
    one_hot_bidding = Input(shape=(None, BIDDING_VOCAB_SIZE), name="one_hot_bidding")
    bidding_mask = Input(shape=(None,), name="bidding_mask", dtype=tf.bool)
    player_position = Input(shape=(None, 4), name="one_hot_player_position")
    holding = Input(shape=(None, 52), name="holding")
    sequence_vulnerability = Input(shape=(None, 2), name="sequence_vulnerability")
    # vulnerability = K.expand_dims(Input(shape=2, name="vulnerability"), axis=2)
    vulnerability = Input(shape=2, name="vulnerability")
    vulnerability_initial_state = tf.keras.layers.Reshape((2, 1))(vulnerability)
    vulnerability_initial_state = tf.keras.layers.ZeroPadding1D(
        padding=(0, lstm_units - 2), name="padded_vulnerability"
    )(vulnerability_initial_state)
    vulnerability_initial_state = tf.keras.layers.Reshape((lstm_units,))(vulnerability_initial_state)
    vulnerability_initial_state = [vulnerability_initial_state, vulnerability_initial_state]

    # TODO and dropout/regularization
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True, return_sequences=True)(
        one_hot_bidding, mask=bidding_mask, initial_state=vulnerability_initial_state
    )
    # TODO consider adding stace_c
    x = concatenate([lstm_outputs, player_position, holding, sequence_vulnerability])
    x = Dense(128, "selu")(x)
    x = Dense(96, "selu")(x)
    x = Dense(64, "selu")(x)
    target_shape = target.num_tokens() if issubclass(target.__class__, CategoricalSequenceFeature) else target.shape()
    output_layer = tf.keras.layers.Dense(target_shape, activation="softmax")(x)
    return Model(
        inputs=[one_hot_bidding, bidding_mask, player_position, holding, sequence_vulnerability, vulnerability],
        outputs=output_layer,
    )


@tf.function
def prepare_targets(target: ContextFeature, contexts, sequences):
    targets = sequences["sequence_" + target.name]
    return sequences, targets

@tf.function
def prepare_sequence_targets(target: str, contexts, sequences):
    targets = sequences[target]
    return sequences, targets


if __name__ == "__main__":
    sequence_features = [
        BiddingSequenceFeature(),
        HoldingSequenceFeature(),
        PlayerPositionSequenceFeature(),
        TargetBiddingSequence(),
    ]
    context_features = [TargetHcp(), Vulnerability()]
    bidding_dataset = build_tfrecord_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), context_features, sequence_features
    )
    validation_dataset = build_tfrecord_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/validation.tfrecord"), context_features, sequence_features
    )

    target = sequence_features[-1]
    # Create X,y tuples for submission to model
    # targeted_dataset = prepared_dataset.map(lambda context, sequence: (sequence, context[target.name()]))
    targeted_dataset = bidding_dataset.map(partial(prepare_sequence_targets, target.prepared_name()), num_parallel_calls=tf.data.AUTOTUNE)
    targeted_validation_dataset = validation_dataset.map(
        partial(prepare_sequence_targets, target.prepared_name()), num_parallel_calls=tf.data.AUTOTUNE
    ).prefetch(tf.data.AUTOTUNE)

    prepared_bidding_dataset = (
        targeted_dataset.cache().shuffle(1_000, reshuffle_each_iteration=True)
        # .map(prepare_lstm_dataset, num_parallel_calls=tf.data.AUTOTUNE)
        .prefetch(tf.data.AUTOTUNE)
    )

    for example in prepared_bidding_dataset:
        print("EXAMPLE\n")
        print(example)
        break
    model = build_lstm(target, sequence_features)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(from_logits=False),
        metrics=[tf.keras.metrics.CategoricalCrossentropy(from_logits=False), "CategoricalAccuracy"],
    )
    print(model.summary())
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir="./logs/run_1_predict_bidding")
    early_stopping_callback = tf.keras.callbacks.EarlyStopping(patience=10)
    # checkpoint_callback = tf.keras.callbacks.ModelCheckpoint("./checkpoints", save_best_only=True)
    model.fit(
        targeted_dataset,
        epochs=10,
        validation_data=targeted_validation_dataset,
        callbacks=[tensorboard_callback, early_stopping_callback],
    )
    model.save("/Users/frice/bridge/bid_learn/models/release/toy/target_bidding_1")
