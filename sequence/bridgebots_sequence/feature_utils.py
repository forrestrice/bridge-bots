from abc import ABC, abstractmethod
from typing import List, Tuple

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
    def __init__(self, bid_weights: List[Tuple[str, float]], default_weight: float = 0):
        bid_keys = [k for k, v in bid_weights]
        bid_values = [v for k, v in bid_weights]
        init = tf.lookup.KeyValueTensorInitializer(
            keys=tf.constant(bid_keys), values=tf.constant(bid_values, dtype=tf.float64)
        )
        self.vocab_table = tf.lookup.StaticHashTable(init, default_value=default_weight)

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


class ObservedBiddingSampleWeightsCalculator(BiddingSampleWeightsCalculator):
    # fmt: off
    bid_weights = [
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

    def __init__(self):
        super().__init__(self.bid_weights)


class SimpleBiddingSampleWeightsCalculator(BiddingSampleWeightsCalculator):
    # fmt: off
    bid_weights = [
        ("PASS", 0.25),
        ("1C", 1), ("1D", 1), ("1H", 1), ("1S", 1), ("1NT", 1),
        ("2C", 1.5), ("2D", 1.5), ("2H", 1.5), ("2S", 1.5), ("2NT", 1.5),
        ("3C", 1.75), ("3D", 1.75), ("3H", 1.75), ("3S", 1.75),
        ("3NT", 2),
        ("4C", 2), ("4D", 2), ("4H", 2), ("4S", 2), ("4NT", 2),
        ("5C", 3), ("5D", 3), ("5H", 3), ("5S", 3), ("5NT", 3),
        ("6C", 6), ("6D", 6), ("6H", 6), ("6S", 6), ("6NT", 6),
        ("7C", 10), ("7D", 10), ("7H", 10), ("7S", 10), ("7NT", 10),
        ("X", 1.5), ("XX", 4),
        ("EOS", 0.1),
    ]
    # fmt: on

    def __init__(self):
        super().__init__(self.bid_weights)


class VerySimpleBiddingSampleWeightsCalculator(BiddingSampleWeightsCalculator):
    # fmt: off
    bid_weights = [
        ("PASS", 0.25),
        ("EOS", 0.1),
    ]
    # fmt: on

    def __init__(self):
        super().__init__(self.bid_weights, default_weight=1)


class OnesBiddingSampleWeightsCalculator(BiddingSampleWeightsCalculator):
    # fmt: off
    bid_weights = [
        ("PASS", 1),
        ("1C", 1), ("1D", 1), ("1H", 1), ("1S", 1), ("1NT", 1),
        ("2C", 1), ("2D", 1), ("2H", 1), ("2S", 1), ("2NT", 1),
        ("3C", 1), ("3D", 1), ("3H", 1), ("3S", 1),
        ("3NT", 1),
        ("4C", 1), ("4D", 1), ("4H", 1), ("4S", 1), ("4NT", 1),
        ("5C", 1), ("5D", 1), ("5H", 1), ("5S", 1), ("5NT", 1),
        ("6C", 1), ("6D", 1), ("6H", 1), ("6S", 1), ("6NT", 1),
        ("7C", 1), ("7D", 1), ("7H", 1), ("7S", 1), ("7NT", 1),
        ("X", 1), ("XX", 1),
        ("EOS", 1),
    ]
    # fmt: on

    def __init__(self):
        super().__init__(self.bid_weights, default_weight=1)
