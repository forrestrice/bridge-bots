from typing import List, Optional

from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import Direction


class BidMetadata:
    def __init__(self, bid_index: int, bid: str, alerted: bool = False, explanation: str = None):
        self.bid_index = bid_index
        self.bid = bid
        self.alerted = alerted
        self.explanation = explanation

    def __repr__(self) -> str:
        return (
            f"BidMetadata(bid_index={self.bid_index}, bid={self.bid}, alerted={self.alerted}, "
            f"explanation={self.explanation})"
        )

    def __eq__(self, other) -> bool:
        return (
            self.bid_index == other.bid_index
            and self.bid == other.bid
            and self.alerted == other.alerted
            and self.explanation == other.explanation
        )


class Commentary:
    def __init__(self, bid_index: Optional[int], play_index: Optional[int], comment):
        self.bid_index = bid_index
        self.play_index = play_index
        self.comment = comment

    def __repr__(self) -> str:
        return f"Commentary(bid_index={self.bid_index}, play_index={self.play_index}, comment={self.comment})"

    def __eq__(self, other) -> bool:
        return (
            self.bid_index == other.bid_index and self.play_index == other.play_index and self.comment == other.comment
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
        commentary: List[Commentary] = None,
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

    def __repr__(self) -> str:
        return (
            f"BoardRecord(\n"
            f"\tbidding_record={self.bidding_record},\n"
            f"\traw_bidding_record={self.raw_bidding_record},\n"
            f"\tplay_record={self.play_record},\n"
            f"\tdeclarer={self.declarer}, contract={self.contract}, tricks={self.tricks}, scoring={self.scoring},\n"
            f"\tnorth={self.north}, south={self.south}, east={self.east}, west={self.west},\n"
            f"\tdate={self.date}, event={self.event},\n"
            f"\tbidding_metadata={self.bidding_metadata},\n"
            f"\tcommentary={self.commentary})\n"
            f")"
        )

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


class DealRecord:
    def __init__(self, deal: Deal, board_records: List[BoardRecord]):
        self.deal = deal
        self.board_records = board_records

    def __repr__(self) -> str:
        return f"DealRecord(\n" \
               f"deal={self.deal},\n" \
               f"board_records={self.board_records}\n" \
               f")"

    def __eq__(self, other) -> bool:
        return self.deal == other.deal and self.board_records == other.board_records

