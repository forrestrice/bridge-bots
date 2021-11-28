import json
import unittest

from bridgebots import Deal, Direction, PlayerHand, Suit, deal_utils, from_acbl_dict


class TestAcblDeal(unittest.TestCase):
    def test_deal_from_acbl_handrecord(self):
        handrecord = (
            '{"box_number":"03151000","board_number":36,'
            '"north_spades":"10 6 2","north_hearts":"A Q 10 9 3","north_diamonds":"6 2","north_clubs":"K 8 2",'
            '"east_spades":"K Q 4 3","east_hearts":"7 5","east_diamonds":"Q J 10 7","east_clubs":"Q 9 5",'
            '"south_spades":"A 9 8","south_hearts":"K 8 2","south_diamonds":"A 5 4 3","south_clubs":"A 10 7",'
            '"west_spades":"J 7 5","west_hearts":"J 6 4","west_diamonds":"K 9 8","west_clubs":"J 6 4 3",'
            '"double_dummy_north_south":"2C 1D 3H 2S 3NT","double_dummy_east_west":"C5 D6 H4 S5 NT4",'
            '"double_dummy_par_score":"+600 3NT-NS","dealer":"west","vulnerability":"Both"}'
        )

        handrecord_json = json.loads(handrecord)
        deal = from_acbl_dict(handrecord_json)
        expected_north = PlayerHand.from_string_lists(
            ["K", "8", "2"], ["6", "2"], ["A", "Q", "10", "9", "3"], ["10", "6", "2"]
        )
        self.assertEqual(expected_north, deal.hands[Direction.NORTH])
        self.assertTrue(deal.ns_vulnerable)
        self.assertTrue(deal.ew_vulnerable)
        self.assertEqual(Direction.WEST, deal.dealer)

    def test_deal_from_handrecord_with_void(self):
        handrecord = (
            '{"box_number": "11091800", "board_number": 6, '
            '"north_spades": "A K", "north_hearts": "J 8 5", "north_diamonds": "Q 10 7", "north_clubs": "A K J 9 7",'
            ' "east_spades": "Q J 9 7 5", "east_hearts": "A 9 3", "east_diamonds": "A K 8 3 2", "east_clubs": "-----",'
            ' "south_spades": "10 8 6 2", "south_hearts": "10 7 6 2", "south_diamonds": "9 6", "south_clubs": "Q 4 2", '
            '"west_spades": "4 3", "west_hearts": "K Q 4", "west_diamonds": "J 5 4", "west_clubs": "10 8 6 5 3", '
            '"double_dummy_north_south": "2/1C 1NT D3 H6 S5", "double_dummy_east_west": "3D 2S C5 H6 NT6", '
            '"double_dummy_par_score": "-110 3D-EW", "dealer": "East", "vulnerability": "E-W"}'
        )

        handrecord_json = json.loads(handrecord)
        deal = from_acbl_dict(handrecord_json)
        self.assertEqual(0, len(deal.hands[Direction.EAST].suits[Suit.CLUBS]))


class TestBinaryDeal(unittest.TestCase):
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

    def test_serialize_then_deserialize(self):
        binary_deal = deal_utils.serialize_deal(TestBinaryDeal.test_deal)
        out_deal = deal_utils.deserialize_deal(binary_deal)
        self.assertEqual(TestBinaryDeal.test_deal, out_deal)
