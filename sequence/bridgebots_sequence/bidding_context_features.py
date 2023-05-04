from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple

import tensorflow as tf

from bridgebots import Deal
from bridgebots.deal_utils import calculate_shape, count_hcp
from bridgebots_sequence.interpreter import HcpModelInterpreter, ModelInterpreterMixin, ShapeModelInterpreter


@dataclass
class BiddingContextExampleData:
    dealer_vulnerable: bool
    dealer_opp_vulnerable: bool
    deal: Optional[Deal]  # Only present when creating training data

    @staticmethod
    def from_deal(deal: Deal) -> BiddingContextExampleData:
        dealer_vuln = deal.is_vulnerable(deal.dealer)
        dealer_opp_vuln = deal.is_vulnerable(deal.dealer.next())
        return BiddingContextExampleData(dealer_vuln, dealer_opp_vuln, deal)


class ContextFeature(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def schema(self) -> tf.io.FixedLenFeature:
        pass

    @property
    @abstractmethod
    def shape(self) -> int:
        pass

    @property
    def sequence_name(self) -> str:
        return "sequence_" + self.name

    @abstractmethod
    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        pass

    @tf.function
    @abstractmethod
    def prepare_dataset(self, contexts: dict, sequences: dict, batch_size: int, time_steps: int) -> Tuple[dict, dict]:
        pass

    # Currently, features do not have any internal state - they are just collections of functions, so we can compare
    # equality and hash by class
    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class TargetHcp(ContextFeature):
    interpreter = HcpModelInterpreter()

    @property
    def name(self) -> str:
        return "target_hcp"

    @property
    def schema(self) -> tf.io.FixedLenFeature:
        return tf.io.FixedLenFeature([4], dtype=tf.int64)

    @property
    def shape(self) -> int:
        return 4

    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        dealer = context_data.deal.dealer
        hcps = [count_hcp(context_data.deal.hands[dealer.offset(i)].cards) for i in range(4)]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=hcps))

    @tf.function
    def prepare_dataset(self, contexts: dict, sequences: dict, batch_size: int, time_steps: int) -> Tuple[dict, dict]:
        target = contexts[self.name]
        sequence_targets = tf.reshape(
            tf.repeat(target, repeats=time_steps, axis=0), shape=[batch_size, time_steps, self.shape]
        )
        sequences = sequences.copy()
        sequences[self.sequence_name] = sequence_targets
        return contexts, sequences


class Vulnerability(ContextFeature):
    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        return tf.train.Feature(
            int64_list=tf.train.Int64List(value=[context_data.dealer_vulnerable, context_data.dealer_opp_vulnerable])
        )

    @property
    def name(self) -> str:
        return "vulnerability"

    @property
    def schema(self) -> tf.io.FixedLenFeature:
        return tf.io.FixedLenFeature([2], dtype=tf.int64)

    @property
    def shape(self) -> int:
        return 2

    @tf.function
    def prepare_dataset(self, contexts: dict, sequences: dict, batch_size: int, time_steps: int) -> Tuple[dict, dict]:
        feature = contexts[self.name]
        sequence_feature = tf.reshape(
            tf.repeat(feature, repeats=time_steps, axis=0), shape=[batch_size, time_steps, self.shape]
        )
        sequences = sequences.copy()
        sequences[self.sequence_name] = sequence_feature
        sequences[self.name] = feature
        return contexts, sequences


class TargetShape(ContextFeature, ModelInterpreterMixin):
    interpreter = ShapeModelInterpreter()

    @property
    def name(self) -> str:
        return "target_shape"

    @property
    def schema(self) -> tf.io.FixedLenFeature:
        return tf.io.FixedLenFeature([16], dtype=tf.int64)

    @property
    def shape(self) -> int:
        return 16

    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        dealer = context_data.deal.dealer
        shapes = [calculate_shape(context_data.deal.hands[dealer.offset(i)].cards) for i in range(4)]
        shape_feature = [s for shape in shapes for s in shape]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=shape_feature))

    @tf.function
    def prepare_dataset(self, contexts: dict, sequences: dict, batch_size: int, time_steps: int) -> Tuple[dict, dict]:
        target = contexts[self.name]
        sequence_targets = tf.reshape(
            tf.repeat(target, repeats=time_steps, axis=0), shape=[batch_size, time_steps, self.shape]
        )
        sequences = sequences.copy()
        sequences[self.sequence_name] = sequence_targets
        return contexts, sequences
