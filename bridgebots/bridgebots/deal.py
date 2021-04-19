from __future__ import annotations

from functools import total_ordering
from typing import Dict, List

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

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.suit, self.rank))

    def __lt__(self, other):
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __str__(self):
        return self.suit.name[0] + self.rank.value[1]

    def __repr__(self):
        return f"Card({self.suit!r},{self.rank!r})"

    @classmethod
    def from_str(cls, card_str):
        return Card(Suit.from_str(card_str[0]), Rank.from_str(card_str[1]))


class PlayerHand:
    """
    A single player's 13 cards in a bridge deal
    """

    def __init__(self, suits: Dict[Suit, List[Rank]]):
        self.suits = suits
        assert 13 == sum([len(ranks) for suit, ranks in self.suits.items()])
        self.cards = []
        for suit in Suit:
            for rank in self.suits[suit]:
                self.cards.append(Card(suit, rank))

    @staticmethod
    def from_string_lists(clubs: List[str], diamonds: List[str], hearts: List[str], spades: List[str]):
        """
        Build a PlayerHand out of Lists of Strings which map to Ranks for each suit. e.g. ['A', 'T', '3'] to represent
        a suit holding of Ace, Ten, Three
        :return: PlayerHand representing the holdings provided by the arguments
        """
        suits = {
            Suit.CLUBS: sorted([Rank.from_str(card_str) for card_str in clubs], reverse=True),
            Suit.DIAMONDS: sorted([Rank.from_str(card_str) for card_str in diamonds], reverse=True),
            Suit.HEARTS: sorted([Rank.from_str(card_str) for card_str in hearts], reverse=True),
            Suit.SPADES: sorted([Rank.from_str(card_str) for card_str in spades], reverse=True),
        }
        return PlayerHand(suits)

    def __str__(self):
        return "Clubs:{}\nDiamonds:{}\nHearts:{}\nSpades:{}".format(
            self.suits[Suit.CLUBS], self.suits[Suit.DIAMONDS], self.suits[Suit.HEARTS], self.suits[Suit.SPADES]
        )

    def __eq__(self, other):
        return self.suits == other.suits

    def __hash__(self):
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

    def __str__(self):
        header = "{} Deals\nns_vuln:{}\new_vuln:{}\n".format(self.dealer, self.ns_vulnerable, self.ew_vulnerable)
        hands_str = "North:\n{}\nEast:\n{}\nSouth:\n{}\nWest:\n{}".format(
            self.hands[Direction.NORTH],
            self.hands[Direction.EAST],
            self.hands[Direction.SOUTH],
            self.hands[Direction.WEST],
        )
        return header + hands_str

    def __eq__(self, other):
        return (
            self.dealer == other.dealer
            and self.ns_vulnerable == other.ns_vulnerable
            and self.ew_vulnerable == other.ew_vulnerable
            and self.hands == other.hands
        )

    def __hash__(self):
        card_sets = [(direction, frozenset(self.hands[direction].cards)) for direction in self.hands]
        return hash((self.dealer, self.ns_vulnerable, self.ew_vulnerable, frozenset(card_sets)))
