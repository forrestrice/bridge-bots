import unittest

from bridgebots.deal import Card, PlayerHand
from bridgebots.deal_enums import Rank, Suit


class TestDeal(unittest.TestCase):
    def test_valid_player_hand_cards(self):
        ph = PlayerHand.from_string_lists(["A", "K", "2"], ["A", "K", "Q"], ["10", "3"], ["J", "9", "8", "3", "2"])
        self.assertEqual(13, len(ph.cards))

    def test_constructor_sorts(self):
        ph = PlayerHand.from_string_lists(["2", "A", "K"], ["A", "K", "Q"], ["10", "3"], ["J", "9", "8", "3", "2"])
        self.assertEqual(
            [Card(Suit.CLUBS, Rank.ACE), Card(Suit.CLUBS, Rank.KING), Card(Suit.CLUBS, Rank.TWO)], ph.cards[0:3]
        )
