from abc import ABC, abstractmethod

import tensorflow as tf

from bridgebots import DealRecord
from bridgebots.deal_utils import count_hcp


class ContextFeature(ABC):
    @abstractmethod
    def calculate(self, deal_record: DealRecord) -> tf.train.Feature:
        raise NotImplementedError

    @abstractmethod
    def name(self):
        raise NotImplementedError

    @abstractmethod
    def schema(self):
        raise NotImplementedError

    @abstractmethod
    def shape(self):
        raise NotImplementedError


class TargetHcp(ContextFeature):
    def shape(self):
        return 4

    def schema(self):
        return tf.io.FixedLenFeature([4], dtype=tf.int64)

    def name(self):
        return "target_hcp"

    def calculate(self, deal_record: DealRecord) -> tf.train.Feature:
        dealer = deal_record.deal.dealer
        hcps = [count_hcp(deal_record.deal.hands[dealer.offset(i)].cards) for i in range(4)]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=hcps))
