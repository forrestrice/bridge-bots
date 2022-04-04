import logging
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from bridgebots import (
    BiddingSuit,
    BoardRecord,
    Card,
    Deal,
    DealRecord,
    Direction,
    build_lin_url,
    parse_multi_lin,
    parse_pbn,
)
from bridgebots.deal_utils import calculate_shape, count_hcp


def _calculate_trump_data(deal: Deal, board_record: BoardRecord) -> Tuple[Optional[int], Optional[int]]:
    if board_record.contract.suit == BiddingSuit.NO_TRUMP:
        return None, None
    trump_suit = board_record.contract.suit.to_suit()
    offense_trumps = []
    offense_trumps.extend(deal.player_cards[board_record.declarer])
    offense_trumps.extend(deal.player_cards[board_record.declarer.partner()])
    offense_trumps = [c for c in offense_trumps if c.suit == trump_suit]
    return len(offense_trumps), count_hcp(offense_trumps)


def _extract_board_data(deal: Deal, board_record: BoardRecord, results_path: Path) -> Dict:
    """
    :return: A dictionary of csv keys to data values for use in a csv.DictWriter
    """
    board_dict = {}
    board_dict["board_id"] = board_record.board_name
    board_dict["file"] = results_path.name
    board_dict["deal_hash"] = hash(deal)
    board_dict.update({direction.name.lower(): board_record.names[direction] for direction in Direction})
    board_dict["dealer"] = deal.dealer.name.lower()
    board_dict["vulnerable"] = _calculate_vulnerable(deal)
    board_dict["bidding"] = _create_bidding_entry(board_record)

    opener_seat, opening_bid, opener_hcp, opener_shape_str = _calculate_opener_data(deal, board_record)
    board_dict["opener"] = opener_seat
    board_dict["opening"] = opening_bid
    board_dict["opener_hcp"] = opener_hcp
    board_dict["opener_shape"] = opener_shape_str

    overcall_type, overcall, overcaller_hcp, overcaller_shape_str, contested, competitive = _calculate_overcaller_data(
        deal, board_record
    )
    board_dict["overcall_type"] = overcall_type
    board_dict["overcall"] = overcall
    board_dict["overcaller_hcp"] = overcaller_hcp
    board_dict["overcaller_shape"] = overcaller_shape_str
    board_dict["contested"] = contested
    board_dict["competitive"] = competitive

    board_dict["declarer"] = board_record.declarer.name.lower()
    board_dict["contract"] = str(board_record.contract)
    board_dict["lead"] = board_record.play_record[0] if len(board_record.play_record) > 0 else None
    board_dict["result"] = _create_contract_result(board_record)
    board_dict["tricks"] = board_record.tricks
    board_dict["score_ns"], board_dict["score_ew"] = _calculate_direction_scores(board_record)
    board_dict["score_declarer"], board_dict["score_defender"] = board_record.score, board_record.score * -1
    board_dict["link"] = build_lin_url(deal, board_record)

    board_dict["declarer_shape"] = _calculate_shape_str(deal.player_cards[board_record.declarer])
    board_dict["dummy_shape"] = _calculate_shape_str(deal.player_cards[board_record.declarer.partner()])
    board_dict["lho_shape"] = _calculate_shape_str(deal.player_cards[board_record.declarer.offset(1)])
    board_dict["rho_shape"] = _calculate_shape_str(deal.player_cards[board_record.declarer.offset(3)])

    board_dict["declarer_hcp"] = count_hcp(deal.player_cards[board_record.declarer])
    board_dict["dummy_hcp"] = count_hcp(deal.player_cards[board_record.declarer.partner()])
    board_dict["lho_hcp"] = count_hcp(deal.player_cards[board_record.declarer.offset(1)])
    board_dict["rho_hcp"] = count_hcp(deal.player_cards[board_record.declarer.offset(3)])

    trump_fit, trump_hcp = _calculate_trump_data(deal, board_record)
    board_dict["trump_fit"] = trump_fit
    board_dict["trump_hcp"] = trump_hcp

    return board_dict


def _calculate_shape_str(cards: List[Card]) -> str:
    """Calculate a shape tuple like (5,3,3,2) and convert it to a shape_str like 5332"""
    return "".join(str(s) for s in calculate_shape(cards))


def _calculate_opener_data(
    deal: Deal, board_record: BoardRecord
) -> Tuple[Optional[int], Optional[str], Optional[int], Optional[str]]:
    """
    :return: the seat which opened, the opening bid, opener's high card points, and opener's shape
    """
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
    opener_shape_str = _calculate_shape_str(opener_cards)
    return seat, opening_bid, opener_hcp, opener_shape_str


def _calculate_overcaller_data(
    deal, board_record
) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str], Optional[bool], Optional[bool]]:
    """
    :return: the overcall type (direct, balance, or sandwich) the overcall bid, overcallers's high card points,
    overcaller's shape, and a contested boolean. The boolean will be true if someone overcalled or if one of players on
    the non-opening team eventually made any bid other than PASS.
    """
    opener = None
    open_index = None
    for i in range(4):
        if board_record.bidding_record[i] != "PASS":
            opener = deal.dealer.offset(i)
            open_index = i
            break
    if opener is None:
        return None, None, None, None, None, None
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
        overcaller_shape_str = _calculate_shape_str(overcaller_cards)

    contested = False
    for i, bid in enumerate(board_record.bidding_record[open_index:]):
        if i % 2 > 0 and bid != "PASS":
            contested = True
            break

    bid_counter = [0, 0]
    for i, bid in enumerate(board_record.bidding_record):
        if bid != "PASS":
            bid_counter[i%2] += 1
    competitive = bid_counter[0] >= 2 and bid_counter[1] >= 2
    return overcall_type, overcall, overcaller_hcp, overcaller_shape_str, contested, competitive


def _calculate_vulnerable(deal: Deal) -> str:
    """
    :return: which seats were vulnerable (1-indexed)
    """
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


def _create_bidding_entry(board_record: BoardRecord) -> str:
    """
    :return: A string representing the bids, the alerts, and the announcements
    """
    bidding_copy = board_record.bidding_record.copy()
    for bid_metadata in board_record.bidding_metadata:
        if bid_metadata.alerted:
            bidding_copy[bid_metadata.bid_index] += "!"
        if bid_metadata.explanation:
            bidding_copy[bid_metadata.bid_index] += f"({bid_metadata.explanation})"
    return "|".join(bidding_copy)


def _create_contract_result(board_record: BoardRecord) -> str:
    if board_record.contract.level == 0:
        return "PASS"
    trick_delta = board_record.tricks - (board_record.contract.level + 6)
    if trick_delta > 0:
        trick_delta_str = f"+{trick_delta}"
    elif trick_delta == 0:
        trick_delta_str = "="
    else:
        trick_delta_str = str(trick_delta)
    return str(board_record.contract) + trick_delta_str


def _calculate_direction_scores(board_record: BoardRecord) -> Tuple[int, int]:
    """
    :return: A tuple of north-south and east-west scores. Useful to have both for team comparisons.
    """
    ns_score = (
        board_record.score if board_record.declarer in [Direction.NORTH, Direction.SOUTH] else -1 * board_record.score
    )
    return ns_score, ns_score * -1


def _generate_input_file_paths(input_format: str, input_path: Path) -> Generator[Path, None, None]:
    results_file_paths = []
    if input_path.is_file():
        results_file_paths.append(input_path)
    elif input_path.is_dir():
        results_file_paths.extend(input_path.rglob(f"*.{input_format}"))
    logging.debug(f"Found {len(results_file_paths)} {input_format} files to read.")
    yield from results_file_paths


def _parse_results_file(results_file_path: Path, input_format: str) -> List[DealRecord]:
    logging.debug(f"Processing {results_file_path}")
    if input_format == "lin":
        deal_records = parse_multi_lin(results_file_path)
    else:
        deal_records = parse_pbn(results_file_path)
    logging.debug(f"Found {len(deal_records)} deals in {results_file_path}")
    return deal_records
