import unittest

from bridgebots import BiddingSuit, calculate_score


class TestScoring(unittest.TestCase):
    def test_passed_hand(self):
        self.assertEqual(0, calculate_score(0, None, 0, 0, True))

    def test_one_minor(self):
        # 1C, 1CX, 1CXX making exactly
        self.assertEqual(70, calculate_score(1, BiddingSuit.CLUBS, 0, 7, True))
        self.assertEqual(140, calculate_score(1, BiddingSuit.CLUBS, 1, 7, True))
        self.assertEqual(230, calculate_score(1, BiddingSuit.CLUBS, 2, 7, False))

        # 1C, 1CX, 1CXX making with 4 non-vulnerable overtricks
        self.assertEqual(150, calculate_score(1, BiddingSuit.CLUBS, 0, 11, False))
        self.assertEqual(540, calculate_score(1, BiddingSuit.CLUBS, 1, 11, False))
        self.assertEqual(1030, calculate_score(1, BiddingSuit.CLUBS, 2, 11, False))

        # 1C, 1CX, 1CXX making with 4 vulnerable overtricks
        self.assertEqual(150, calculate_score(1, BiddingSuit.CLUBS, 0, 11, True))
        self.assertEqual(940, calculate_score(1, BiddingSuit.CLUBS, 1, 11, True))
        self.assertEqual(1830, calculate_score(1, BiddingSuit.CLUBS, 2, 11, True))

    def test_three_no_trump(self):
        # 3N, 3NX, 3NXX making exactly
        self.assertEqual(400, calculate_score(3, BiddingSuit.NO_TRUMP, 0, 9, False))
        self.assertEqual(550, calculate_score(3, BiddingSuit.NO_TRUMP, 1, 9, False))
        self.assertEqual(800, calculate_score(3, BiddingSuit.NO_TRUMP, 2, 9, False))
        self.assertEqual(600, calculate_score(3, BiddingSuit.NO_TRUMP, 0, 9, True))
        self.assertEqual(750, calculate_score(3, BiddingSuit.NO_TRUMP, 1, 9, True))
        self.assertEqual(1000, calculate_score(3, BiddingSuit.NO_TRUMP, 2, 9, True))

        # 3N, 3NX, 3NXX making with two overtricks
        self.assertEqual(460, calculate_score(3, BiddingSuit.NO_TRUMP, 0, 11, False))
        self.assertEqual(750, calculate_score(3, BiddingSuit.NO_TRUMP, 1, 11, False))
        self.assertEqual(1200, calculate_score(3, BiddingSuit.NO_TRUMP, 2, 11, False))
        self.assertEqual(660, calculate_score(3, BiddingSuit.NO_TRUMP, 0, 11, True))
        self.assertEqual(1150, calculate_score(3, BiddingSuit.NO_TRUMP, 1, 11, True))
        self.assertEqual(1800, calculate_score(3, BiddingSuit.NO_TRUMP, 2, 11, True))

    def test_small_major_slam(self):
        # 6H, 6HX, 6HXX making exactly
        self.assertEqual(980, calculate_score(6, BiddingSuit.HEARTS, 0, 12, False))
        self.assertEqual(1210, calculate_score(6, BiddingSuit.HEARTS, 1, 12, False))
        self.assertEqual(1620, calculate_score(6, BiddingSuit.HEARTS, 2, 12, False))
        self.assertEqual(1430, calculate_score(6, BiddingSuit.HEARTS, 0, 12, True))
        self.assertEqual(1660, calculate_score(6, BiddingSuit.HEARTS, 1, 12, True))
        self.assertEqual(2070, calculate_score(6, BiddingSuit.HEARTS, 2, 12, True))

        # 6H, 6HX, 6HXX making with an overtrick
        self.assertEqual(1010, calculate_score(6, BiddingSuit.HEARTS, 0, 13, False))
        self.assertEqual(1310, calculate_score(6, BiddingSuit.HEARTS, 1, 13, False))
        self.assertEqual(1820, calculate_score(6, BiddingSuit.HEARTS, 2, 13, False))
        self.assertEqual(1460, calculate_score(6, BiddingSuit.HEARTS, 0, 13, True))
        self.assertEqual(1860, calculate_score(6, BiddingSuit.HEARTS, 1, 13, True))
        self.assertEqual(2470, calculate_score(6, BiddingSuit.HEARTS, 2, 13, True))

    def test_grand_minor_slam(self):
        # 7D, 7DX, 7DXX making exactly
        self.assertEqual(1440, calculate_score(7, BiddingSuit.DIAMONDS, 0, 13, False))
        self.assertEqual(1630, calculate_score(7, BiddingSuit.DIAMONDS, 1, 13, False))
        self.assertEqual(1960, calculate_score(7, BiddingSuit.DIAMONDS, 2, 13, False))
        self.assertEqual(2140, calculate_score(7, BiddingSuit.DIAMONDS, 0, 13, True))
        self.assertEqual(2330, calculate_score(7, BiddingSuit.DIAMONDS, 1, 13, True))
        self.assertEqual(2660, calculate_score(7, BiddingSuit.DIAMONDS, 2, 13, True))

    def test_undertricks(self):
        # 7D, 7DX, 7DXX down 1
        self.assertEqual(-50, calculate_score(7, BiddingSuit.DIAMONDS, 0, 12, False))
        self.assertEqual(-100, calculate_score(7, BiddingSuit.DIAMONDS, 1, 12, False))
        self.assertEqual(-200, calculate_score(7, BiddingSuit.DIAMONDS, 2, 12, False))
        self.assertEqual(-100, calculate_score(7, BiddingSuit.DIAMONDS, 0, 12, True))
        self.assertEqual(-200, calculate_score(7, BiddingSuit.DIAMONDS, 1, 12, True))
        self.assertEqual(-400, calculate_score(7, BiddingSuit.DIAMONDS, 2, 12, True))

        # 7D, 7DX, 7DXX down 2
        self.assertEqual(-100, calculate_score(7, BiddingSuit.DIAMONDS, 0, 11, False))
        self.assertEqual(-300, calculate_score(7, BiddingSuit.DIAMONDS, 1, 11, False))
        self.assertEqual(-600, calculate_score(7, BiddingSuit.DIAMONDS, 2, 11, False))
        self.assertEqual(-200, calculate_score(7, BiddingSuit.DIAMONDS, 0, 11, True))
        self.assertEqual(-500, calculate_score(7, BiddingSuit.DIAMONDS, 1, 11, True))
        self.assertEqual(-1000, calculate_score(7, BiddingSuit.DIAMONDS, 2, 11, True))

        # 7D, 7DX, 7DXX down 3
        self.assertEqual(-150, calculate_score(7, BiddingSuit.DIAMONDS, 0, 10, False))
        self.assertEqual(-500, calculate_score(7, BiddingSuit.DIAMONDS, 1, 10, False))
        self.assertEqual(-1000, calculate_score(7, BiddingSuit.DIAMONDS, 2, 10, False))
        self.assertEqual(-300, calculate_score(7, BiddingSuit.DIAMONDS, 0, 10, True))
        self.assertEqual(-800, calculate_score(7, BiddingSuit.DIAMONDS, 1, 10, True))
        self.assertEqual(-1600, calculate_score(7, BiddingSuit.DIAMONDS, 2, 10, True))

        # 7D, 7DX, 7DXX down 4
        self.assertEqual(-200, calculate_score(7, BiddingSuit.DIAMONDS, 0, 9, False))
        self.assertEqual(-800, calculate_score(7, BiddingSuit.DIAMONDS, 1, 9, False))
        self.assertEqual(-1600, calculate_score(7, BiddingSuit.DIAMONDS, 2, 9, False))
        self.assertEqual(-400, calculate_score(7, BiddingSuit.DIAMONDS, 0, 9, True))
        self.assertEqual(-1100, calculate_score(7, BiddingSuit.DIAMONDS, 1, 9, True))
        self.assertEqual(-2200, calculate_score(7, BiddingSuit.DIAMONDS, 2, 9, True))
