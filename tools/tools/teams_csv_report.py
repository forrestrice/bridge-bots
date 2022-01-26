import logging
from pathlib import Path

import click

from bridgebots import parse_multi_lin


def build_csv_dicts(deal_records):
    for deal_record in deal_records:
        print(len(deal_record.board_records))
    return []


@click.command()
# @click.option('--count', default=1, help='Number of greetings.')
@click.argument("lin_path", type=click.Path(exists=True, file_okay=True, path_type=Path))
def report(lin_path: Path):
    logging.basicConfig(level=logging.DEBUG)
    logging.info("running")
    csv_dicts = []
    lin_file_paths = []
    if lin_path.is_file():
        lin_file_paths.append(lin_path)
    elif lin_path.is_dir():
        lin_file_paths.extend(lin_path.rglob("*.lin"))

    for lin_file_path in lin_file_paths:
        deal_records = parse_multi_lin(lin_file_path)
        csv_dicts.extend(build_csv_dicts(deal_records))
        print(lin_file_path, len(deal_records))


if __name__ == "__main__":
    report()
