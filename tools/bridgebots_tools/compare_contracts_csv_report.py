import dataclasses
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import click

from bridgebots import BoardRecord, Deal, Direction
from bridgebots_tools.csv_utilities import _write_results
from bridgebots_tools.data_extractors import _extract_board_data, _generate_input_file_paths, _parse_results_file
from bridgebots_tools.tools_logging import configure_logging


@dataclasses.dataclass
class TraceableRecord:
    deal: Deal
    board_record: BoardRecord
    file_path: Path


def _get_direction_key(direction_comparison_type: str, board_record: BoardRecord):
    if direction_comparison_type == "any":
        return "any"
    if board_record.declarer in [Direction.NORTH, Direction.SOUTH]:
        return "ns"
    return "ew"


def _build_comparisons(
    deal_comparison_type: str,
    direction_comparison_type: str,
    left_boards: Dict[int, Dict[str, List[TraceableRecord]]],
    right_boards: Dict[int, Dict[str, List[TraceableRecord]]],
) -> List[Tuple[List[TraceableRecord], List[TraceableRecord]]]:
    comparisons = []
    for deal_hash, left_direction_dict in left_boards.items():
        if deal_hash not in right_boards:
            for direction_key, boards in left_direction_dict.items():
                comparisons.append((boards, []))
        else:
            right_direction_dict = right_boards[deal_hash]
            for right_direction_key, right_results in right_direction_dict.items():
                for left_direction_key, left_results in left_direction_dict.items():
                    if direction_comparison_type == "opposite_direction":
                        if left_direction_key != right_direction_key:
                            comparisons.append((left_results, right_results))
                    elif left_direction_key == right_direction_key:
                        comparisons.append((left_results, right_results))

    for deal_hash, right_direction_dict in right_boards.items():
        if deal_hash not in left_boards:
            for direction_key, boards in right_direction_dict.items():
                comparisons.append(([], boards))

    if deal_comparison_type == "same_deal":
        comparisons = [c for c in comparisons if len(c[0]) > 0 and len(c[1]) > 0]
    return comparisons


@click.command()
@click.option("--input_format", type=click.Choice(["lin", "pbn"], case_sensitive=False), default="lin")
@click.option(
    "--deal_comparison_type", type=click.Choice(["same_deal", "any"], case_sensitive=False), default="same_deal"
)
@click.option(
    "--direction_comparison_type",
    type=click.Choice(["same_direction", "opposite_direction", "any"], case_sensitive=False),
    default="same_direction",
)
@click.option("--lax_doubles/--strict_doubles", default=True)
@click.option("--verbose", "log_level", "-v", flag_value="verbose")
@click.option("--info", "log_level", flag_value="info", default=True)
@click.option("--quiet", "log_level", "-q", flag_value="quiet")
@click.argument("contract_sets", nargs=2)
@click.argument("input_path", type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path))
@click.argument(
    "output_path", type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path), required=False
)
def report(
    input_format: str,
    deal_comparison_type: str,
    direction_comparison_type: str,
    lax_doubles: bool,
    log_level: str,
    contract_sets: List[str],
    input_path: Path,
    output_path: Path,
):
    configure_logging(log_level)
    results_file_paths = _generate_input_file_paths(input_format, input_path)
    left_contracts, right_contracts = [contract_set_str.split(",") for contract_set_str in contract_sets]
    left_boards, right_boards = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for results_file_path in results_file_paths:
        deal_records = _parse_results_file(results_file_path, input_format)
        for deal_record in deal_records:
            for board_record in deal_record.board_records:
                deal_hash = hash(deal_record.deal)
                direction_key = _get_direction_key(direction_comparison_type, board_record)
                record = TraceableRecord(deal_record.deal, board_record, results_file_path)
                contract_str = str(board_record.contract).strip("X") if lax_doubles else str(board_record.contract)
                if contract_str in left_contracts:
                    left_boards[deal_hash][direction_key].append(record)
                elif contract_str in right_contracts:
                    right_boards[deal_hash][direction_key].append(record)
    compared_deals = _build_comparisons(deal_comparison_type, direction_comparison_type, left_boards, right_boards)
    logging.debug(f"Found {len(compared_deals)} comparisons")

    csv_dicts = []
    for left_results, right_results in compared_deals:
        csv_dicts.extend([_extract_board_data(tr.deal, tr.board_record, tr.file_path) for tr in left_results])
        csv_dicts.extend([_extract_board_data(tr.deal, tr.board_record, tr.file_path) for tr in right_results])

    _write_results(output_path, csv_dicts)


if __name__ == "__main__":
    report()
