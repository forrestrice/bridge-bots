from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf

from sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)


@tf.function
def decode_example(context_features, sequence_features, record_bytes):
    return tf.io.parse_single_sequence_example(
        record_bytes, context_features=context_features, sequence_features=sequence_features
    )


@tf.function
def prepare_lstm_dataset_smart(
    context_features: List[ContextFeature], sequence_features: List[SequenceFeature], contexts, sequences
):
    for sequence_feature in sequence_features:
        sequences = sequence_feature.prepare_dataset(sequences)

    bidding_shape = tf.shape(sequences["bidding"])
    batch_size, time_steps = bidding_shape[0], bidding_shape[1]
    for context_feature in context_features:
        contexts, sequences = context_feature.prepare_dataset(contexts, sequences, batch_size, time_steps)
    return contexts, sequences


def build_dataset(
    data_source_path: Path, context_features: List[ContextFeature], sequence_features: List[SequenceFeature]
):
    context_features_schema = {context_feature.name: context_feature.schema() for context_feature in context_features}
    sequence_features_schema = {
        sequence_feature.name: sequence_feature.schema() for sequence_feature in sequence_features
    }
    tf_record_dataset = tf.data.TFRecordDataset([str(data_source_path)])
    decoded_dataset = tf_record_dataset.map(
        partial(decode_example, context_features_schema, sequence_features_schema), num_parallel_calls=tf.data.AUTOTUNE
    )

    bidding_feature = next((sf for sf in sequence_features if isinstance(sf, BiddingSequenceFeature)), None)
    if bidding_feature:
        bidding_dataset = decoded_dataset.map(bidding_feature.vectorize, num_parallel_calls=tf.data.AUTOTUNE)
    else:
        raise ValueError("No BiddingSequenceFeature detected. It is currently required by the data pipeline.")

    # TODO remove
    for example in bidding_dataset:
        # print(example)
        break

    bucketed_dataset = bidding_dataset.bucket_by_sequence_length(
        element_length_func=lambda context, sequence: tf.shape(sequence[bidding_feature.vectorized_name])[0],
        bucket_boundaries=[9, 11, 15],  # Boundaries chosen to roughly split number of records evenly
        bucket_batch_sizes=[64, 48, 32, 16],  # TODO experiment
    )

    lstm_dataset = bucketed_dataset.map(
        partial(prepare_lstm_dataset_smart, context_features, sequence_features), num_parallel_calls=tf.data.AUTOTUNE
    )
    return lstm_dataset


if __name__ == "__main__":
    tf.config.run_functions_eagerly(False)
    sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
    context_features = [TargetHcp(), Vulnerability()]
    dataset = build_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), context_features, sequence_features
    )
    # prepared_dataset = dataset.cache().map(prepare_lstm_dataset, num_parallel_calls=tf.data.AUTOTUNE)
    for i, example in enumerate(dataset):
        print("EXAMPLE")
        print(example, type(example), len(example), type(example[0]), type(example[1]))
        if i > -1:
            break
