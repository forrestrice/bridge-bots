from pathlib import Path
from typing import List

import tensorflow as tf
from keras.layers import Dense, LSTM
from tensorflow.keras import Input, Model, layers

from sequence.bidding_context_features import ContextFeature, TargetHcp
from sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    CategoricalSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from sequence.dataset_pipeline import build_dataset, prepare_lstm_dataset
from sequence.feature_utils import BIDDING_VOCAB_SIZE


def build_lstm(target: ContextFeature, sequence_features: List[SequenceFeature]):
    # Bidding subsequence is a special case since it is the LSTM input so handle names/encoding/inputs manually
    bidding_feature = None
    for sequence_feature in sequence_features:
        if isinstance(sequence_feature, BiddingSequenceFeature):
            bidding_feature = sequence_feature
            sequence_features.remove(bidding_feature)
            break
    if bidding_feature is None:
        raise ValueError("Missing bidding feature for LSTM")

    one_hot_bidding = Input(shape=(None, BIDDING_VOCAB_SIZE + 1), name="one_hot_bidding_subsequence")
    bidding_mask = Input(shape=(None,), name="bidding_subsequence_mask", dtype=tf.bool)
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True)(one_hot_bidding, mask=bidding_mask)

    feature_inputs = [one_hot_bidding, bidding_mask]
    feature_outputs = []
    for sequence_feature in sequence_features:
        feature_input = Input(shape=sequence_feature.shape(), name=sequence_feature.name())
        feature_inputs.append(feature_input)
        if issubclass(sequence_feature.__class__, CategoricalSequenceFeature):
            feature_outputs.append(
                tf.keras.layers.CategoryEncoding(num_tokens=sequence_feature.num_tokens(), output_mode="one_hot")(
                    feature_input
                )
            )
        else:
            feature_outputs.append(feature_input)
    all_features = layers.concatenate(feature_outputs)
    # player_input_layer = Input(shape=(4), name="one_hot_player_position")
    # holding_input_layer = Input(shape=(52), name="HoldingSequence")

    # consider including cell state
    # x = layers.concatenate([lstm_outputs, state_c, holding_input_layer])
    x = layers.concatenate([lstm_outputs, all_features])
    x = Dense(256, "selu")(x)
    x = Dense(128, "selu")(x)
    x = Dense(64, "selu")(x)
    output_layer = tf.keras.layers.Dense(target.shape())(x)
    return Model(inputs=feature_inputs, outputs=output_layer)


if __name__ == "__main__":
    sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
    context_features = [TargetHcp()]
    bidding_dataset = build_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), sequence_features, context_features
    )
    prepared_dataset = (
        bidding_dataset
        .cache()
        .shuffle(1_000, reshuffle_each_iteration=True)
        .map(prepare_lstm_dataset, num_parallel_calls=tf.data.AUTOTUNE)
        .prefetch(tf.data.AUTOTUNE)
    )
    target = context_features[0]
    # Create X,y tuples for submission to model
    targeted_dataset = prepared_dataset.map(lambda context, sequence: (sequence, context[target.name()]))
    for example in targeted_dataset:
        print("EXAMPLE\n")
        print(example)
        break
    model = build_lstm(target, sequence_features)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.MeanSquaredError(),
        metrics=["mae", "mse"],
    )
    print(model.summary())
    model.fit(targeted_dataset, epochs=3)
    model.save("/Users/frice/bridge/bid_learn/models/release/toy/hcp_3")
