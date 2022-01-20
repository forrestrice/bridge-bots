from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf

from sequence.bidding_context_features import ContextFeature, TargetHcp
from sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)


def decode_example(context_features, sequence_features, record_bytes):
    return tf.io.parse_single_sequence_example(
        record_bytes, context_features=context_features, sequence_features=sequence_features
    )


def build_dataset(
    data_source_path: Path, sequence_features: List[SequenceFeature], context_features: List[ContextFeature]
):
    context_features_schema = {context_feature.name(): context_feature.schema() for context_feature in context_features}
    sequence_features_schema = {
        sequence_feature.name(): sequence_feature.schema() for sequence_feature in sequence_features
    }
    tf_record_dataset = tf.data.TFRecordDataset([str(data_source_path)])
    decoded_dataset = tf_record_dataset.map(partial(decode_example, context_features_schema, sequence_features_schema))
    return decoded_dataset


if __name__ == "__main__":
    sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
    context_features = [TargetHcp()]
    dataset = build_dataset(
        Path("/Users/frice/bridge/bid_learn/deals/toy/train.tfrecord"), sequence_features, context_features
    )
    for example in dataset:
        print(example)
        break
