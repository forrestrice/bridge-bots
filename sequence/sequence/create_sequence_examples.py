import logging
import pickle
from pathlib import Path
from typing import Dict, List

import tensorflow as tf
from tensorflow.python.lib.io.tf_record import TFRecordCompressionType

from bridgebots import DealRecord
from sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from sequence.bidding_sequence_features import (
    BiddingSequenceExampleData,
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from sequence.feature_utils import holding


class OneHandSequenceExampleGenerator:
    def __init__(
        self,
        deal_records: List[DealRecord],
        context_features: List[ContextFeature],
        sequence_features: List[SequenceFeature],
    ):
        self.deal_records = deal_records
        self.context_features = context_features
        self.sequence_features = sequence_features

    def __iter__(self):
        for deal_record in self.deal_records:
            dealer = deal_record.deal.dealer
            # Holdings and context features do not change across board records so may be calculated once per deal
            player_holdings = {dealer.offset(i): holding(dealer.offset(i), deal_record) for i in range(4)}
            calculated_context_features = {
                context_feature.name: context_feature.calculate(deal_record)
                for context_feature in self.context_features
            }
            for board_record in deal_record.board_records:
                bidding_data = BiddingSequenceExampleData(deal_record, board_record, player_holdings)
                yield self.build_sequence_example(bidding_data, calculated_context_features)

    def build_sequence_example(
        self, bidding_data: BiddingSequenceExampleData, calculated_context_features: Dict[str, tf.train.Feature]
    ):
        context = tf.train.Features(feature=calculated_context_features)
        calculated_sequence_features = {
            feature.name: feature.calculate(bidding_data) for feature in self.sequence_features
        }
        feature_lists = tf.train.FeatureLists(feature_list=calculated_sequence_features)
        return tf.train.SequenceExample(context=context, feature_lists=feature_lists)


def create_examples(
    source_pickle: Path,
    save_path: Path,
    context_features=List[ContextFeature],
    sequence_features=List[SequenceFeature],
    compression_type: TFRecordCompressionType = TFRecordCompressionType.NONE,
    max_records : int = None
):

    with open(source_pickle, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    example_gen = iter(OneHandSequenceExampleGenerator(deal_records, context_features, sequence_features))
    with tf.io.TFRecordWriter(str(save_path), compression_type) as file_writer:
        for i, example in enumerate(example_gen):
            file_writer.write(example.SerializeToString())
            if i > 0 and i % 10_000 == 0:
                logging.debug(f"wrote {i} results to {save_path.name}")
            if max_records and i > max_records:
                break


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
    context_features = [TargetHcp(), Vulnerability()]
    # TODO train/test/validation loop
    create_examples(
        Path("/Users/frice/bridge/bid_learn/deals/train.pickle"),
        Path("/Users/frice/bridge/bid_learn/deals/train.tfrecord"),
        context_features,
        sequence_features,
        #max_records=20
    )
