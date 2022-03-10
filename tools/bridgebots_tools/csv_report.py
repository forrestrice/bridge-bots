import logging
from pathlib import Path
from typing import Dict, Tuple

import click

from bridgebots import DealRecord
from bridgebots_tools.csv_utilities import _get_headers, _write_results
from bridgebots_tools.data_extractors import (
    _extract_board_data,
    _generate_input_file_paths,
    _parse_results_file,
)
from bridgebots_tools.tools_logging import configure_logging


def _extract_team_dicts(deal_record: DealRecord, results_path: Path) -> Tuple[Dict, Dict]:
    """
    :param deal_record: a deal record with exactly two BoardRecords
    :param results_path: the path to the original lin/pbn file
    :return: A pair of open/closed room dictionaries for csv writing
    """
    if len(deal_record.board_records) != 2:
        raise ValueError(f"Invalid number of board records for a teams match: {len(deal_record.board_records)}")
    open_board, closed_board = deal_record.board_records[0], deal_record.board_records[1]
    return _extract_board_data(deal_record.deal, open_board, results_path), _extract_board_data(
        deal_record.deal, closed_board, results_path
    )


@click.command()
@click.option("--input_format", type=click.Choice(["lin", "pbn"], case_sensitive=False), default="lin")
@click.option("--output_format", type=click.Choice(["team", "individual"], case_sensitive=False), default="team")
@click.option("--verbose", "log_level", "-v", flag_value="verbose")
@click.option("--info", "log_level", flag_value="info", default=True)
@click.option("--quiet", "log_level", "-q", flag_value="quiet")
@click.argument("input_path", type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path))
@click.argument(
    "output_path", type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path), required=False
)
def report(input_format: str, output_format: str, log_level: str, input_path: Path, output_path: Path):
    configure_logging(log_level)
    results_file_paths = _generate_input_file_paths(input_format, input_path)
    csv_dicts = []
    for results_file_path in results_file_paths:
        deal_records = _parse_results_file(results_file_path, input_format)
        for deal_record in deal_records:
            try:
                if output_format == "team":
                    open_dict, closed_dict = _extract_team_dicts(deal_record, results_file_path)
                    prefix_dict = {f"o_{key}": value for key, value in open_dict.items()}
                    prefix_dict.update({f"c_{key}": value for key, value in closed_dict.items()})
                    csv_dicts.append(prefix_dict)
                else:
                    csv_dicts.extend(
                        [
                            _extract_board_data(deal_record.deal, board_record, results_file_path)
                            for board_record in deal_record.board_records
                        ]
                    )
            except (ValueError, IndexError) as e:
                logging.warning(f"Error processing deal:{deal_record}. Error:{e}")
    _write_results(output_path, csv_dicts, _get_headers(output_format))


if __name__ == "__main__":
    report()
