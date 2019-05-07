from functools import total_ordering
from typing import List, Dict
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
        for suit, ranks in self.suits.items():
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    @classmethod
    def from_string_lists(cls, clubs: List[str], diamonds: List[str], hearts: List[str], spades: List[str]):
        suits = {
            Suit.CLUBS: sorted([Rank.from_str(card_str) for card_str in clubs]),
            Suit.DIAMONDS: sorted([Rank.from_str(card_str) for card_str in diamonds]),
            Suit.HEARTS: sorted([Rank.from_str(card_str) for card_str in hearts]),
            Suit.SPADES: sorted([Rank.from_str(card_str) for card_str in spades]),
        }
        return PlayerHand(suits)

    def __str__(self):
        return "Clubs:{}\nDiamonds:{}\nHearts:{}\nSpades:{}".format(
            self.suits[Suit.CLUBS],
            self.suits[Suit.DIAMONDS],
            self.suits[Suit.HEARTS],
            self.suits[Suit.SPADES])


class Deal:
    def __init__(self, dealer: Direction, ns_vulnerable: bool, ew_vulnerable: bool, north_hand: PlayerHand,
                 south_hand: PlayerHand, east_hand: PlayerHand, west_hand: PlayerHand):
        self.dealer = dealer
        self.ns_vulnerable = ns_vulnerable
        self.ew_vulnerable = ew_vulnerable
        self.hands = {Direction.NORTH: north_hand,
                      Direction.SOUTH: south_hand,
                      Direction.EAST: east_hand,
                      Direction.WEST: west_hand}
        self.player_cards = {direction: self.hands[direction].cards for direction in self.hands}

    def __str__(self):
        header = "{} Deals\nns_vuln:{}\new_vuln:{}\n".format(self.dealer, self.ns_vulnerable, self.ew_vulnerable)
        hands = "North:\n{}\nEast:\n{}\nSouth:\n{}\nWest:\n{}".format(
            self.hands[Direction.NORTH],
            self.hands[Direction.EAST],
            self.hands[Direction.SOUTH],
            self.hands[Direction.WEST])
        return header + hands
