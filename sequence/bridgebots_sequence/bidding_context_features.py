from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import tensorflow as tf

from bridgebots import Deal
from bridgebots.deal_utils import calculate_shape, count_hcp


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
    @abstractmethod
    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
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

    @tf.function
    def prepare_dataset(self, contexts, sequences, batch_size, time_steps):
        pass

    # Currently, features do not have any internal state - they are just collections of functions, so we can compare
    # equality and hash by class
    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class TargetHcp(ContextFeature):
    def shape(self):
        return 4

    def schema(self):
        return tf.io.FixedLenFeature([4], dtype=tf.int64)

    @property
    def name(self):
        return "target_hcp"

    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        dealer = context_data.deal.dealer
        hcps = [count_hcp(context_data.deal.hands[dealer.offset(i)].cards) for i in range(4)]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=hcps))

    @tf.function
    def prepare_dataset(self, contexts, sequences, batch_size, time_steps):
        target = contexts[self.name]
        sequence_targets = tf.reshape(
            tf.repeat(target, repeats=time_steps, axis=0), shape=[batch_size, time_steps, self.shape()]
        )
        sequences = sequences.copy()
        sequences["sequence_" + self.name] = sequence_targets
        return contexts, sequences


class Vulnerability(ContextFeature):
    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        return tf.train.Feature(
            int64_list=tf.train.Int64List(value=[context_data.dealer_vulnerable, context_data.dealer_opp_vulnerable])
        )

    @property
    def name(self):
        return "vulnerability"

    def schema(self):
        return tf.io.FixedLenFeature([2], dtype=tf.int64)

    def shape(self):
        return 2

    @tf.function
    def prepare_dataset(self, contexts, sequences, batch_size, time_steps):
        feature = contexts[self.name]
        sequence_feature = tf.reshape(
            tf.repeat(feature, repeats=time_steps, axis=0), shape=[batch_size, time_steps, self.shape()]
        )
        sequences = sequences.copy()
        sequences["sequence_" + self.name] = sequence_feature
        sequences[self.name] = feature
        return contexts, sequences


class TargetShape(ContextFeature):
    def shape(self):
        return 16

    def schema(self):
        return tf.io.FixedLenFeature([16], dtype=tf.int64)

    @property
    def name(self):
        return "target_shape"

    def calculate(self, context_data: BiddingContextExampleData) -> tf.train.Feature:
        dealer = context_data.deal.dealer
        shapes = [calculate_shape(context_data.deal.hands[dealer.offset(i)].cards) for i in range(4)]
        shape_feature = [s for shape in shapes for s in shape]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=shape_feature))

    @tf.function
    def prepare_dataset(self, contexts, sequences, batch_size, time_steps):
        target = contexts[self.name]
        sequence_targets = tf.reshape(
            tf.repeat(target, repeats=time_steps, axis=0), shape=[batch_size, time_steps, self.shape()]
        )
        sequences = sequences.copy()
        sequences["sequence_" + self.name] = sequence_targets
        return contexts, sequences
