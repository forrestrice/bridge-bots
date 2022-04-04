import csv
import sys
from pathlib import Path

import sys
from pathlib import Path

import click

from bridgebots import build_lin_str, build_lin_url
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

    csv_dict = {"board_id": board, "file": input_path.name}
    deal_records = _parse_results_file(input_path, input_format)
    for deal_record in deal_records:
        for board_record in deal_record.board_records:
            # Write one instance of the board to the LIN file (or stdout)
            if board_record.board_name in ["o" + board]:
                lin_output = build_lin_str(deal_record.deal, board_record, lin_type="multi")
                output_handle = open(output_lin, "a") if output_lin else sys.stdout
                try:
                    output_handle.write(lin_output + "\n")
                finally:
                    if output_lin:
                        output_handle.close()
            # Add both LIN links to the CSV dict
            if board_record.board_name in ["c" + board, "o" + board]:
                lin_url = build_lin_url(deal_record.deal, board_record)
                link_key = "c_link" if board_record.board_name.startswith("c") else "o_link"
                csv_dict[link_key] = lin_url

    # Write CSV to file (or stdout)
    output_csv_exists = output_csv is not None and output_csv.exists()
    output_handle = open(output_csv, "a") if output_csv else sys.stdout
    try:
        writer = csv.DictWriter(output_handle, fieldnames=_LINKS_CSV_HEADERS, extrasaction="ignore")
        if not output_csv_exists:
            writer.writeheader()
        writer.writerow(csv_dict)

    finally:
        if output_csv:
            output_handle.close()


if __name__ == "__main__":
    report()
