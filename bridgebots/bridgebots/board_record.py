from typing import List

from bridgebots.deal import Card
from bridgebots.deal_enums import Direction


class BidMetadata:
    def __init__(self, bid_index: int, bid: str, alerted: bool = False, explanation: str = None):
        self.bid_index = bid_index
        self.bid = bid
        self.alerted = alerted
        self.explanation = explanation

    def __str__(self) -> str:
        return str(vars(self))

    def __eq__(self, other) -> bool:
        return (
            self.bid_index == other.bid_index
            and self.bid == other.bid
            and self.alerted == other.alerted
            and self.explanation == other.explanation
        )


class BoardRecord:
    """
    The record of a played deal.
    """

    def __init__(
        self,
        bidding_record: List[str],
        raw_bidding_record: List[str],
        play_record: List[Card],
        declarer: Direction,
        contract: str,
        tricks: int,
        scoring: str = None,
        north: str = None,
        south: str = None,
        east: str = None,
        west: str = None,
        date: str = None,
        event: str = None,
        bidding_metadata: List[BidMetadata] = None,
        commentary: str = None,
    ):
        self.bidding_record = bidding_record
        self.raw_bidding_record = raw_bidding_record
        self.play_record = play_record
        self.declarer = declarer
        self.contract = contract
        self.tricks = tricks
        self.scoring = scoring
        self.north = north
        self.south = south
        self.east = east
        self.west = west
        self.date = date
        self.event = event
        self.bidding_metadata = bidding_metadata
        self.commentary = commentary

    def __str__(self) -> str:
        return str(vars(self))

    def __eq__(self, other) -> bool:
        return (
            self.bidding_record == other.bidding_record
            and self.raw_bidding_record == other.raw_bidding_record
            and self.play_record == other.play_record
            and self.declarer == other.declarer
            and self.contract == other.contract
            and self.tricks == other.tricks
            and self.scoring == other.scoring
            and self.north == other.north
            and self.south == other.south
            and self.east == other.east
            and self.west == other.west
            and self.date == other.date
            and self.event == other.event
            and self.bidding_metadata == other.bidding_metadata
            and self.commentary == other.commentary
        )
