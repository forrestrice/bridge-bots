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
