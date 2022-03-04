from typing import List

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
