import logging
from functools import partial
from pathlib import Path
from typing import Dict, List, Tuple

from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import BiddingSuit, Direction, Suit
from bridgebots.deal_utils import from_pbn_deal
from bridgebots.table_record import TableRecord


def _split_pbn(file_path: Path) -> List[List[str]]:
    """
    Read in the entire pbn file. Split on lines consisting of '*\n' into a list of strings per board
    :param file_path: path to pbn file
    :return:
    """
    with open(file_path, "r") as pbn_file:
        records = []
        current_record = ""
        while True:
            line = pbn_file.readline()
            if line == "":
                return records
            elif line == "*\n":
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
        if not record_string.startswith("["):
            i += 1
            continue
        if "[" in record_string and "]" not in record_string:
            while "]" not in record_string:
                i += 1
                record_string = record_string + record_strings[i]
        record_string = record_string.replace("[", "").replace("]", "")
        key, value = record_string.split(maxsplit=1)
        record_dict[key] = value.replace('"', "")
        if key == "Auction":
            auction_record = []
            i += 1
            while i < len(record_strings):
                auction_str = record_strings[i]
                if "[" in auction_str:
                    break
                auction_record.extend(auction_str.split())
                i += 1
            if auction_record and auction_record[-1] in ["AP", "ap"]:
                auction_record = auction_record[:-1]  # Replace 'AP' with 3 passes
                auction_record.extend(["Pass"] * 3)
            record_dict["bidding_record"] = auction_record

        elif key == "Play":
            play_record = []
            i += 1
            while i < len(record_strings):
                play_str = record_strings[i]
                if "[" in play_str:
                    break
                play_record.append(play_str.split())
                i += 1
            record_dict["play_record"] = play_record
        else:
            i += 1
    return record_dict


def _evaluate_card(trump_suit: Suit, suit_led: Suit, card: Card) -> int:
    """
    :return: Score a card on its ability to win a trick given the trump suit and the suit that was led to the trick
    """
    score = card.rank.value[0]
    if card.suit == trump_suit:
        score += 100
    elif card.suit != suit_led:
        score -= 100
    return score


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
    if contract == "Pass":
        return []
    try:
        trump_suit = BiddingSuit.from_str(contract[1:2]).to_suit()
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
                suit_led = trick_cards[0].suit
                evaluator = partial(_evaluate_card, trump_suit, suit_led)
                winning_index, winning_card = max(enumerate(trick_cards), key=lambda c: evaluator(c[1]))
                start_index = (start_index + winning_index) % 4  # wrap-around to first column if necessary
        return play_record
    except (IndexError, KeyError) as e:
        logging.warning(f"Malformed play record: {trick_records} exception:{e}")
        return []


def _parse_table_record(record_dict: Dict) -> TableRecord:
    """
    Convert the record dictionary to a TableRecord
    :param record_dict: mapping of PBN keys to deal or board information
    :return: TableRecord representing the people and actions at the table
    """
    declarer_str = record_dict["Declarer"]
    declarer = Direction.from_str(declarer_str) if declarer_str and declarer_str != "" else None
    bidding_record = record_dict.get("bidding_record") or []
    play_record_strings = record_dict.get("play_record") or []
    play_record = _sort_play_record(play_record_strings, record_dict["Contract"])
    result_str = record_dict.get("Result")
    result = int(result_str) if result_str and result_str != "" else None

    return TableRecord(
        bidding_record=bidding_record,
        play_record=play_record,
        declarer=declarer,
        contract=record_dict["Contract"],
        tricks=result,
        scoring=record_dict.get("Scoring"),
        north=record_dict.get("North"),
        south=record_dict.get("South"),
        east=record_dict.get("East"),
        west=record_dict.get("West"),
        date=record_dict.get("Date"),
        event=record_dict.get("Event"),
    )


def parse_pbn(file_path: Path) -> List[Tuple[Deal, TableRecord]]:
    """
    Split pbn file into boards then decompose those boards into Deal and TableRecord objects
    :param file_path: path to a pbn file
    :return: A list of pairs of Deal and TableRecord
    """
    records_strings = _split_pbn(file_path)
    results = []
    for record_strings in records_strings:
        record_dict = _build_record_dict(record_strings)
        deal = from_pbn_deal(record_dict["Dealer"], record_dict["Vulnerable"], record_dict["Deal"])
        table_record = _parse_table_record(record_dict)
        results.append((deal, table_record))
    return results
