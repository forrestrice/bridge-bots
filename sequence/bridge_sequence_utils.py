from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import tensorflow as tf
from numpy.typing import ArrayLike

from bridgebots import BoardRecord, Card, DealRecord, Direction, Rank, Suit
from bridgebots.bids import LEGAL_BIDS
from bridgebots.deal_utils import count_hcp

BIDDING_VOCAB = {bid: index + 1 for index, bid in enumerate(LEGAL_BIDS)}
# BIDDING_VOCAB["EOS"] = len(BIDDING_VOCAB)
BIDDING_VOCAB["PAD"] = 0
BIDDING_VOCAB_SIZE = len(BIDDING_VOCAB)

SORTED_CARDS = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)
SORTED_CARD_INDEX = {card: index for index, card in enumerate(SORTED_CARDS)}
MAX_BIDDING_SEQUENCE = 35  # 0.01% of boards in the vugraph project have a length longer than 35


@dataclass
class BiddingExampleData:
    direction: Direction
    bidding_sequence: List[str]
    deal_record: DealRecord
    board_record: BoardRecord
    holdings: Dict[Direction, ArrayLike]


@dataclass
class BiddingSequenceExampleData:
    deal_record: DealRecord
    board_record: BoardRecord
    holdings: Dict[Direction, ArrayLike]


# Taken from the documentation
# The following functions can be used to convert a value to a type compatible
# with tf.Example.


def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _float_feature(value):
    """Returns a float_list from a float / double."""
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))


def _int64_feature(value):
    """Returns an int64_list from a bool / enum / int / uint."""
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def numpy_holding(direction: Direction, deal_record: DealRecord) -> ArrayLike:
    bit_holding = np.zeros(52)
    card_indices = [SORTED_CARD_INDEX[c] for c in deal_record.deal.hands[direction].cards]
    bit_holding.put(card_indices, 1)
    return bit_holding


def holding(direction: Direction, deal_record: DealRecord) -> List:
    bit_holding = [0] * 52
    for card in deal_record.deal.hands[direction].cards:
        bit_holding[SORTED_CARD_INDEX[card]] = 1
    return bit_holding


class DealTarget(ABC):
    @abstractmethod
    def shape(self):
        pass

    @abstractmethod
    def calculate(self, deal_record: DealRecord):
        pass


class SpadesDealTarget(DealTarget):
    """The number of spades held by each player starting with the dealer"""

    def shape(self):
        return 4

    def calculate(self, deal_record: DealRecord):
        dealer = deal_record.deal.dealer
        return np.array([len(deal_record.deal.hands[dealer.offset(i)].suits[Suit.SPADES]) for i in range(4)])


class HcpDealTarget(DealTarget):
    """The number of high card points held by each player starting with the dealer"""

    def shape(self):
        return 4

    def calculate(self, deal_record: DealRecord):
        dealer = deal_record.deal.dealer
        return np.array([count_hcp(deal_record.deal.hands[dealer.offset(i)].cards) for i in range(4)])


class DealFeature(ABC):
    @abstractmethod
    def shape(self):
        pass

    @abstractmethod
    def calculate(self, deal_record: DealRecord, direction: Direction):
        pass


class PlayerPositionFeature(DealFeature):
    def shape(self):
        return 4

    def calculate(self, deal_record: DealRecord, direction: Direction):
        offset = (direction.value - deal_record.deal.dealer.value) % 4  # python modulo is always non-negative
        return tf.keras.utils.to_categorical(offset, num_classes=4)


class PlayerPosition:
    def calculate(self, bidding_data: BiddingExampleData) -> tf.train.Feature:
        return _int64_feature((bidding_data.direction.value - bidding_data.deal_record.deal.dealer.value) % 4)

    def schema(self):
        return tf.io.FixedLenFeature([], dtype=tf.int64)


class BiddingIndices:
    def calculate(self, bidding_data: BiddingExampleData) -> tf.train.Feature:
        bidding_indices = [BIDDING_VOCAB[bid] for bid in bidding_data.bidding_sequence]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=bidding_indices))

    def schema(self):
        return tf.io.VarLenFeature(dtype=tf.int64)


class Holding:
    def calculate(self, bidding_data: BiddingExampleData) -> tf.train.Feature:
        holding = bidding_data.holdings[bidding_data.direction]
        print(holding)
        return tf.train.Feature(int64_list=tf.train.Int64List(value=holding))

    def schema(self):
        return tf.io.FixedLenFeature([52], dtype=tf.int64)


class HcpTarget:
    def calculate(self, deal_record: DealRecord) -> tf.train.Feature:
        dealer = deal_record.deal.dealer
        hcps = [count_hcp(deal_record.deal.hands[dealer.offset(i)].cards) for i in range(4)]
        return tf.train.Feature(int64_list=tf.train.Int64List(value=hcps))

    def schema(self):
        # TODO should this really be int64?
        return tf.io.FixedLenFeature([4], dtype=tf.int64)


class HoldingSequence:
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        dealer = bidding_data.deal_record.deal.dealer
        sequence_feature = []
        for i, bid in enumerate(bidding_data.board_record.bidding_record):
            player = dealer.offset(i)
            holding = bidding_data.holdings[player]
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=holding))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)


class BiddingIndicesSequence:
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for bid in bidding_data.board_record.bidding_record:
            bid_index = BIDDING_VOCAB[bid]
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=[bid_index]))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)


class PlayerPositionSequence:
    def calculate(self, bidding_data: BiddingSequenceExampleData) -> tf.train.FeatureList:
        sequence_feature = []
        for i in range(len(bidding_data.board_record.bidding_record)):
            feature = tf.train.Feature(int64_list=tf.train.Int64List(value=[i%4]))
            sequence_feature.append(feature)
        return tf.train.FeatureList(feature=sequence_feature)