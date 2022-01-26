from typing import List

from bridgebots import Card, DealRecord, Direction, Rank, Suit
from bridgebots.bids import LEGAL_BIDS

SORTED_CARDS = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)
SORTED_CARD_INDEX = {card: index for index, card in enumerate(SORTED_CARDS)}
BIDDING_VOCAB_SIZE = len(LEGAL_BIDS) + 1  # +1 for padding


def holding(direction: Direction, deal_record: DealRecord) -> List:
    bit_holding = [0] * 52
    for card in deal_record.deal.hands[direction].cards:
        bit_holding[SORTED_CARD_INDEX[card]] = 1
    return bit_holding
