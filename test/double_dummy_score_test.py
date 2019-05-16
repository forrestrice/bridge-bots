import unittest

from deal.deal_enums import Direction, BiddingSuit
from deal.double_dummy import DoubleDummyScore


class TestDoubleDummyScore(unittest.TestCase):
    def test_parse(self):
        dd_score = DoubleDummyScore.from_acbl_strings("C4 D6 H5 S6 NT4", "2C 2/-H 1S 3/2NT D6 H8/6")
        self.assertEqual(4, dd_score.scores[Direction.NORTH][BiddingSuit.CLUBS])
        self.assertEqual(6, dd_score.scores[Direction.NORTH][BiddingSuit.DIAMONDS])
        self.assertEqual(5, dd_score.scores[Direction.NORTH][BiddingSuit.HEARTS])
        self.assertEqual(6, dd_score.scores[Direction.NORTH][BiddingSuit.SPADES])
        self.assertEqual(4, dd_score.scores[Direction.NORTH][BiddingSuit.NO_TRUMP])

        self.assertEqual(4, dd_score.scores[Direction.SOUTH][BiddingSuit.CLUBS])
        self.assertEqual(6, dd_score.scores[Direction.SOUTH][BiddingSuit.DIAMONDS])
        self.assertEqual(5, dd_score.scores[Direction.SOUTH][BiddingSuit.HEARTS])
        self.assertEqual(6, dd_score.scores[Direction.SOUTH][BiddingSuit.SPADES])
        self.assertEqual(4, dd_score.scores[Direction.SOUTH][BiddingSuit.NO_TRUMP])

        self.assertEqual(8, dd_score.scores[Direction.EAST][BiddingSuit.CLUBS])
        self.assertEqual(6, dd_score.scores[Direction.EAST][BiddingSuit.DIAMONDS])
        self.assertEqual(8, dd_score.scores[Direction.EAST][BiddingSuit.HEARTS])
        self.assertEqual(7, dd_score.scores[Direction.EAST][BiddingSuit.SPADES])
        self.assertEqual(9, dd_score.scores[Direction.EAST][BiddingSuit.NO_TRUMP])

        self.assertEqual(8, dd_score.scores[Direction.WEST][BiddingSuit.CLUBS])
        self.assertEqual(6, dd_score.scores[Direction.WEST][BiddingSuit.DIAMONDS])
        self.assertEqual(6, dd_score.scores[Direction.WEST][BiddingSuit.HEARTS])
        self.assertEqual(7, dd_score.scores[Direction.WEST][BiddingSuit.SPADES])
        self.assertEqual(8, dd_score.scores[Direction.WEST][BiddingSuit.NO_TRUMP])


if __name__ == '__main__':
    unittest.main()
