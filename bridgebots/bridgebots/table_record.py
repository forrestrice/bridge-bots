from typing import List

from bridgebots.deal import Card
from bridgebots.deal_enums import Direction


class TableRecord:
    """
    The record of a played deal. Often called a "board"
    """

    def __init__(
        self,
        bidding_record: List[str],
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
    ):
        self.bidding_record = bidding_record
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

    def __str__(self) -> str:
        return str(vars(self))
