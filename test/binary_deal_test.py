import unittest

from deal.deal import Deal, PlayerHand
from deal.deal_enums import Direction

hands = {
    Direction.NORTH: PlayerHand.from_string_lists(
        ["9", "8", "6", "4"], ["K", "Q", "7", "6", "3"], ["A", "K"], ["7", "3"]
    ),
    Direction.SOUTH: PlayerHand.from_string_lists(
        ["A", "K", "Q", "5"], ["A", "9", "4"], ["J", "5", "2"], ["K", "8", "4"]
    ),
    Direction.EAST: PlayerHand.from_string_lists(
        ["2"], ["J", "10", "8", "5", "2"], ["Q", "8", "7", "4", "3"], ["A", "10"]
    ),
    Direction.WEST: PlayerHand.from_string_lists(
        ["J", "10", "7", "3"], [], ["10", "9", "6"], ["Q", "J", "9", "6", "5", "2"]
    ),
}
test_deal = Deal(Direction.EAST, True, False, hands)


class TestBinaryDeal(unittest.TestCase):
    def test_serialize_then_deserialize(self):
        binary_deal = test_deal.serialize()
        out_deal = Deal.deserialize(binary_deal)
        self.assertEqual(test_deal, out_deal)
