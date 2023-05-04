from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple

import tensorflow as tf

from bridgebots import BidMetadata, Direction
from bridgebots_sequence.feature_utils import BIDDING_VOCAB, BIDDING_VOCAB_SIZE, TARGET_BIDDING_VOCAB
from bridgebots_sequence.interpreter import (
    BiddingLogitsModelInterpreter,
    BiddingPredictionModelInterpreter,
    ModelInterpreterMixin,
)


@dataclass
class BiddingSequenceExampleData:
    dealer: Direction
    bidding_record: List[str]
    bidding_metadata: List[BidMetadata]
    holdings: Dict[Direction, List[int]]


class SequenceFeature(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def prepared_name(self) -> str:
        return self.name

    @property
    @abstractmethod
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        pass

    @abstractmethod
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        pass

    @abstractmethod
    @tf.function
    def prepare_dataset(self, sequences: dict) -> dict:
        pass

    # Currently, features do not have any internal state - they are just collections of functions, so we can compare
    # equality and hash by class
    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class HoldingSequenceFeature(SequenceFeature):
    @property
    def name(self):
        return "holding"

    @property
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        return tf.io.FixedLenSequenceFeature([52], dtype=tf.int64)

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


class BidAlertedSequenceFeature(SequenceFeature):
    @property
    def name(self) -> str:
        return "alerted"

    @property
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

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
    def prepare_dataset(self, sequences: dict) -> dict:
        return sequences


class BidExplainedSequenceFeature(SequenceFeature):
    @property
    def name(self) -> str:
        return "explained"

    @property
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

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
    def prepare_dataset(self, sequences: dict) -> dict:
        return sequences


class CategoricalSequenceFeature(SequenceFeature, ABC):
    @property
    @abstractmethod
    def num_tokens(self) -> int:
        pass

    @property
    def prepared_name(self) -> str:
        return "one_hot_" + self.name


class PlayerPositionSequenceFeature(CategoricalSequenceFeature):
    @property
    def name(self) -> str:
        return "player_position"

    @property
    def num_tokens(self) -> int:
        return 4

    @property
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for i in range(len(bidding_data.bidding_record) + 1):  # +1 to account for SOS token
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=[i % 4]))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)

    @tf.function
    def prepare_dataset(self, sequences: dict) -> dict:
        sequences = sequences.copy()
        sequences["one_hot_player_position"] = tf.one_hot(
            tf.squeeze(sequences[self.name], axis=2), depth=self.num_tokens
        )
        return sequences


class StringCategoricalSequenceFeature(CategoricalSequenceFeature, ABC):
    @property
    def vectorized_name(self) -> str:
        return "vectorized_" + self.name

    @tf.function
    def vectorize(self, context: dict, sequence: dict) -> Tuple[dict, dict]:
        sequence_copy = sequence.copy()
        sequence_copy[self.vectorized_name] = self._vectorize(sequence[self.name])
        return context, sequence_copy

    @abstractmethod
    def _vectorize(self, string_feature: tf.Tensor) -> tf.Tensor:
        pass


class BiddingSequenceFeature(StringCategoricalSequenceFeature):
    bid_vectorization_layer = tf.keras.layers.StringLookup(num_oov_indices=1, vocabulary=BIDDING_VOCAB)

    @property
    def name(self) -> str:
        return "bidding"

    @property
    def num_tokens(self) -> int:
        return BIDDING_VOCAB_SIZE

    @property
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    def _vectorize(self, string_feature: tf.Tensor) -> tf.Tensor:
        return self.bid_vectorization_layer(string_feature)

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_with_sos = ["SOS"] + bidding_data.bidding_record
        bidding_feature = [
            tf.train.Feature(bytes_list=tf.train.BytesList(value=[str.encode(bid)])) for bid in bidding_with_sos
        ]
        return tf.train.FeatureList(feature=bidding_feature)

    @tf.function
    def prepare_dataset(self, sequences: dict) -> dict:
        sequences = sequences.copy()
        sequences["bidding_mask"] = tf.not_equal(tf.squeeze(sequences[self.vectorized_name], axis=2), 0)
        sequences["one_hot_bidding"] = tf.one_hot(
            tf.squeeze(sequences[self.vectorized_name], axis=2), BIDDING_VOCAB_SIZE, dtype=tf.int64
        )
        return sequences


class TargetBiddingSequence(StringCategoricalSequenceFeature, ModelInterpreterMixin):
    bid_vectorization_layer = tf.keras.layers.StringLookup(num_oov_indices=1, vocabulary=TARGET_BIDDING_VOCAB)
    interpreter = BiddingPredictionModelInterpreter()
    logits_interpreter = BiddingLogitsModelInterpreter()

    @property
    def name(self) -> str:
        return "target_bidding"

    @property
    def num_tokens(self) -> int:
        return BIDDING_VOCAB_SIZE

    @property
    def schema(self) -> tf.io.FixedLenSequenceFeature:
        return tf.io.FixedLenSequenceFeature([1], dtype=tf.string)

    def _vectorize(self, string_feature: tf.Tensor) -> tf.Tensor:
        return self.bid_vectorization_layer(string_feature)

    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        bidding_with_eos = bidding_data.bidding_record + ["EOS"]
        bidding_feature = [
            tf.train.Feature(bytes_list=tf.train.BytesList(value=[str.encode(bid)])) for bid in bidding_with_eos
        ]
        return tf.train.FeatureList(feature=bidding_feature)

    @tf.function
    def prepare_dataset(self, sequences: dict) -> dict:
        sequences = sequences.copy()
        sequences["one_hot_target_bidding"] = tf.one_hot(
            tf.squeeze(sequences[self.vectorized_name], axis=2), BIDDING_VOCAB_SIZE, dtype=tf.int64
        )
        return sequences
