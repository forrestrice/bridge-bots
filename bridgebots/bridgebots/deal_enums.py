from __future__ import annotations

from enum import Enum
from functools import total_ordering

"""
Common bridge concepts such as Cardinal Direction, Suit, and Card Rank represented as Enums
"""


@total_ordering
class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    __from_str_map__ = {"N": NORTH, "E": EAST, "S": SOUTH, "W": WEST}

    @classmethod
    def from_str(cls, direction_str) -> Direction:
        return Direction(cls.__from_str_map__[direction_str.upper()])

    def __lt__(self, other) -> bool:
        return self.value < other.value

    def __repr__(self) -> str:
        return self.name

    def next(self) -> Direction:
        return Direction((self.value + 1) % 4)


@total_ordering
class Suit(Enum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    __from_str_map__ = {"S": SPADES, "H": HEARTS, "D": DIAMONDS, "C": CLUBS}

    @classmethod
    def from_str(cls, suit_str: str) -> Suit:
        return Suit(cls.__from_str_map__[suit_str.upper()])

    def __lt__(self, other) -> bool:
        return self.value < other.value

    def __repr__(self) -> str:
        return self.name


@total_ordering
class BiddingSuit(Enum):
    CLUBS = 0, Suit.CLUBS
    DIAMONDS = 1, Suit.DIAMONDS
    HEARTS = 2, Suit.HEARTS
    SPADES = 3, Suit.SPADES
    NO_TRUMP = 4, None

    __from_str_map__ = {"S": SPADES, "H": HEARTS, "D": DIAMONDS, "C": CLUBS, "N": NO_TRUMP, "NT": NO_TRUMP}

    def __lt__(self, other) -> bool:
        return self.value < other.value

    def __repr__(self) -> str:
        return self.name

    def to_suit(self) -> Suit:
        return self.value[1]

    @classmethod
    def from_str(cls, bidding_suit_str: str) -> BiddingSuit:
        return BiddingSuit(cls.__from_str_map__[bidding_suit_str.upper()])


@total_ordering
class Rank(Enum):
    TWO = 2, "2"
    THREE = 3, "3"
    FOUR = 4, "4"
    FIVE = 5, "5"
    SIX = 6, "6"
    SEVEN = 7, "7"
    EIGHT = 8, "8"
    NINE = 9, "9"
    TEN = 10, "T"
    JACK = 11, "J"
    QUEEN = 12, "Q"
    KING = 13, "K"
    ACE = 14, "A"

    __from_str_map__ = {
        "2": TWO,
        "3": THREE,
        "4": FOUR,
        "5": FIVE,
        "6": SIX,
        "7": SEVEN,
        "8": EIGHT,
        "9": NINE,
        "10": TEN,
        "T": TEN,
        "J": JACK,
        "Q": QUEEN,
        "K": KING,
        "A": ACE,
    }

    @classmethod
    def from_str(cls, rank_str: str) -> Rank:
        return Rank(cls.__from_str_map__[rank_str.upper()])

    def __lt__(self, other) -> bool:
        return self.value < other.value

    def __repr__(self) -> str:
        return self.name

    def to_char(self) -> str:
        return self.value[1]
