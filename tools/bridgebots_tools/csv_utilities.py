# This list can be reordered or items can be removed to modify the output columns
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List

_CSV_HEADERS = (
    "board_id",
    "file",
    "deal_hash",
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
    "competitive",
    "declarer",
    "contract",
    "lead",
    "result",
    "tricks",
    "score_ns",
    "score_ew",
    "score_declarer",
    "score_defender",
    "link",
    "declarer_shape",
    "dummy_shape",
    "lho_shape",
    "rho_shape",
    "declarer_hcp",
    "dummy_hcp",
    "lho_hcp",
    "rho_hcp",
    "trump_fit",
    "trump_hcp")

_PREFIX_CSV_HEADERS = [f"o_{header}" for header in _CSV_HEADERS] + [f"c_{header}" for header in _CSV_HEADERS]


def _get_headers(output_format: str):
    return _PREFIX_CSV_HEADERS if output_format == "team" else _CSV_HEADERS


def _write_results(csv_path: Path, csv_dicts: List[Dict], headers: List[str] = _CSV_HEADERS):
    """
    Write csv_dicts to csv_path using the supplied headers
    """
    logging.debug(f"Writing {len(csv_dicts)} deals to {csv_path}")
    output_handle = open(csv_path, "w") if csv_path else sys.stdout
    try:
        writer = csv.DictWriter(output_handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for csv_dict in csv_dicts:
            writer.writerow(csv_dict)
    finally:
        if csv_path:
            output_handle.close()
