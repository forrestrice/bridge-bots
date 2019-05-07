# A compressed representation of a bridge deal
from collections import defaultdict

from deal.deal import Deal, Card, PlayerHand
from deal.deal_enums import Direction, Rank, Suit
from typing import List, Tuple

reverse_sorted_cards = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)


def serialize(deal: Deal) -> bytes:
    card_tuples: List[Tuple[Card, Direction]] = []
    for direction, cards in deal.player_cards.items():
        for card in cards:
            card_tuples.append((card, direction))

    sorted_tuples = sorted(card_tuples, key=lambda ct: ct[0])
    binary_deal = 0
    for card, direction in sorted_tuples:
        binary_deal = (binary_deal << 2) | direction.value
    binary_deal = (binary_deal << 2) | deal.dealer.value
    binary_deal = (binary_deal << 1) | deal.ns_vulnerable
    binary_deal = (binary_deal << 1) | deal.ew_vulnerable
    return binary_deal.to_bytes(14, byteorder='big')


def deserialize(binary_deal_bytes: bytes) -> Deal:
    binary_deal = int.from_bytes(binary_deal_bytes, byteorder='big')
    ew_vulnerable = bool(binary_deal & 1)
    ns_vulnerable = bool(binary_deal & 2)
    binary_deal = binary_deal >> 2
    dealer = Direction(binary_deal & 3)
    binary_deal = binary_deal >> 2
    hands = defaultdict(lambda: defaultdict(list))
    for card in reverse_sorted_cards:
        card_direction = Direction(binary_deal & 3)
        hands[card_direction][card.suit].insert(0, card.rank)
        binary_deal = binary_deal >> 2

    north_hand = PlayerHand(hands[Direction.NORTH])
    south_hand = PlayerHand(hands[Direction.SOUTH])
    east_hand = PlayerHand(hands[Direction.EAST])
    west_hand = PlayerHand(hands[Direction.WEST])
    return Deal(dealer, ns_vulnerable, ew_vulnerable, north_hand, south_hand, east_hand, west_hand)
