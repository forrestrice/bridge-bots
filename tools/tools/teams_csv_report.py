import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click

from bridgebots import BoardRecord, Deal, DealRecord, Direction, build_lin_url, parse_multi_lin
from bridgebots.deal_utils import calculate_shape, count_hcp

# This list can be reordered or items can be removed to modify the output columns
CSV_HEADERS = [
    "board_id",
    "file",
    "north",
    "south",
    "east",
    "west",
    "dealer",
    "vulnerable",
    "bidding",
    "opener",
    "opening",
    "opener_hcp",
    "opener_shape",
    "overcall_type",
    "overcall",
    "overcaller_hcp",
    "overcaller_shape",
    "contested",
    "declarer",
    "contract",
    "tricks",
    "score",
    "link",
]

PREFIX_CSV_HEADERS = [f"o_{header}" for header in CSV_HEADERS] + [f"c_{header}" for header in CSV_HEADERS]


def calculate_opener_data(
    deal: Deal, board_record: BoardRecord
) -> Tuple[Optional[int], Optional[str], Optional[int], Optional[str]]:
    opener = None
    seat = None
    opening_bid = None
    for i in range(4):
        if board_record.bidding_record[i] != "PASS":
            opener = deal.dealer.offset(i)
            seat = i + 1
            opening_bid = board_record.bidding_record[i]
            break
    if opener is None:
        return None, None, None, None
    opener_cards = deal.player_cards[opener]
    opener_hcp = count_hcp(opener_cards)
    opener_shape = calculate_shape(opener_cards)
    opener_shape_str = "".join(str(s) for s in opener_shape)
    return seat, opening_bid, opener_hcp, opener_shape_str


def calculate_overcaller_data(
    deal, board_record
) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str], Optional[bool]]:
    opener = None
    open_index = None
    for i in range(4):
        if board_record.bidding_record[i] != "PASS":
            opener = deal.dealer.offset(i)
            open_index = i
            break
    if opener is None:
        return None, None, None, None, None
    overcall_type = None
    overcaller = None
    overcall = None
    if board_record.bidding_record[open_index + 1] != "PASS":
        overcall_type = "direct"
        overcaller = opener.offset(1)
        overcall = board_record.bidding_record[open_index + 1]
    elif board_record.bidding_record[open_index + 3] != "PASS":
        overcaller = opener.offset(3)
        overcall = board_record.bidding_record[open_index + 3]
        if board_record.bidding_record[open_index + 2] == "PASS":
            overcall_type = "balance"
        else:
            overcall_type = "sandwich"

    overcaller_hcp = None
    overcaller_shape_str = None
    if overcaller:
        overcaller_cards = deal.player_cards[overcaller]
        overcaller_hcp = count_hcp(overcaller_cards)
        overcaller_shape = calculate_shape(overcaller_cards)
        overcaller_shape_str = "".join(str(s) for s in overcaller_shape)

    contested = False
    for i, bid in enumerate(board_record.bidding_record[open_index:]):
        if i % 2 > 0 and bid != "PASS":
            contested = True
            break

    return overcall_type, overcall, overcaller_hcp, overcaller_shape_str, contested


def calculate_vulnerable(deal: Deal) -> str:
    dealer_vuln = deal.is_vulnerable(deal.dealer)
    opp_vuln = deal.is_vulnerable(deal.dealer.next())
    if dealer_vuln and opp_vuln:
        return "all"
    elif dealer_vuln:
        return "1-3"
    elif opp_vuln:
        return "2-4"
    else:
        return "none"


def create_bidding_entry(board_record: BoardRecord):
    bidding_copy = board_record.bidding_record.copy()
    for bid_metadata in board_record.bidding_metadata:
        if bid_metadata.alerted:
            bidding_copy[bid_metadata.bid_index] += "!"
        if bid_metadata.explanation:
            bidding_copy[bid_metadata.bid_index] += f"({bid_metadata.explanation})"
    return "|".join(bidding_copy)


def extract_board_data(deal: Deal, board_record: BoardRecord, lin_path: Path) -> Dict:
    board_dict = {}
    board_dict["board_id"] = board_record.board_name
    board_dict["file"] = lin_path.name
    board_dict.update({direction.name.lower(): board_record.names[direction] for direction in Direction})
    board_dict["dealer"] = deal.dealer.name.lower()
    board_dict["vulnerable"] = calculate_vulnerable(deal)
    board_dict["bidding"] = create_bidding_entry(board_record)
    opener_seat, opening_bid, opener_hcp, opener_shape_str = calculate_opener_data(deal, board_record)
    board_dict["opener"] = opener_seat
    board_dict["opening"] = opening_bid
    board_dict["opener_hcp"] = opener_hcp
    board_dict["opener_shape"] = opener_shape_str
    overcall_type, overcall, overcaller_hcp, overcaller_shape_str, contested = calculate_overcaller_data(
        deal, board_record
    )
    board_dict["overcall_type"] = overcall_type
    board_dict["overcall"] = overcall
    board_dict["overcaller_hcp"] = overcaller_hcp
    board_dict["overcaller_shape"] = overcaller_shape_str
    board_dict["contested"] = contested
    board_dict["declarer"] = board_record.declarer.name.lower()
    board_dict["contract"] = str(board_record.contract)
    board_dict["tricks"] = board_record.tricks
    board_dict["score"] = board_record.score
    board_dict["link"] = build_lin_url(deal, board_record)
    return board_dict


def extract_team_dicts(deal_record: DealRecord, lin_path: Path) -> Tuple[Dict, Dict]:
    if len(deal_record.board_records) != 2:
        raise ValueError(f"Invalid number of board records for a teams match: {len(deal_record.board_records)}")
    open_board, closed_board = deal_record.board_records[0], deal_record.board_records[1]
    return extract_board_data(deal_record.deal, open_board, lin_path), extract_board_data(
        deal_record.deal, closed_board, lin_path
    )


def write_results(csv_path: Path, csv_dicts: List[Dict]):
    with open(csv_path, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=PREFIX_CSV_HEADERS)
        writer.writeheader()
        for csv_dict in csv_dicts:
            writer.writerow(csv_dict)


@click.command()
@click.option("--format", type=click.Choice(["team", "individual"], case_sensitive=False), default="team")
@click.option("--verbose/--normal", "-v/", default=False)
@click.option("--quiet/--loud", "-q/", default=False)
@click.argument("lin_path", type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path))
@click.argument("csv_path", type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path))
def report(format: str, verbose: bool, quiet: bool, lin_path: Path, csv_path: Path):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif not quiet:
        logging.basicConfig(level=logging.INFO)
    lin_file_paths = []
    if lin_path.is_file():
        lin_file_paths.append(lin_path)
    elif lin_path.is_dir():
        lin_file_paths.extend(lin_path.rglob("*.lin"))
    logging.debug(f"Found {len(lin_file_paths)} LIN files to read.")
    csv_dicts = []
    for lin_file_path in lin_file_paths:
        logging.debug(f"Processing {lin_file_path}")
        deal_records = parse_multi_lin(lin_file_path)
        logging.debug(f"Found {len(deal_records)} deals in {lin_file_path}")
        for deal_record in deal_records:
            try:
                open_dict, closed_dict = extract_team_dicts(deal_record, lin_path)
                prefix_dict = {f"o_{key}": value for key, value in open_dict.items()}
                prefix_dict.update({f"c_{key}": value for key, value in closed_dict.items()})
                csv_dicts.append(prefix_dict)
            except ValueError as e:
                logging.warning(f"Error processing deal:{deal_record}. Error:{e}")
    logging.debug(f"Writing {len(csv_dicts)} deals to {csv_path}")
    write_results(csv_path, csv_dicts)


if __name__ == "__main__":
    report()
