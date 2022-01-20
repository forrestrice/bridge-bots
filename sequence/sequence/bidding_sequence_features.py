from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import tensorflow as tf

from bridgebots import BoardRecord, DealRecord, Direction


@dataclass
class BiddingSequenceExampleData:
    deal_record: DealRecord
    board_record: BoardRecord
    holdings: Dict[Direction, List]


class SequenceFeature(ABC):
    @abstractmethod
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        raise NotImplementedError

    @abstractmethod
    def name(self):
        raise NotImplementedError

    @abstractmethod
    def schema(self):
        raise NotImplementedError


class HoldingSequenceFeature(SequenceFeature):
    def schema(self):
        return tf.io.FixedLenSequenceFeature([52], dtype=tf.int64)

    def name(self):
        return "holding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        dealer = bidding_data.deal_record.deal.dealer
        sequence_feature = []
        for i, bid in enumerate(bidding_data.board_record.bidding_record):
            player = dealer.offset(i)
            holding = bidding_data.holdings[player]
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=holding))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)


class BiddingSequenceFeature(SequenceFeature):
    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    def name(self):
        return "bidding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_feature = [
            tf.train.Feature(bytes_list=tf.train.BytesList(value=[str.encode(bid)]))
            for bid in bidding_data.board_record.bidding_record
        ]
        return tf.train.FeatureList(feature=bidding_feature)


class PlayerPositionSequenceFeature(SequenceFeature):
    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    def name(self):
        return "player_position"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for i in range(len(bidding_data.board_record.bidding_record)):
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=[i % 4]))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)
