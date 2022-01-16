from __future__ import annotations

from dataclasses import InitVar, dataclass
from typing import Dict, List, Optional

from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import BiddingSuit, Direction
from bridgebots.play_utils import calculate_score


@dataclass(frozen=True)
class BidMetadata:
    """
    Represents the alert status and the explanation of a bid
    """

    bid_index: int
    bid: str
    alerted: bool = False
    explanation: Optional[str] = None


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class Contract:
    """
    The final contract of a played board. Includes level (6 in 6NT), Bidding Suit (None if passed out), and number of
    times the contract was doubled
    """

    level: int
    suit: Optional[BiddingSuit]
    doubled: int

    @staticmethod
    def from_str(contract: str) -> Contract:
        working_contract = contract
        try:
            if working_contract == "PASS":
                return Contract(0, None, 0)
            doubled = working_contract.count("X")
            if doubled > 0:
                working_contract = working_contract.replace("X", "")
            level = int(working_contract[0])
            suit = BiddingSuit.from_str(working_contract[1:])
            return Contract(level, suit, doubled)
        except (ValueError, IndexError, KeyError) as e:
            raise ValueError(f"Invalid Contract: {contract}") from e

    def __str__(self):
        if self.level == 0:
            return "PASS"
        contract_str = str(self.level) + self.suit.abbreviation()
        for i in range(self.doubled):
            contract_str += "X"
        return contract_str


@dataclass(frozen=True)
class BoardRecord:
    """
    The record of a played deal.
    This class implements __hash__ and __eq__ so the internal lists should be treated as immutable
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
            score = calculate_score(
                self.contract.level, self.contract.suit, self.contract.doubled, self.tricks, declarer_vulnerable
            )
            super().__setattr__("score", score)  # Cannot assign directly because dataclass is frozen

    def __hash__(self):
        return hash(
            (
                tuple(self.bidding_record),
                tuple(self.raw_bidding_record),
                tuple(self.play_record),
                self.declarer,
                self.contract,
                self.tricks,
                self.scoring,
                frozenset(self.names.items()) if self.names else None,
                self.date,
                self.event,
                tuple(self.bidding_record) if self.bidding_record else None,
                tuple(self.commentary) if self.commentary else None,
                self.score,
            )
        )


@dataclass
class DealRecord:
    """
    Wrapper class for a deal and all the board records associated with the deal
    """

    deal: Deal
    board_records: List[BoardRecord]
