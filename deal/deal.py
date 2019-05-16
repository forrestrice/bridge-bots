from __future__ import annotations
from collections import defaultdict
from functools import total_ordering
from typing import List, Dict, Tuple
from deal.deal_enums import Suit, Rank, Direction


@total_ordering
class Card:
    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __str__(self):
        return "{0} of {1}".format(self.rank.name, self.suit.name)

    def __repr__(self):
        return f"Card({self.suit!r},{self.rank!r})"


class PlayerHand:
    def __init__(self, suits: Dict[Suit, List[Rank]]):
        self.suits = suits
        assert 13 == sum([len(ranks) for suit, ranks in self.suits.items()])
        self.cards = []
        for suit in Suit:
            for rank in self.suits[suit]:
                self.cards.append(Card(suit, rank))

    @staticmethod
    def from_string_lists(clubs: List[str], diamonds: List[str], hearts: List[str], spades: List[str]):
        suits = {
            Suit.CLUBS: sorted([Rank.from_str(card_str) for card_str in clubs], reverse=True),
            Suit.DIAMONDS: sorted([Rank.from_str(card_str) for card_str in diamonds], reverse=True),
            Suit.HEARTS: sorted([Rank.from_str(card_str) for card_str in hearts], reverse=True),
            Suit.SPADES: sorted([Rank.from_str(card_str) for card_str in spades], reverse=True),
        }
        return PlayerHand(suits)

    def __str__(self):
        return "Clubs:{}\nDiamonds:{}\nHearts:{}\nSpades:{}".format(
            self.suits[Suit.CLUBS],
            self.suits[Suit.DIAMONDS],
            self.suits[Suit.HEARTS],
            self.suits[Suit.SPADES])

    def __eq__(self, other):
        return self.suits == other.suits


reverse_sorted_cards = sorted([Card(suit, rank) for suit in Suit for rank in Rank], reverse=True)


class Deal:

    def __init__(self, dealer: Direction, ns_vulnerable: bool, ew_vulnerable: bool, hands: Dict[Direction, PlayerHand]):
        self.dealer = dealer
        self.ns_vulnerable = ns_vulnerable
        self.ew_vulnerable = ew_vulnerable
        self.hands = hands
        self.player_cards = {direction: self.hands[direction].cards for direction in self.hands}

    def __str__(self):
        header = "{} Deals\nns_vuln:{}\new_vuln:{}\n".format(self.dealer, self.ns_vulnerable, self.ew_vulnerable)
        hands_str = "North:\n{}\nEast:\n{}\nSouth:\n{}\nWest:\n{}".format(
            self.hands[Direction.NORTH],
            self.hands[Direction.EAST],
            self.hands[Direction.SOUTH],
            self.hands[Direction.WEST])
        return header + hands_str

    def __eq__(self, other):
        return (self.dealer == other.dealer and
                self.ns_vulnerable == other.ns_vulnerable and
                self.ew_vulnerable == other.ew_vulnerable and
                self.hands == other.hands)

    def serialize(self) -> bytes:
        card_tuples: List[Tuple[Card, Direction]] = []
        for direction, cards in self.player_cards.items():
            for card in cards:
                card_tuples.append((card, direction))

        sorted_tuples = sorted(card_tuples, key=lambda ct: ct[0])

        binary_deal = 0
        for card, direction in sorted_tuples:
            binary_deal = (binary_deal << 2) | direction.value

        # for some reason pycharm thinks self.dealer.value is a Direction
        # noinspection PyTypeChecker
        binary_deal = (binary_deal << 2) | self.dealer.value
        binary_deal = (binary_deal << 1) | self.ns_vulnerable
        binary_deal = (binary_deal << 1) | self.ew_vulnerable
        return binary_deal.to_bytes(14, byteorder='big')

    @staticmethod
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
            hands[card_direction][card.suit].append(card.rank)
            binary_deal = binary_deal >> 2

        deal_hands = {
            Direction.NORTH: PlayerHand(hands[Direction.NORTH]),
            Direction.SOUTH: PlayerHand(hands[Direction.SOUTH]),
            Direction.EAST: PlayerHand(hands[Direction.EAST]),
            Direction.WEST: PlayerHand(hands[Direction.WEST]),
        }
        return Deal(dealer, ns_vulnerable, ew_vulnerable, deal_hands)
