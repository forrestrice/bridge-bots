import dataclasses
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bridgebots.bids import canonicalize_bid
from bridgebots.board_record import BidMetadata, BoardRecord, Contract, DealRecord
from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import BiddingSuit, Direction
from bridgebots.deal_utils import from_pbn_deal
from bridgebots.play_utils import trick_evaluator


def _split_pbn(file_path: Path) -> List[List[str]]:
    """
    Read in the entire PBN file. Split on lines consisting of '*\n' into a list of strings per board
    :param file_path: path to PBN file
    :return:
    """
    with open(file_path, "r") as pbn_file:
        records = []
        current_record = ""
        while True:
            line = pbn_file.readline()
            if line == "":  # EOF
                if current_record:
                    records.append(current_record)
                return records
            elif line == "\n":  # End of Board Record
                records.append(current_record.splitlines())
                current_record = ""
            else:
                current_record += line


def _build_record_dict(record_strings: List[str]) -> Dict:
    """
    Parse the pbn line by line. When a block section like "Auction" or "Play" is encountered, collect all the content of
     the block into a single entry
    :param record_strings: List of string lines for a single board
    :return: A dictionary mapping keys from the pbn to strings or other useful values (e.g. list of strings for the
    bidding record)
    """
    record_dict = {}
    # Janky while loop to handle non bracketed lines
    i = 0
    while i < len(record_strings):
        record_string = record_strings[i]
        if not (record_string.startswith("[") or record_string.startswith("{")):
            i += 1
            continue
        if record_string.startswith("{"):
            commentary = ""
            while i < len(record_strings):
                record_string = record_strings[i]
                if record_string.startswith("["):
                    break
                commentary += record_string + " "
                i += 1
            record_dict["Commentary"] = commentary.strip()
            continue
        if record_string.startswith("[") and "]" not in record_string:
            while "]" not in record_string:
                i += 1
                record_string = record_string + record_strings[i]
        record_string = record_string.replace("[", "").replace("]", "")
        key, value = record_string.split(maxsplit=1)
        value = value.replace('"', "")
        if key == "Note":
            number, message = value.split(":", maxsplit=1)
            key = key + "_" + number
            value = message
        record_dict[key] = value
        if key == "Auction":
            auction_record = []
            i += 1
            while i < len(record_strings):
                auction_str = record_strings[i]
                if "[" in auction_str:
                    break
                auction_record.extend(auction_str.split())
                i += 1
            record_dict["bidding_record"] = auction_record

        elif key == "Play":
            play_record = []
            i += 1
            while i < len(record_strings):
                play_str = record_strings[i]
                if "[" in play_str or play_str == "*":
                    break
                play_record.append(play_str.split())
                i += 1
            record_dict["play_record"] = play_record
        else:
            i += 1
    return record_dict


def _update_bidding_metadata(
    bid_index: int, raw_bid: str, bidding_record: List[str], bidding_metadata: List[BidMetadata], record_dict: dict
):
    """
    Create or update bidding metadata for the most recent bid
    """
    if len(bidding_record) == 0:
        return
    if bidding_metadata and bidding_metadata[-1].bid_index == bid_index - 1:
        bid_metadata = bidding_metadata[-1]
    else:
        bid_metadata = BidMetadata(bid_index=bid_index - 1, bid=bidding_record[-1])
        bidding_metadata.append(bid_metadata)
    if raw_bid == "!":
        bid_metadata = dataclasses.replace(bid_metadata, alerted=True)
    else:
        # Attempt to determine which note should be used as an explanation
        match = re.match("=([0-9]+)=", raw_bid)
        if match:
            note_key = "Note_" + match.group(1)
            explanation = record_dict.get(note_key) if note_key in record_dict else raw_bid
        else:
            explanation = raw_bid
        if bid_metadata.explanation:
            bid_metadata = dataclasses.replace(bid_metadata, explanation=bid_metadata.explanation + " | " + explanation)
        else:
            bid_metadata = dataclasses.replace(bid_metadata, explanation=explanation)
    bidding_metadata[-1] = bid_metadata


def _parse_bidding_record(raw_bidding_record: List[str], record_dict: dict) -> Tuple[List[str], List[BidMetadata]]:
    """
    Check each auction string. If it is a valid bid, add it to the bidding record. If not, create/update BidMetadata for
    the previous bid. Example auction:

    1C 2NT =0= ! 3H =1= pass
    3S pass 3NT pass
    pass pass

    For 2NT create a BidMetaData which looks up Note_0 from record_dict as an explanation and sets the alert flag to
    true

    :param raw_bidding_record: All strings from the auction section of the PBN
    :param record_dict: Other fields from the PBN, including notes (bid explanations)
    :return: cleaned bidding record and bidding metadata
    """
    bid_index = 0
    bidding_record = []
    bidding_metadata = []
    for raw_bid in raw_bidding_record:
        canonical_bid = canonicalize_bid(raw_bid)
        if canonical_bid:
            bidding_record.append(canonical_bid)
            bid_index += 1
        elif raw_bid.upper() == "AP":
            bidding_record.extend(["PASS"] * 3)
            bid_index += 3
        else:
            _update_bidding_metadata(bid_index, raw_bid, bidding_record, bidding_metadata, record_dict)
    return bidding_record, bidding_metadata


def _sort_play_record(trick_records: List[List[str]], contract: str) -> List[Card]:
    """
    Untangle the true play order of the cards for a board

    PBNs record cardplay by direction. For Example
    [Play "N"]
    H6 HK HQ H5
    CA C4 C6 CK
    H2 H3 DJ H8

    The H6 was led by N and followed by the HK by E, HQ by S, and H5 by W, which meant that E won the trick. On the
    second trick, E led the C4 followed by the C6, CK, and CA. In order to create the true ordering of the first two
    tricks, we need to evaluate who won the first trick and start appending from there, wrapping around when we reach
    the 4th column.

    :param trick_records: List of List of cards played to each trick. Order is consistent by direction, not necessarily
    by time!
    :param contract: Board contract. Trump suit is used to determine trick winners
    :return: A list of Cards in played order
    """
    if contract == "":
        logging.warning(f"empty contract, cannot determine play ordering: {trick_records}")
        return []
    if contract.upper() == "PASS":
        return []
    try:
        trump_suit = BiddingSuit.from_str(contract[1:2])
        play_record = []
        start_index = 0  # represents which column is on lead
        for trick_record in trick_records:
            trick_cards = []
            for i in range(0, 4):
                card_index = (start_index + i) % 4
                card_str = trick_record[card_index]
                if card_str not in ["-", "--"]:
                    card = Card.from_str(card_str)
                    play_record.append(card)
                    trick_cards.append(card)
            # 4 cards played to trick. Determine the winning index relative to the column on lead
            if len(trick_cards) == 4:
                evaluator = trick_evaluator(trump_suit, trick_cards[0].suit)
                winning_index, winning_card = max(enumerate(trick_cards), key=lambda c: evaluator(c[1]))
                start_index = (start_index + winning_index) % 4  # wrap-around to first column if necessary
        return play_record
    except (IndexError, KeyError) as e:
        logging.warning(f"Malformed play record: {trick_records} exception:{e}")
        return []


def _parse_board_record(record_dict: Dict, deal: Deal) -> BoardRecord:
    """
    Convert the record dictionary to a BoardRecord
    :param record_dict: mapping of PBN keys to deal or board information
    :return: BoardRecord representing the people and actions at the table
    """
    declarer_str = record_dict["Declarer"]
    declarer = Direction.from_str(declarer_str) if declarer_str and declarer_str != "" else None
    raw_bidding_record = record_dict.get("bidding_record") or []
    bidding_record, bidding_metadata = _parse_bidding_record(raw_bidding_record, record_dict)
    play_record_strings = record_dict.get("play_record") or []
    play_record = _sort_play_record(play_record_strings, record_dict["Contract"])

    result_str = record_dict.get("Result")
    if not result_str:
        message = f"Missing tricks result: {result_str}"
        logging.warning(message)
        raise ValueError(message)

    contract_str = record_dict.get("Contract")
    if not contract_str:
        message = f"Missing contract: {contract_str}"
        logging.warning(message)
        raise ValueError(message)

    player_names = {
        Direction.NORTH: record_dict.get("North"),
        Direction.SOUTH: record_dict.get("South"),
        Direction.EAST: record_dict.get("East"),
        Direction.WEST: record_dict.get("West"),
    }

    return BoardRecord(
        bidding_record=bidding_record,
        raw_bidding_record=raw_bidding_record,
        play_record=play_record,
        declarer=declarer,
        contract=Contract.from_str(contract_str),
        declarer_vulnerable=deal.is_vulnerable(declarer),
        tricks=int(result_str),
        scoring=record_dict.get("Scoring"),
        names=player_names,
        date=record_dict.get("Date"),
        event=record_dict.get("Event"),
        bidding_metadata=bidding_metadata,
        # TODO adjust to use commentary type
        commentary=record_dict.get("Commentary"),
    )


def _parse_single_pbn_record(record_strings: List[str], previous_deal: Optional[Deal]) -> Tuple[Deal, BoardRecord]:
    """
    :param record_strings: One string per line of a single PBN deal record
    :return: Deal and BoardRecord corresponding to the PBN record
    """
    record_dict = _build_record_dict(record_strings)
    try:
        deal = from_pbn_deal(record_dict["Dealer"], record_dict["Vulnerable"], record_dict["Deal"])
    except KeyError as e:
        if previous_deal:
            deal = previous_deal
        else:
            raise ValueError("Missing deal fields and no previous_deal provided") from e
    board_record = _parse_board_record(record_dict, deal)
    return deal, board_record


def parse_pbn(file_path: Path) -> List[DealRecord]:
    """
    Split PBN file into boards then decompose those boards into Deal and BoardRecord objects. Only supports PBN v1.0
    See https://www.tistis.nl/pbn/pbn_v10.txt

    :param file_path: path to a PBN file
    :return: A list of DealRecords representing all the boards played
    """
    records_strings = _split_pbn(file_path)
    # Maintain a mapping from deal to board records to create a single deal record per deal
    records = defaultdict(list)
    # Some PBNs have multiple board records per deal
    previous_deal = None
    for record_strings in records_strings:
        try:
            deal, board_record = _parse_single_pbn_record(record_strings, previous_deal)
            records[deal].append(board_record)
            previous_deal = deal
        except (KeyError, ValueError) as e:
            logging.warning(f"Malformed record {record_strings}: {e}")
    return [DealRecord(deal, board_records) for deal, board_records in records.items()]
