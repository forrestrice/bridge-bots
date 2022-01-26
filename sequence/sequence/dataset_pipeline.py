from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf

from bridgebots.bids import LEGAL_BIDS
from sequence.bidding_context_features import ContextFeature, TargetHcp
from sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    CategoricalSequenceFeature, HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from sequence.feature_utils import BIDDING_VOCAB_SIZE


def decode_example(context_features, sequence_features, record_bytes):
    return tf.io.parse_single_sequence_example(
        record_bytes, context_features=context_features, sequence_features=sequence_features
    )


def vectorize_bids(bid_vectorization_layer, context, sequence):
    bids = sequence["bidding"]
    sequence["vectorized_bidding"] = bid_vectorization_layer(bids)
    return context, sequence


def create_subsequences(context, sequence):
    vectorized_bidding = sequence["vectorized_bidding"]
    bidding_shape = tf.shape(vectorized_bidding)

    # Transpose and tile the bidding to prepare for subsequence creation. For example:
    # PASS
    # 1D
    # 2S
    # Becomes:
    # PASS 1D 2S
    # PASS 1D 2S
    # PASS 1D 2S
    tiled_bidding = tf.tile(tf.transpose(vectorized_bidding), bidding_shape)

    # Construct a ragged lower triangular matrix of ones to mask the tiled bidding and create subsequences. The example
    # from above becomes:
    # EMPTY
    # PASS
    # PASS 1D
    # PASS 1D 2S
    sequence["bidding_subsequence"] = tf.gather(
        tiled_bidding, tf.ragged.range(tf.range(bidding_shape[0])), batch_dims=1
    )

    # We will eventually use from_tensor_slices to create multiple subsequence examples from a single bidding sequence.
    # Therefore tile the context so that each subsequence example gets its own copy
    tiled_context = {
        context_key: tf.tile(tf.transpose(tf.expand_dims(context_value, axis=1)), bidding_shape)
        for context_key, context_value in context.items()
    }

    return tf.data.Dataset.from_tensor_slices((tiled_context, sequence))


# TODO should this take arguments? Understand this more and leave a better comment.
def convert_ragged_bidding(context, sequence):
    sequence["bidding_subsequence"] = sequence["bidding_subsequence"]
    return context, sequence


def build_dataset(
    data_source_path: Path, sequence_features: List[SequenceFeature], context_features: List[ContextFeature]
):
    context_features_schema = {context_feature.name(): context_feature.schema() for context_feature in context_features}
    sequence_features_schema = {
        sequence_feature.name(): sequence_feature.schema() for sequence_feature in sequence_features
    }
    tf_record_dataset = tf.data.TFRecordDataset([str(data_source_path)])
    decoded_dataset = tf_record_dataset.map(partial(decode_example, context_features_schema, sequence_features_schema), num_parallel_calls=tf.data.AUTOTUNE)

    # Disable standardization - bids have already been standardized by bridgebots
    bid_vectorization_layer = tf.keras.layers.experimental.preprocessing.TextVectorization(
        standardize=None, vocabulary=LEGAL_BIDS
    )
    vectorized_dataset = decoded_dataset.map(partial(vectorize_bids, bid_vectorization_layer), num_parallel_calls=tf.data.AUTOTUNE)
    # TODO remove
    for example in vectorized_dataset:
        #print(example)
        break

    subsequence_dataset = vectorized_dataset.flat_map(create_subsequences).map(convert_ragged_bidding, num_parallel_calls=tf.data.AUTOTUNE)

    bucketed_dataset = subsequence_dataset.bucket_by_sequence_length(
        element_length_func=lambda context, sequence: tf.shape(sequence["bidding_subsequence"])[0],
        bucket_boundaries=[4, 8],  # Boundaries chosen to roughly split number of records evenly
        bucket_batch_sizes=[64, 32, 16],  # TODO experiment
    )

    return bucketed_dataset

def prepare_lstm_dataset(contexts, sequences):
    sequences["bidding_subsequence_mask"] = tf.not_equal(sequences["bidding_subsequence"], 0)
    sequences["one_hot_bidding_subsequence"] = tf.one_hot(sequences["bidding_subsequence"], BIDDING_VOCAB_SIZE + 1, dtype=tf.int64)
    return contexts, sequences



if __name__ == "__main__":
    sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
    context_features = [TargetHcp()]
    dataset = build_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), sequence_features, context_features
    )
    prepared_dataset = dataset.cache().map(prepare_lstm_dataset, num_parallel_calls=tf.data.AUTOTUNE)
    for i, example in enumerate(prepared_dataset):
        print(example, type(example), len(example))
        if i > 3:
            break
