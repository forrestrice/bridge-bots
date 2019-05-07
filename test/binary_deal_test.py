import unittest

from deal.binary_deal import serialize, deserialize
from deal.deal import PlayerHand, Deal, Card
from deal.deal_enums import Direction, Suit, Rank

north = PlayerHand.from_string_lists(['9', '8', '6', '4'], ['K', 'Q', '7', '6', '3'], ['A', 'K'], ['7', '3'])
south = PlayerHand.from_string_lists(['A', 'K', 'Q', '5'], ['A', '9', '4'], ['J', '5', '2'], ['K', '8', '4'])
east = PlayerHand.from_string_lists(['2'], ['J', '10', '8', '5', '2'], ['Q', '8', '7', '4', '3'], ['A', '10'])
west = PlayerHand.from_string_lists(['J', '10', '7', '3'], [], ['10', '9', '6'], ['Q', 'J', '9', '6', '5', '2'])
test_deal = Deal(Direction.EAST, True, False, north, south, east, west)


class TestBinaryDeal(unittest.TestCase):
    def test_sorted_card_tuples(self):
        binary_deal = serialize(test_deal)
        print(binary_deal)

    def test_deserialize(self):
        binary_deal = serialize(test_deal)
        print(binary_deal)
        out_deal = deserialize(binary_deal)
        print("\n\n")
        print(test_deal)
        print("\n\n")
        print(out_deal)
        #self.assertEqual(test_deal, out_deal)
