from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf

from bridgebots_sequence.bidding_context_features import ContextFeature, TargetHcp, TargetShape, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BidAlertedSequenceFeature,
    BidExplainedSequenceFeature,
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
    TargetBiddingSequence,
)


@tf.function
def decode_example(context_features, sequence_features, record_bytes):
    return tf.io.parse_single_sequence_example(
        record_bytes, context_features=context_features, sequence_features=sequence_features
    )


@tf.function
def prepare_lstm_dataset(
    context_features: List[ContextFeature], sequence_features: List[SequenceFeature], contexts, sequences
):
    for sequence_feature in sequence_features:
        sequences = sequence_feature.prepare_dataset(sequences)

    bidding_shape = tf.shape(sequences["bidding"])
    batch_size, time_steps = bidding_shape[0], bidding_shape[1]
    for context_feature in context_features:
        contexts, sequences = context_feature.prepare_dataset(contexts, sequences, batch_size, time_steps)
    return contexts, sequences


@tf.function
def build_tfrecord_dataset(
    data_source_path: Path, context_features: List[ContextFeature], sequence_features: List[SequenceFeature]
) -> tf.data.Dataset:
    tf_record_dataset = tf.data.TFRecordDataset([str(data_source_path)])
    context_features_schema, sequence_features_schema = _build_schema(context_features, sequence_features)
    decoded_dataset = tf_record_dataset.map(
        partial(decode_example, context_features_schema, sequence_features_schema), num_parallel_calls=tf.data.AUTOTUNE
    )
    bidding_feature = next((sf for sf in sequence_features if isinstance(sf, BiddingSequenceFeature)), None)
    if bidding_feature:
        bidding_dataset = decoded_dataset.map(bidding_feature.vectorize, num_parallel_calls=tf.data.AUTOTUNE)
    else:
        raise ValueError("No BiddingSequenceFeature detected. It is currently required by the data pipeline.")

    target_bidding_feature = next((sf for sf in sequence_features if isinstance(sf, TargetBiddingSequence)), None)
    if target_bidding_feature:
        bidding_dataset = bidding_dataset.map(target_bidding_feature.vectorize, num_parallel_calls=tf.data.AUTOTUNE)

    bucketed_dataset = bidding_dataset.bucket_by_sequence_length(
        element_length_func=lambda context, sequence: tf.shape(sequence[bidding_feature.vectorized_name])[0],
        bucket_boundaries=[9, 11, 15],  # Boundaries chosen to roughly split number of records evenly
        bucket_batch_sizes=[64, 48, 32, 16],  # TODO experiment
    )

    lstm_dataset = bucketed_dataset.map(
        partial(prepare_lstm_dataset, context_features, sequence_features), num_parallel_calls=tf.data.AUTOTUNE
    )
    return lstm_dataset


def _build_schema(context_features: List[ContextFeature], sequence_features: List[SequenceFeature]):
    context_features_schema = {context_feature.name: context_feature.schema for context_feature in context_features}
    sequence_features_schema = {
        sequence_feature.name: sequence_feature.schema for sequence_feature in sequence_features
    }
    return context_features_schema, sequence_features_schema


def build_inference_dataset(
    protobuff_dataset: tf.data.Dataset, context_features: List[ContextFeature], sequence_features: List[SequenceFeature]
):
    context_features_schema, sequence_features_schema = _build_schema(context_features, sequence_features)
    decoded_dataset = protobuff_dataset.map(
        partial(decode_example, context_features_schema, sequence_features_schema), num_parallel_calls=tf.data.AUTOTUNE
    )
    bidding_feature = next((sf for sf in sequence_features if isinstance(sf, BiddingSequenceFeature)), None)
    if bidding_feature:
        bidding_dataset = decoded_dataset.map(bidding_feature.vectorize, num_parallel_calls=tf.data.AUTOTUNE)
    else:
        raise ValueError("No BiddingSequenceFeature detected. It is currently required by the data pipeline.")
    batched_dataset = bidding_dataset.batch(1)
    lstm_dataset = batched_dataset.map(
        partial(prepare_lstm_dataset, context_features, sequence_features), num_parallel_calls=tf.data.AUTOTUNE
    )
    return lstm_dataset.map(lambda contexts, sequences: sequences)


if __name__ == "__main__":
    tf.config.run_functions_eagerly(False)
    sequence_features = [
        BiddingSequenceFeature(),
        HoldingSequenceFeature(),
        PlayerPositionSequenceFeature(),
        BidAlertedSequenceFeature(),
        BidExplainedSequenceFeature(),
        TargetBiddingSequence(),
    ]
    context_features = [TargetHcp(), Vulnerability(), TargetShape()]
    dataset = build_tfrecord_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), context_features, sequence_features
    )
    # prepared_dataset = dataset.cache().map(prepare_lstm_dataset, num_parallel_calls=tf.data.AUTOTUNE)
    for i, example in enumerate(dataset):
        print("EXAMPLE")
        print(example)
        if i > 3:
            break
