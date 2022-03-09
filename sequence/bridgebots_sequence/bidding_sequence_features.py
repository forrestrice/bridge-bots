from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import tensorflow as tf

from bridgebots import BidMetadata, Direction
from bridgebots_sequence.feature_utils import BIDDING_VOCAB, BIDDING_VOCAB_SIZE, TARGET_BIDDING_VOCAB


@dataclass
class BiddingSequenceExampleData:
    dealer: Direction
    bidding_record: List[str]
    bidding_metadata: List[BidMetadata]
    holdings: Dict[Direction, List[int]]


class SequenceFeature(ABC):
    @abstractmethod
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    def prepared_name(self):
        return self.name

    @abstractmethod
    @tf.function
    def prepare_dataset(self, sequences):
        pass

    # Currently, features do not have any internal state - they are just collections of functions, so we can compare
    # equality and hash by class
    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class CategoricalSequenceFeature(SequenceFeature, ABC):
    @abstractmethod
    def num_tokens(self):
        pass

    def prepared_name(self):
        return "one_hot_" + self.name


class HoldingSequenceFeature(SequenceFeature):
    def schema(self):
        return tf.io.FixedLenSequenceFeature([52], dtype=tf.int64)

    @property
    def name(self):
        return "holding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for i in range(len(bidding_data.bidding_record) + 1):  # +1 to account for SOS token
            player = bidding_data.dealer.offset(i)
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

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    @property
    def name(self):
        return "player_position"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for i in range(len(bidding_data.bidding_record) + 1):  # +1 to account for SOS token
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=[i % 4]))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)

    @tf.function
    def prepare_dataset(self, sequences):
        sequences = sequences.copy()
        sequences["one_hot_player_position"] = tf.one_hot(
            tf.squeeze(sequences[self.name], axis=2), depth=self.num_tokens()
        )
        return sequences


class BiddingSequenceFeature(CategoricalSequenceFeature):
    # Disable standardization - bids have already been standardized by bridgebots
    bid_vectorization_layer = tf.keras.layers.StringLookup(num_oov_indices=1, vocabulary=BIDDING_VOCAB)

    def num_tokens(self):
        return BIDDING_VOCAB_SIZE

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    @property
    def name(self):
        return "bidding"

    @property
    def vectorized_name(self):
        return "vectorized_bidding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_with_sos = ["SOS"] + bidding_data.bidding_record
        bidding_feature = [
            tf.train.Feature(bytes_list=tf.train.BytesList(value=[str.encode(bid)])) for bid in bidding_with_sos
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
        sequences["bidding_mask"] = tf.not_equal(tf.squeeze(sequences[self.vectorized_name], axis=2), 0)
        sequences["one_hot_bidding"] = tf.one_hot(
            tf.squeeze(sequences[self.vectorized_name], axis=2), BIDDING_VOCAB_SIZE, dtype=tf.int64
        )
        return sequences


class TargetBiddingSequence(CategoricalSequenceFeature):
    # Disable standardization - bids have already been standardized by bridgebots
    bid_vectorization_layer = tf.keras.layers.StringLookup(num_oov_indices=1, vocabulary=TARGET_BIDDING_VOCAB)

    def num_tokens(self):
        return BIDDING_VOCAB_SIZE

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    @property
    def name(self):
        return "target_bidding"

    @property
    def vectorized_name(self):
        return "target_vectorized_bidding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_with_eos = bidding_data.bidding_record + ["EOS"]
        bidding_feature = [
            tf.train.Feature(bytes_list=tf.train.BytesList(value=[str.encode(bid)])) for bid in bidding_with_eos
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
        sequences["one_hot_target_bidding"] = tf.one_hot(
            tf.squeeze(sequences[self.vectorized_name], axis=2), BIDDING_VOCAB_SIZE, dtype=tf.int64
        )
        return sequences


class BidAlertedSequenceFeature(SequenceFeature):
    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    @property
    def name(self):
        return "alerted"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        alerted_vector = [0] * (len(bidding_data.bidding_record) + 1)  # +1 to account for SOS token
        for bid_metadata in bidding_data.bidding_metadata:
            if bid_metadata.alerted:
                alerted_vector[bid_metadata.bid_index + 1] = 1
        alerted_feature = [
            tf.train.Feature(int64_list=tf.train.Int64List(value=[alert_flag])) for alert_flag in alerted_vector
        ]
        return tf.train.FeatureList(feature=alerted_feature)

    @tf.function
    def prepare_dataset(self, sequences):
        return sequences


class BidExplainedSequenceFeature(SequenceFeature):
    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    @property
    def name(self):
        return "explained"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        explained_vector = [0] * (len(bidding_data.bidding_record) + 1)  # +1 to account for SOS token
        for bid_metadata in bidding_data.bidding_metadata:
            if bid_metadata.explanation:
                explained_vector[bid_metadata.bid_index + 1] = 1
        explained_feature = [
            tf.train.Feature(int64_list=tf.train.Int64List(value=[explained_flag]))
            for explained_flag in explained_vector
        ]
        return tf.train.FeatureList(feature=explained_feature)

    @tf.function
    def prepare_dataset(self, sequences):
        return sequences
