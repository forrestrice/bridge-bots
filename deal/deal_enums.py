from enum import Enum
from functools import total_ordering


@total_ordering
class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    _ignore_ = ['_char_map']
    _char_map = {}

    @classmethod
    def from_char(self, direction_char):
        return Direction._char_map[direction_char]

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        return self.name

    def next(self):
        return Direction((self.value + 1) % 4)


Direction._char_map = {"N": Direction.NORTH, "E": Direction.EAST, "S": Direction.SOUTH, "W": Direction.WEST}

@total_ordering
class Suit(Enum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        return self.name


@total_ordering
class BiddingSuit(Enum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
    NO_TRUMP = 4

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        return self.name


@total_ordering
class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    # double underscore to end the enum declaration
    __from_str_map__ = {'2': TWO, '3': THREE, '4': FOUR, '5': FIVE, '6': SIX, '7': SEVEN, '8': EIGHT, '9': NINE,
                        '10': TEN, 'T': TEN, 'J': JACK, 'Q': QUEEN, 'K': KING, 'A': ACE}

    @classmethod
    def from_str(cls, str):
        return Rank(cls.__from_str_map__[str])

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        return self.name
