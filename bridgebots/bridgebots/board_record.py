from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Dict, List, Optional

from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import BiddingSuit, Direction
from bridgebots.play_utils import calculate_score


@dataclass
class BidMetadata:
    """
    Represents the alert status and the explanation of a bid
    """

    bid_index: int
    bid: str
    alerted: bool = False
    explanation: Optional[str] = None


@dataclass
class Commentary:
    """
    Analyst commentary on the board, bidding, or play.
    Commentary before the board will have a bid_index of -1 and a play_index of None
    Commentary during bidding or cardplay will have the appropriate bidding/play indices
    Commentary after the play will have a play_index of the last card played in the hand
    """

    bid_index: Optional[int]
    play_index: Optional[int]
    comment: str


@dataclass
class Contract:
    level: int
    suit: Optional[BiddingSuit]
    doubled: int

    @staticmethod
    def from_str(contract: str) -> Contract:
        if contract == "PASS":
            return Contract(0, None, 0)
        doubled = contract.count("X")
        if doubled > 0:
            contract = contract.replace("X", "")
        level = int(contract[0])
        suit = BiddingSuit.from_str(contract[1:])
        return Contract(level, suit, doubled)


@dataclass
class BoardRecord:
    """
    The record of a played deal.
    """

    bidding_record: List[str]
    raw_bidding_record: List[str]
    play_record: List[Card]
    declarer: Direction
    contract: Contract
    tricks: int
    scoring: Optional[str]
    names: Optional[Dict[Direction, str]]
    date: Optional[str]
    event: Optional[str]
    bidding_metadata: Optional[List[BidMetadata]]
    commentary: Optional[List[Commentary]]
    declarer_vulnerable: InitVar[bool] = None
    score: int = None

    def __post_init__(self, declarer_vulnerable: bool):
        if self.score is None and declarer_vulnerable is None:
            raise ValueError("score and declarer_vulnerable may not both be None")
        if self.score is None:
            self.score = calculate_score(
                self.contract.level, self.contract.suit, self.contract.doubled, self.tricks, declarer_vulnerable
            )


@dataclass
class DealRecord:
    """
    Wrapper class for a deal and all the board records associated with the deal
    """

    deal: Deal
    board_records: List[BoardRecord]
