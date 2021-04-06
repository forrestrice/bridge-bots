from __future__ import annotations

from collections import defaultdict
from functools import total_ordering
from typing import Dict, List, Tuple

from deal.deal_enums import Direction, Rank, Suit


@total_ordering
class Card:
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

    def __hash__(self):
        return hash(set(self.cards))


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

    def __hash__(self):
        card_sets = [(direction, frozenset(self.hands[direction].cards)) for direction in self.hands]
        return hash((self.dealer, self.ns_vulnerable, self.ew_vulnerable, frozenset(card_sets)))

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

    ns_vuln_strings = {'Both', 'N-S', 'All', 'NS'}
    ew_vuln_strings = {'Both', 'E-W', 'All', 'EW'}

    @staticmethod
    def from_acbl_dict(acbl_dict: Dict[str, str]) -> Deal:
        player_cards = {}
        for direction in Direction:
            suit_keys = [direction.name.lower() + "_" + suit.name.lower() for suit in Suit]
            suit_string_lists = [[] if acbl_dict[suit_key] == "-----" else acbl_dict[suit_key].split() for suit_key in suit_keys]
            player_cards[direction] = PlayerHand.from_string_lists(*suit_string_lists)

        dealer_direction = Direction[acbl_dict["dealer"].upper()]
        vuln_string = acbl_dict["vulnerability"]
        ns_vuln = vuln_string in Deal.ns_vuln_strings
        ew_vuln = vuln_string in Deal.ew_vuln_strings
        return Deal(dealer_direction, ns_vuln, ew_vuln, player_cards)

    @staticmethod
    def from_pbn_deal(dealer_str: str, vulnerability_str: str, deal_str: str) -> Deal:
        ns_vulnerable = vulnerability_str in Deal.ns_vuln_strings
        ew_vulnerable = vulnerability_str in Deal.ew_vuln_strings

        dealer = Direction.from_char(dealer_str)

        hands_direction = Direction.from_char(dealer_str[0])
        deal_str = deal_str[2:]
        player_hands = {}
        for player_str in deal_str.split():
            suits = player_str.split('.')
            suits.reverse()
            player_hands[hands_direction] = PlayerHand.from_string_lists(*suits)
            hands_direction = hands_direction.next()

        return Deal(dealer, ns_vulnerable, ew_vulnerable, player_hands)
