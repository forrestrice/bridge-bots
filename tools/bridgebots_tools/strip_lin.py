import sys
from pathlib import Path

import click

from bridgebots import build_lin_str, parse_multi_lin
from bridgebots.lin import LinType


@click.command()
@click.argument("input_file", type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
@click.argument(
    "output_file", type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path), required=False
)
def strip_lin(input_file: Path, output_file: Path):
    deal_records = parse_multi_lin(input_file)

    # Write boards to file (or stdout)
    output_handle = open(output_file, "a") if output_file else sys.stdout
    try:
        for deal_record in deal_records:
            for board_record in deal_record.board_records:
                output_handle.write(build_lin_str(deal_record.deal, board_record, LinType.MULTI))
                output_handle.write("\n")
    finally:
        if output_file:
            output_handle.close()


if __name__ == "__main__":
    strip_lin()
