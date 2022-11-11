import sys
from pathlib import Path

import click

from bridgebots import build_lin_str
from bridgebots_tools.csv_report import _extract_team_dicts
from bridgebots_tools.csv_utilities import _get_headers, _write_results
from bridgebots_tools.data_extractors import _parse_results_file
from bridgebots_tools.tools_logging import configure_logging

_LINKS_CSV_HEADERS = ("board_id", "file", "o_link", "c_link")


@click.command()
@click.option("--input_format", type=click.Choice(["lin", "pbn"], case_sensitive=False), default="lin")
@click.option("--verbose", "log_level", "-v", flag_value="verbose")
@click.option("--info", "log_level", flag_value="info", default=True)
@click.option("--quiet", "log_level", "-q", flag_value="quiet")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.argument("file_name", type=str, required=True)
@click.argument("board", type=str, required=True)
@click.argument(
    "output_lin", type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path), required=False
)
@click.argument(
    "output_csv", type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path), required=False
)
def report(
    input_format: str,
    log_level: str,
    input_dir: Path,
    file_name: str,
    board: str,
    output_lin: Path,
    output_csv: Path,
):
    configure_logging(log_level)
    input_path = next(input_dir.rglob(file_name))

    deal_records = _parse_results_file(input_path, input_format)
    csv_dicts = []
    for deal_record in deal_records:
        if "o" + board in [board_record.board_name for board_record in deal_record.board_records]:
            # Write one instance of the board to the LIN file (or stdout)
            board_record = deal_record.board_records[0]
            lin_output = build_lin_str(deal_record.deal, board_record, lin_type="multi")
            output_handle = open(output_lin, "a") if output_lin else sys.stdout
            try:
                output_handle.write(lin_output + "\n")
            finally:
                if output_lin:
                    output_handle.close()
            # Now collect CSV information from the open and closed rooms
            open_dict, closed_dict = _extract_team_dicts(deal_record, input_path)
            prefix_dict = {f"o_{key}": value for key, value in open_dict.items()}
            prefix_dict.update({f"c_{key}": value for key, value in closed_dict.items()})
            csv_dicts.append(prefix_dict)

    # Write CSV to file (or stdout)
    _write_results(output_csv, csv_dicts, _get_headers(output_format="team"))


if __name__ == "__main__":
    report()
