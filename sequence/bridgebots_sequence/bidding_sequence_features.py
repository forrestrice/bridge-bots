from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import tensorflow as tf

from bridgebots import BoardRecord, DealRecord, Direction
from bridgebots_sequence.feature_utils import BIDDING_VOCAB, BIDDING_VOCAB_SIZE, TARGET_BIDDING_VOCAB


@dataclass
class BiddingSequenceExampleData:
    deal_record: DealRecord
    board_record: BoardRecord
    holdings: Dict[Direction, List]


class SequenceFeature(ABC):
    @abstractmethod
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def schema(self):
        pass

    @abstractmethod
    def shape(self):
        pass

    def prepared_name(self):
        return self.name()

    @abstractmethod
    @tf.function
    def prepare_dataset(self, sequences):
        pass


class CategoricalSequenceFeature(SequenceFeature, ABC):
    @abstractmethod
    def num_tokens(self):
        pass

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
        for i in range(len(bidding_data.board_record.bidding_record) + 1):  # +1 to account for SOS token
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
        for i in range(len(bidding_data.board_record.bidding_record) + 1):  # +1 to account for SOS token
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
        standardize=None, vocabulary=BIDDING_VOCAB
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
        bidding_with_sos = ["SOS"] + bidding_data.board_record.bidding_record
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
        sequences["bidding_mask"] = tf.not_equal(tf.squeeze(sequences[self.vectorized_name]), 0)
        sequences["one_hot_bidding"] = tf.one_hot(
            tf.squeeze(sequences[self.vectorized_name]), BIDDING_VOCAB_SIZE, dtype=tf.int64
        )
        return sequences


class TargetBiddingSequence(CategoricalSequenceFeature):
    # Disable standardization - bids have already been standardized by bridgebots
    bid_vectorization_layer = tf.keras.layers.experimental.preprocessing.TextVectorization(
        standardize=None, vocabulary=TARGET_BIDDING_VOCAB
    )

    def num_tokens(self):
        return BIDDING_VOCAB_SIZE

    def shape(self):
        return None

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    @property
    def name(self):
        return "target_bidding"

    @property
    def vectorized_name(self):
        return "target_vectorized_bidding"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_with_eos = bidding_data.board_record.bidding_record + ["EOS"]
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
            tf.squeeze(sequences[self.vectorized_name]), BIDDING_VOCAB_SIZE, dtype=tf.int64
        )
        return sequences


class BidAlertedSequenceFeature(SequenceFeature):
    def shape(self):
        return 1

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    @property
    def name(self):
        return "alerted"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        alerted_vector = [0] * (len(bidding_data.board_record.bidding_record) + 1)  # +1 to account for SOS token
        for bid_metadata in bidding_data.board_record.bidding_metadata:
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
    def shape(self):
        return 1

    def schema(self):
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    @property
    def name(self):
        return "explained"

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        explained_vector = [0] * (len(bidding_data.board_record.bidding_record) + 1)  # +1 to account for SOS token
        for bid_metadata in bidding_data.board_record.bidding_metadata:
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
