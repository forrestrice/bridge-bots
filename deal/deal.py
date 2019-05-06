from typing import List
from deal.deal_enums import Suit, Rank, Direction


class Card:
    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    def __str__(self):
        return "{} of {}".format(self.rank.name, self.suit.name)


class PlayerHand:
    def __init__(self, clubs: List[str], diamonds: List[str], hearts: List[str], spades: List[str]):

        self.suits = {}
        self.suits[Suit.CLUBS] = sorted([Rank.from_str(card_str) for card_str in clubs])
        self.suits[Suit.DIAMONDS] = sorted([Rank.from_str(card_str) for card_str in diamonds])
        self.suits[Suit.HEARTS] = sorted([Rank.from_str(card_str) for card_str in hearts])
        self.suits[Suit.SPADES] = sorted([Rank.from_str(card_str) for card_str in spades])
        assert 13 == sum([len(ranks) for suit, ranks in self.suits.items()])
        self.cards = []
        for suit, ranks in self.suits.items():
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    def __str__(self):
        return "Clubs:{}\nDiamonds:{}\nHearts:{}\nSpades:{}".format(
            self.suits[Suit.CLUBS],
            self.suits[Suit.DIAMONDS],
            self.suits[Suit.HEARTS],
            self.suits[Suit.SPADES])


class Deal:
    def __init__(self, dealer: str, ns_vulnerable: bool, ew_vulnerable: bool, north_hand: PlayerHand,
                 east_hand: PlayerHand, south_hand: PlayerHand, west_hand: PlayerHand):
        self.dealer = dealer
        self.ns_vulnerable = ns_vulnerable
        self.ew_vulnerable = ew_vulnerable
        self.hands = {}
        self.hands[Direction.NORTH] = north_hand
        self.hands[Direction.SOUTH] = south_hand
        self.hands[Direction.EAST] = east_hand
        self.hands[Direction.WEST] = west_hand

    def __str__(self):
        header = "{} Deals\nns_vuln:{}\new_vuln:{}\n".format(self.dealer, self.ns_vulnerable, self.ew_vulnerable)
        hands = "North:\n{}\nEast:\n{}\nSouth:\n{}\nWest:\n{}".format(
            self.hands[Direction.NORTH],
            self.hands[Direction.EAST],
            self.hands[Direction.SOUTH],
            self.hands[Direction.WEST])
        return header + hands

    def player_cards(self):
        return {direction: self.hands[direction].cards for direction in self.hands}
