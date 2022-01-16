from collections import defaultdict
from typing import Dict, List, Tuple

from bridgebots.deal import Card, Deal, PlayerHand
from bridgebots.deal_enums import Direction, Rank, Suit

"""
Utilities for converting bridge data to/from a bridgebots representation
"""
_NS_VULNERABLE_STRINGS = {"Both", "N-S", "All", "NS", "b", "n"}
_EW_VULNERABLE_STRINGS = {"Both", "E-W", "All", "EW", "b", "e"}
_REVERSE_SORTED_CARDS = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)
_LIN_DEALER_TO_DIRECTION = {"1": Direction.SOUTH, "2": Direction.WEST, "3": Direction.NORTH, "4": Direction.EAST}
_HOLDING_SUIT_IDENTIFIERS = ["S", "H", "D", "C"]
_DECK_SET = frozenset({Card(suit, rank) for rank in Rank for suit in Suit})
_RANK_HCP = {Rank.ACE: 4, Rank.KING: 3, Rank.QUEEN: 2, Rank.JACK: 1}


def serialize_deal(deal: Deal) -> bytes:
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


def deserialize_deal(binary_deal_bytes: bytes) -> Deal:
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
    for card in _REVERSE_SORTED_CARDS:
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
        suit_string_lists.reverse()
        player_cards[direction] = PlayerHand.from_string_lists(*suit_string_lists)

    dealer_direction = Direction[acbl_dict["dealer"].upper()]
    vuln_string = acbl_dict["vulnerability"]
    ns_vuln = vuln_string in _NS_VULNERABLE_STRINGS
    ew_vuln = vuln_string in _EW_VULNERABLE_STRINGS
    return Deal(dealer_direction, ns_vuln, ew_vuln, player_cards)


def from_pbn_deal(dealer_str: str, vulnerability_str: str, deal_str: str) -> Deal:
    """
    Convert a PBN deal to a bridgebots Deal
    :param dealer_str: value of the 'Dealer' key in the pbn record
    :param vulnerability_str: value of the 'Vulnerable' key in the pbn record
    :param deal_str: value of the 'Deal' key in the pbn record
    :return: Deal representation of the pbn record
    """
    ns_vulnerable = vulnerability_str in _NS_VULNERABLE_STRINGS
    ew_vulnerable = vulnerability_str in _EW_VULNERABLE_STRINGS

    dealer = Direction.from_str(dealer_str)
    if deal_str is None or deal_str == "":
        raise ValueError(f"Invalid deal_str:{deal_str}")
    hands_direction = Direction.from_str(deal_str[0])
    deal_str = deal_str[2:]
    player_hands = {}
    for player_str in deal_str.split():
        suit_lists = [list(suit) for suit in player_str.split(".")]
        player_hands[hands_direction] = PlayerHand.from_string_lists(*suit_lists)
        hands_direction = hands_direction.next()

    return Deal(dealer, ns_vulnerable, ew_vulnerable, player_hands)


def _parse_lin_holding(holding: str) -> List[List[str]]:
    suit_holdings = []
    holding_index = 0
    for id in _HOLDING_SUIT_IDENTIFIERS:
        suit_holding = []
        while holding_index < len(holding):
            c = holding[holding_index]
            if c == id:
                holding_index += 1
                continue
            if c in _HOLDING_SUIT_IDENTIFIERS:
                break
            suit_holding.append(c)
            holding_index += 1
        suit_holdings.append(suit_holding)
    return suit_holdings


def from_lin_deal(lin_dealer_str: str, vulnerability_str: str, holdings_str: str) -> Deal:
    """
    Convert LIN deal nodes into a bridgebots deal
    :param lin_dealer_str: Numbers map to directions starting with 1=South
    :param vulnerability_str: LIN vulnerability. One of b,o,n,e
    :param holdings_str: Holding like "1S98643HAJT54DCJT4,SQJTH98DKT7542C76,S5HKQ3DJ93CAKQ832,"
    :return: bridgebots deal representation
    """
    dealer = _LIN_DEALER_TO_DIRECTION[lin_dealer_str]
    holdings = holdings_str.strip(",").split(",")
    # Convert a holding string like SA63HJ8642DK53CKJ into a PlayerHand
    players_suit_holdings = [_parse_lin_holding(holding) for holding in holdings]
    player_hands = {}
    current_direction = Direction.SOUTH
    for suit_holdings in players_suit_holdings:
        suit_holdings_lists = [list(suit_holding) for suit_holding in suit_holdings]
        player_hands[current_direction] = PlayerHand.from_string_lists(*suit_holdings_lists)
        current_direction = current_direction.next()

    # Some LIN files only include 3 hands. In that case infer the 4th hand
    if len(player_hands) == 3:
        held_cards = {card for player_hand in player_hands.values() for card in player_hand.cards}
        remaining_cards = _DECK_SET - held_cards
        player_hands[current_direction] = PlayerHand.from_cards(remaining_cards)

    ns_vulnerable = vulnerability_str in _NS_VULNERABLE_STRINGS
    ew_vulnerable = vulnerability_str in _EW_VULNERABLE_STRINGS
    deal = Deal(dealer, ns_vulnerable, ew_vulnerable, player_hands)
    return deal


def count_hcp(cards: List[Card]) -> int:
    """:return Goren High Card Points for a list of cards"""
    return sum((_RANK_HCP.get(c.rank, 0) for c in cards))
