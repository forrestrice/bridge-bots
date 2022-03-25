from abc import ABC, abstractmethod
from typing import List

import tensorflow as tf

from bridgebots import Card, DealRecord, Direction, Rank, Suit
from bridgebots.bids import LEGAL_BIDS

SORTED_CARDS = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)
SORTED_CARD_INDEX = {card: index for index, card in enumerate(SORTED_CARDS)}
BIDDING_VOCAB = ["SOS"] + LEGAL_BIDS
TARGET_BIDDING_VOCAB = LEGAL_BIDS.copy() + ["EOS"]
BIDDING_VOCAB_SIZE = len(BIDDING_VOCAB) + 1  # +1 for padding


def holding_from_deal(direction: Direction, deal_record: DealRecord) -> List[int]:
    return holding_from_cards(deal_record.deal.hands[direction].cards)


def holding_from_cards(cards: List[Card]) -> List[int]:
    bit_holding = [0] * 52
    for card in cards:
        bit_holding[SORTED_CARD_INDEX[card]] = 1
    return bit_holding


class SampleWeightsCalculator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def input_name(self) -> str:
        pass

    @abstractmethod
    @tf.function
    def prepare_dataset(self, sequences: dict) -> dict:
        pass


class BiddingSampleWeightsCalculator(SampleWeightsCalculator):
    # fmt: off
    bid_weights_gut = [
        ("PASS", 0.5),
        ("1C", 1), ("1D", 1), ("1H", 1), ("1S", 1), ("1NT", 1),
        ("2C", 1.5), ("2D", 1.5), ("2H", 1.5), ("2S", 1.5), ("2NT", 1.5),
        ("3C", 1.75), ("3D", 1.75), ("3H", 1.75), ("3S", 1.75),
        ("3NT", 2),
        ("4C", 2), ("4D", 2), ("4H", 2), ("4S", 2), ("4NT", 2),
        ("5C", 3), ("5D", 3), ("5H", 3), ("5S", 3), ("5NT", 3),
        ("6C", 4), ("6D", 4), ("6H", 4), ("6S", 4), ("6NT", 4),
        ("7C", 5), ("7D", 5), ("7H", 5), ("7S", 5), ("7NT", 5),
        ("X", 1.5), ("XX", 4),
        ("EOS", 0.1),
    ]
    # fmt: on
    # fmt: off
    bid_weights_observed = [
        ("PASS", 1.9),
        ("1C", 50), ("1D", 50), ("1H", 40), ("1S", 40), ("1NT", 40),
        ("2C", 50), ("2D", 50), ("2H", 50), ("2S", 50), ("2NT", 50),
        ("3C", 70), ("3D", 70), ("3H", 70), ("3S", 70),
        ("3NT", 50),
        ("4C", 175), ("4D", 175), ("4H", 65), ("4S", 65),
        ("4NT", 250),
        ("5C", 250), ("5D", 250),
        ("5H", 350), ("5S", 550),
        ("5NT", 1500),
        ("6C", 800), ("6D", 800), ("6H", 800), ("6S", 800), ("6NT", 1900),
        ("7C", 7000), ("7D", 7000), ("7H", 7000), ("7S", 7000), ("7NT", 7000),
        ("X", 30), ("XX", 450),
        ("EOS", 0.1),
    ]
    # fmt: on

    bid_keys = [k for k, v in bid_weights_observed]
    bid_values = [v for k, v in bid_weights_observed]
    init = tf.lookup.KeyValueTensorInitializer(
        keys=tf.constant(bid_keys), values=tf.constant(bid_values, dtype=tf.float64)
    )
    vocab_table = tf.lookup.StaticHashTable(init, default_value=0)

    @property
    def name(self) -> str:
        return "target_bidding_sample_weight"

    @property
    def input_name(self) -> str:
        return "target_bidding"

    @tf.function
    def prepare_dataset(self, sequences: dict) -> dict:
        sequences = sequences.copy()
        sequences[self.name] = tf.squeeze(self.vocab_table.lookup(sequences[self.input_name]), axis=2)
        return sequences
