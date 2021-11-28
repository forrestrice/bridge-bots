import logging
import pickle
from collections import defaultdict
from pathlib import Path

from bridgebots.board_record import DealRecord
from bridgebots.pbn import parse_pbn

logging.basicConfig(level=logging.DEBUG)

all_results = []
for results_path in Path("/Users/frice/bridge/results/").rglob("*.pbn"):
    file_results = parse_pbn(results_path)
    all_results.extend(file_results)
    logging.debug(f"extracted {len(file_results)} results from {results_path}")

logging.info(f"{len(all_results)} total results")

# Deduplicate deals, collecting all boards to a list
deal_dict = defaultdict(set)
for deal_record in all_results:
    deal_dict[deal_record.deal] |= set(deal_record.board_records)

deduped_results = [DealRecord(deal, list(board_records)) for deal, board_records in deal_dict.items()]

pickle_file_path = "/Users/frice/bridge/results/major_tournaments_pbn.pickle"
with open(pickle_file_path, "wb") as pickle_file:
    pickle.dump(deduped_results, pickle_file)

board_record_count = sum(len(deal_record.board_records) for deal_record in deduped_results)
logging.info(f"wrote {len(deduped_results)} deals with {board_record_count} board records to {pickle_file_path}")
