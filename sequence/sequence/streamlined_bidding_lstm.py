from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf
from keras.layers import Dense, LSTM
from tensorflow.keras import Input, Model, layers

from sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from sequence.feature_utils import BIDDING_VOCAB_SIZE
from sequence.streamlined_dataset_pipeline import build_dataset


def build_lstm(target: ContextFeature, sequence_features: List[SequenceFeature]):
    one_hot_bidding = Input(shape=(None, BIDDING_VOCAB_SIZE), name="one_hot_bidding")
    bidding_mask = Input(shape=(None,), name="bidding_mask", dtype=tf.bool)
    player_position = Input(shape=(None, 4), name="one_hot_player_position")
    holding = Input(shape=(None, 52), name="holding")
    vulnerability = Input(shape=(None, 2), name="sequence_vulnerability")

    # TODO initialization with vulnerability and dropout/regularization
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True, return_sequences=True)(
        one_hot_bidding, mask=bidding_mask
    )
    # TODO consider adding stace_c
    x = layers.concatenate([lstm_outputs, player_position, holding, vulnerability])
    x = Dense(64, "selu")(x)
    x = Dense(16, "selu")(x)
    x = Dense(8, "selu")(x)
    output_layer = tf.keras.layers.Dense(target.shape())(x)
    return Model(inputs=[one_hot_bidding, bidding_mask, player_position, holding, vulnerability], outputs=output_layer)


@tf.function
def prepare_targets(target: ContextFeature, contexts, sequences):
    targets = sequences["sequence_" + target.name]
    return sequences, targets


if __name__ == "__main__":
    sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
    context_features = [TargetHcp(), Vulnerability()]
    bidding_dataset = build_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), context_features, sequence_features
    )

    target = context_features[0]
    # Create X,y tuples for submission to model
    # targeted_dataset = prepared_dataset.map(lambda context, sequence: (sequence, context[target.name()]))
    targeted_dataset = bidding_dataset.map(partial(prepare_targets, target), num_parallel_calls=tf.data.AUTOTUNE)

    prepared_dataset = (
        targeted_dataset.cache().shuffle(1_000, reshuffle_each_iteration=True)
        # .map(prepare_lstm_dataset, num_parallel_calls=tf.data.AUTOTUNE)
        .prefetch(tf.data.AUTOTUNE)
    )

    for example in prepared_dataset:
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
