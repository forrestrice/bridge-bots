import unittest

from bridgebots import Card, PlayerHand, Rank, Suit


class TestDeal(unittest.TestCase):
    def test_valid_player_hand_cards(self):
        ph = PlayerHand.from_string_lists(["J", "9", "8", "3", "2"], ["10", "3"], ["A", "K", "Q"], ["A", "K", "2"])
        self.assertEqual(13, len(ph.cards))

    def test_constructor_sorts(self):
        ph = PlayerHand.from_string_lists(["J", "9", "8", "3", "2"], ["10", "3"], ["A", "K", "Q"], ["2", "A", "K"])
        self.assertEqual(
            [Card(Suit.SPADES, Rank.JACK), Card(Suit.SPADES, Rank.NINE), Card(Suit.SPADES, Rank.EIGHT)], ph.cards[0:3]
        )

    def test_holding_str(self):
        cards = [
            Card.from_str(c) for c in ["S6", "S5", "HA", "H8", "H6", "DA", "DK", "DJ", "DT", "D6", "D5", "CJ", "C4"]
        ]
        hand = PlayerHand.from_cards(cards)
        self.assertEqual("65 A86 AKJT65 J4", hand.holding_str())

    def test_holding_str_void(self):
        cards = [
            Card.from_str(c) for c in ["SA", "S8", "S6", "S5", "DA", "DK", "DJ", "DT", "D6", "D5", "CJ", "C4", "C2"]
        ]
        hand = PlayerHand.from_cards(cards)
        self.assertEqual("A865 - AKJT65 J42", hand.holding_str())
