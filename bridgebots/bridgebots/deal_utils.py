from collections import defaultdict
from typing import Dict, List, Tuple

from bridgebots.deal import Card, Deal, PlayerHand
from bridgebots.deal_enums import Direction, Rank, Suit

"""
Utilities for converting bridge data to/from a bridgebots representation
"""
REVERSE_SORTED_CARDS = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)
NS_VULNERABLE_STRINGS = {"Both", "N-S", "All", "NS"}
EW_VULNERABLE_STRINGS = {"Both", "E-W", "All", "EW"}


def serialize(deal: Deal) -> bytes:
    """
    Convert a Deal to a binary representation. Use two bits for each card to represent the Direction which holds that
    card. Two more bits encode the Direction that delt, and two final bits to encode vulnerability.
    :param deal: Deal to serialize
    :return: Compressed byte representation of the deal
    """
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
    return binary_deal.to_bytes(14, byteorder="big")


def deserialize(binary_deal_bytes: bytes) -> Deal:
    """
    Unpack compressed deal data into a Deal object
    :param binary_deal_bytes: compressed byte representation of a deal
    :return: Deal object corresponding to the binary data
    """
    binary_deal = int.from_bytes(binary_deal_bytes, byteorder="big")
    ew_vulnerable = bool(binary_deal & 1)
    ns_vulnerable = bool(binary_deal & 2)
    binary_deal = binary_deal >> 2
    dealer = Direction(binary_deal & 3)
    binary_deal = binary_deal >> 2
    hands = defaultdict(lambda: defaultdict(list))
    for card in REVERSE_SORTED_CARDS:
        card_direction = Direction(binary_deal & 3)
        hands[card_direction][card.suit].append(card.rank)
        binary_deal = binary_deal >> 2

    deal_hands = {
        Direction.NORTH: PlayerHand(hands[Direction.NORTH]),
        Direction.SOUTH: PlayerHand(hands[Direction.SOUTH]),
        Direction.EAST: PlayerHand(hands[Direction.EAST]),
        Direction.WEST: PlayerHand(hands[Direction.WEST]),
    }
    return Deal(dealer, ns_vulnerable, ew_vulnerable, deal_hands)


def from_acbl_dict(acbl_dict: Dict[str, str]) -> Deal:
    """
    The ACBL API returns JSON which can be converted into a Deal object
    :param acbl_dict: dictionary record for a deal from ACBL api JSON data
    :return: Deal representation
    """
    player_cards = {}
    for direction in Direction:
        suit_keys = [direction.name.lower() + "_" + suit.name.lower() for suit in Suit]
        suit_string_lists = [
            [] if acbl_dict[suit_key] == "-----" else acbl_dict[suit_key].split() for suit_key in suit_keys
        ]
        player_cards[direction] = PlayerHand.from_string_lists(*suit_string_lists)

    dealer_direction = Direction[acbl_dict["dealer"].upper()]
    vuln_string = acbl_dict["vulnerability"]
    ns_vuln = vuln_string in NS_VULNERABLE_STRINGS
    ew_vuln = vuln_string in EW_VULNERABLE_STRINGS
    return Deal(dealer_direction, ns_vuln, ew_vuln, player_cards)


def from_pbn_deal(dealer_str: str, vulnerability_str: str, deal_str: str) -> Deal:
    """
    Convert a PBN deal to a bridgebots Deal
    :param dealer_str: value of the 'Dealer' key in the pbn record
    :param vulnerability_str: value of the 'Vulnerable' key in the pbn record
    :param deal_str: value of the 'Deal' key in the pbn record
    :return: Deal representation of the pbn record
    """
    ns_vulnerable = vulnerability_str in NS_VULNERABLE_STRINGS
    ew_vulnerable = vulnerability_str in EW_VULNERABLE_STRINGS

    dealer = Direction.from_str(dealer_str)

    hands_direction = Direction.from_str(dealer_str[0])
    deal_str = deal_str[2:]
    player_hands = {}
    for player_str in deal_str.split():
        suits = player_str.split(".")
        suits.reverse()
        player_hands[hands_direction] = PlayerHand.from_string_lists(*suits)
        hands_direction = hands_direction.next()

    return Deal(dealer, ns_vulnerable, ew_vulnerable, player_hands)
