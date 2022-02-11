from abc import ABC, abstractmethod

import tensorflow as tf

from bridgebots import DealRecord
from bridgebots.deal_utils import count_hcp


class ContextFeature(ABC):
    @abstractmethod
    def calculate(self, deal_record: DealRecord) -> tf.train.Feature:
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

    @tf.function
    def prepare_dataset(self, contexts, sequences, batch_size, time_steps):
        raise NotImplementedError


class TargetHcp(ContextFeature):
    def shape(self):
        return 4

    def schema(self):
        return tf.io.FixedLenFeature([4], dtype=tf.int64)

    @property
    def name(self):
        return "target_hcp"

    def calculate(self, deal_record: DealRecord) -> tf.train.Feature:
        dealer = deal_record.deal.dealer
        hcps = [count_hcp(deal_record.deal.hands[dealer.offset(i)].cards) for i in range(4)]
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
    def calculate(self, deal_record: DealRecord) -> tf.train.Feature:
        dealer_vuln = deal_record.deal.is_vulnerable(deal_record.deal.dealer)
        dealer_opp_vuln = deal_record.deal.is_vulnerable(deal_record.deal.dealer.next())
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[dealer_vuln, dealer_opp_vuln]))

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

