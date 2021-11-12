from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

from bridgebots.deal import Deal
from bridgebots.deal_enums import BiddingSuit, Direction
from bridgebots.deal_utils import from_acbl_dict


class DoubleDummyScore:
    """
    Represents the double-dummy number of tricks available for declaring each suit from each direction
    """

    suit_identifiers = {
        "C": BiddingSuit.CLUBS,
        "D": BiddingSuit.DIAMONDS,
        "H": BiddingSuit.HEARTS,
        "S": BiddingSuit.SPADES,
        "NT": BiddingSuit.NO_TRUMP,
    }

    def __init__(self, scores: Dict[Direction, Dict[BiddingSuit, int]]):
        self.scores = scores
        assert 20 == sum([len(suit_scores) for direction, suit_scores in self.scores.items()])

    @staticmethod
    def from_acbl_strings(dd_north_south: str, dd_east_west: str) -> DoubleDummyScore:
        scores = {}
        scores.update(DoubleDummyScore._scores_from_acbl_string(dd_north_south, Direction.NORTH, Direction.SOUTH))
        scores.update(DoubleDummyScore._scores_from_acbl_string(dd_north_south, Direction.NORTH, Direction.SOUTH))
        scores.update(DoubleDummyScore._scores_from_acbl_string(dd_east_west, Direction.EAST, Direction.WEST))
        return DoubleDummyScore(scores)

    @staticmethod
    def _extract_score(score_str: str, with_book: bool) -> Tuple[int, int]:
        book_tricks = 6 if with_book else 0
        if "/" in score_str:
            score_str_list = score_str.split("/")
            return book_tricks + int(score_str_list[0]), book_tricks + int(score_str_list[1])
        else:
            return book_tricks + int(score_str), book_tricks + int(score_str)

    @staticmethod
    def _extract_suit(suit_score: str) -> Tuple[str, BiddingSuit, bool]:
        for suit_identifier, suit in DoubleDummyScore.suit_identifiers.items():
            if suit_identifier in suit_score:
                # if the suit comes after the number, the trick score is +6
                with_book = suit_score.index(suit_identifier) > 0
                return suit_score.replace(suit_identifier, ""), suit, with_book

    @staticmethod
    def _scores_from_acbl_string(
        acbl_str: str, first_direction: Direction, second_direction: Direction
    ) -> Dict[Direction, Dict[BiddingSuit, int]]:
        """Parse a string like '2C 2/-H 1S 3/2NT D6 H8/6' into two score dictionary entries"""
        scores = defaultdict(dict)
        suit_score_strings = acbl_str.split()
        for suit_score_str in suit_score_strings:
            # If one direction can make 7 tricks in a given suit but their partner cannot, then the lower score will
            # be represented as a '-'. In these cases a full trick score will be given later in the string, so skip the
            # current score
            if "-" in suit_score_str:
                continue
            score_str, suit, with_book = DoubleDummyScore._extract_suit(suit_score_str)
            first_score, second_score = DoubleDummyScore._extract_score(score_str, with_book)
            scores[first_direction][suit] = first_score
            scores[second_direction][suit] = second_score
        return scores


# TODO remove in favor of DealRecord
class DoubleDummyDeal:
    """
    Wrapper class which holds a deal and its double dummy scores
    """

    def __init__(self, deal: Deal, dd_score: DoubleDummyScore):
        self.deal = deal
        self.dd_score = dd_score

    @staticmethod
    def from_acbl_dict(acbl_dict: Dict[str, str]) -> DoubleDummyDeal:
        dd_score = DoubleDummyScore.from_acbl_strings(
            acbl_dict["double_dummy_north_south"], acbl_dict["double_dummy_east_west"]
        )
        return DoubleDummyDeal(from_acbl_dict(acbl_dict), dd_score)
