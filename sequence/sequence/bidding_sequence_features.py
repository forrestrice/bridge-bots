from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import tensorflow as tf

from bridgebots import BoardRecord, DealRecord, Direction
from bridgebots.bids import LEGAL_BIDS
from sequence.feature_utils import BIDDING_VOCAB_SIZE


@dataclass
class BiddingSequenceExampleData:
    deal_record: DealRecord
    board_record: BoardRecord
    holdings: Dict[Direction, List]


class SequenceFeature(ABC):
    @abstractmethod
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @abstractmethod
    def schema(self):
        raise NotImplementedError

    @abstractmethod
    def shape(self):
        raise NotImplementedError

    def prepared_name(self):
        return self.name()

    @abstractmethod
    @tf.function
    def prepare_dataset(self, sequences):
        raise NotImplementedError


class CategoricalSequenceFeature(SequenceFeature, ABC):
    @abstractmethod
    def num_tokens(self):
        raise NotImplementedError

    def prepared_name(self):
        return "one_hot_" + self.name()


class HoldingSequenceFeature(SequenceFeature):
    def shape(self):
        return 52

    def schema(self):
        return tf.io.FixedLenSequenceFeature([52], dtype=tf.int64)

    @property
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

    @tf.function
    def prepare_dataset(self, sequences):
        return sequences


class PlayerPositionSequenceFeature(CategoricalSequenceFeature):
    def num_tokens(self):
        return 4

    def shape(self):
        return 1

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    @property
    def name(self):
        return "player_position"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for i in range(len(bidding_data.board_record.bidding_record)):
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=[i % 4]))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)

    @tf.function
    def prepare_dataset(self, sequences):
        sequences = sequences.copy()
        sequences["one_hot_player_position"] = tf.one_hot(tf.squeeze(sequences[self.name]), depth=self.num_tokens())
        return sequences


class BiddingSequenceFeature(CategoricalSequenceFeature):

    # Disable standardization - bids have already been standardized by bridgebots
    bid_vectorization_layer = tf.keras.layers.experimental.preprocessing.TextVectorization(
        standardize=None, vocabulary=LEGAL_BIDS
    )

    def num_tokens(self):
        return BIDDING_VOCAB_SIZE

    def shape(self):
        return None

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    @property
    def name(self):
        return "bidding"

    @property
    def vectorized_name(self):
        return "vectorized_bidding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_feature = [
            tf.train.Feature(bytes_list=tf.train.BytesList(value=[str.encode(bid)]))
            for bid in bidding_data.board_record.bidding_record
        ]
        return tf.train.FeatureList(feature=bidding_feature)

    @tf.function
    def vectorize(self, context, sequence):
        sequence_copy = sequence.copy()
        sequence_copy[self.vectorized_name] = self.bid_vectorization_layer(sequence[self.name])
        return context, sequence_copy

    @tf.function
    def prepare_dataset(self, sequences):
        sequences = sequences.copy()
        sequences["bidding_mask"] = tf.not_equal(tf.squeeze(sequences[self.vectorized_name]), 0)
        sequences["one_hot_bidding"] = tf.one_hot(tf.squeeze(sequences[self.vectorized_name]), BIDDING_VOCAB_SIZE, dtype=tf.int64)
        return sequences
