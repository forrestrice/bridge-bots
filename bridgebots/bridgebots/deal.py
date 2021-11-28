from __future__ import annotations

from functools import total_ordering
from typing import Dict, Iterable, List

from bridgebots.deal_enums import Direction, Rank, Suit

"""
Classes to represent each component of a bridge deal
"""


@total_ordering
class Card:
    """
    A single card in a hand or deal of bridge
    """

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __eq__(self, other) -> bool:
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def __lt__(self, other) -> bool:
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __str__(self) -> bool:
        return self.suit.name[0] + self.rank.value[1]

    def __repr__(self) -> str:
        return self.suit.name[0] + self.rank.value[1]

    @classmethod
    def from_str(cls, card_str) -> Card:
        return Card(Suit.from_str(card_str[0]), Rank.from_str(card_str[1]))


class PlayerHand:
    """
    A single player's 13 cards in a bridge deal
    """

    def __init__(self, suits: Dict[Suit, List[Rank]]):
        self.suits = suits
        assert 13 == sum([len(ranks) for suit, ranks in self.suits.items()])
        self.cards = []
        for suit in reversed(Suit):
            for rank in self.suits[suit]:
                self.cards.append(Card(suit, rank))

    @staticmethod
    def from_string_lists(spades: List[str], hearts: List[str], diamonds: List[str], clubs: List[str]) -> PlayerHand:
        """
        Build a PlayerHand out of Lists of Strings which map to Ranks for each suit. e.g. ['A', 'T', '3'] to represent
        a suit holding of Ace, Ten, Three
        :return: PlayerHand representing the holdings provided by the arguments
        """
        suits = {
            Suit.SPADES: sorted([Rank.from_str(card_str) for card_str in spades], reverse=True),
            Suit.HEARTS: sorted([Rank.from_str(card_str) for card_str in hearts], reverse=True),
            Suit.DIAMONDS: sorted([Rank.from_str(card_str) for card_str in diamonds], reverse=True),
            Suit.CLUBS: sorted([Rank.from_str(card_str) for card_str in clubs], reverse=True),
        }
        return PlayerHand(suits)

    @staticmethod
    def from_cards(cards: Iterable[Card]) -> PlayerHand:
        suits = {
            Suit.CLUBS: sorted([card.rank for card in cards if card.suit == Suit.CLUBS], reverse=True),
            Suit.DIAMONDS: sorted([card.rank for card in cards if card.suit == Suit.DIAMONDS], reverse=True),
            Suit.HEARTS: sorted([card.rank for card in cards if card.suit == Suit.HEARTS], reverse=True),
            Suit.SPADES: sorted([card.rank for card in cards if card.suit == Suit.SPADES], reverse=True),
        }
        return PlayerHand(suits)

    def __repr__(self):
        suit_arrays = [[], [], [], []]
        for card in self.cards:
            suit_arrays[card.suit.value].append(repr(card))
        repr_str = " | ".join(" ".join(suit) for suit in reversed(suit_arrays))
        return f"PlayerHand({repr_str})"

    def __eq__(self, other) -> bool:
        return self.suits == other.suits

    def __hash__(self) -> int:
        return hash(set(self.cards))


class Deal:
    """
    A bridge deal consists of the dealer, the vulnerability of the teams, and the hands
    """

    def __init__(self, dealer: Direction, ns_vulnerable: bool, ew_vulnerable: bool, hands: Dict[Direction, PlayerHand]):
        self.dealer = dealer
        self.ns_vulnerable = ns_vulnerable
        self.ew_vulnerable = ew_vulnerable
        self.hands = hands
        self.player_cards = {direction: self.hands[direction].cards for direction in self.hands}

    def __repr__(self):
        return (
            f"Deal(\n"
            f"\tdealer={self.dealer}, ns_vulnerable={self.ns_vulnerable}, ew_vulnerable={self.ew_vulnerable}\n"
            f"\tNorth: {self.hands[Direction.NORTH]}\n"
            f"\tSouth: {self.hands[Direction.SOUTH]}\n"
            f"\tEast: {self.hands[Direction.EAST]}\n"
            f"\tWest: {self.hands[Direction.WEST]}\n"
            f")"
        )

    def __eq__(self, other) -> bool:
        return (
            self.dealer == other.dealer
            and self.ns_vulnerable == other.ns_vulnerable
            and self.ew_vulnerable == other.ew_vulnerable
            and self.hands == other.hands
        )

    def __hash__(self) -> int:
        card_sets = [(direction, frozenset(self.hands[direction].cards)) for direction in self.hands]
        return hash((self.dealer, self.ns_vulnerable, self.ew_vulnerable, frozenset(card_sets)))

    @staticmethod
    def from_cards(
        dealer: Direction, ns_vulnerable: bool, ew_vulnerable: bool, player_cards: Dict[Direction, List[Card]]
    ) -> Deal:
        hands = {direction: PlayerHand.from_cards(cards) for direction, cards in player_cards.items()}
        return Deal(dealer, ns_vulnerable, ew_vulnerable, hands)

    def is_vulnerable(self, direction: Direction):
        return self.ns_vulnerable if direction in [Direction.NORTH, Direction.SOUTH] else self.ew_vulnerable
