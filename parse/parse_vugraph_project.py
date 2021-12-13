import logging
import pickle
from collections import defaultdict
from pathlib import Path

from bridgebots import DealRecord, parse_multi_lin

logging.basicConfig(level=logging.DEBUG)

# /Users/frice/bridge/vugraph_project/www.sarantakos.com/bridge/vugraph/2013/nec/rr10b.lin
# "/Users/frice/bridge/vugraph_project/"
#test_path="/Users/frice/bridge/vugraph_project/www.sarantakos.com/bridge/vugraph/2015/wbc/rr134.lin"
#parse_multi_lin(Path(test_path))
all_results = []
for results_path in Path("/Users/frice/bridge/vugraph_project/").rglob(
    "*.lin"
):
    logging.debug(f"results_path: {str(results_path)}")
    try:
        file_results = parse_multi_lin(results_path)
        all_results.extend(file_results)
        logging.debug(f"extracted {len(file_results)} results from {results_path}")
    except UnicodeError as e:
        logging.error(e)

logging.info(f"{len(all_results)} total results")

# Deduplicate deals, collecting all boards to a set
deal_dict = defaultdict(set)
for deal_record in all_results:
    deal_dict[deal_record.deal] |= set(deal_record.board_records)

deduped_results = [DealRecord(deal, list(board_records)) for deal, board_records in deal_dict.items()]

pickle_file_path = "/Users/frice/bridge/vugraph_project/all_deals.pickle"
with open(pickle_file_path, "wb") as pickle_file:
    pickle.dump(deduped_results, pickle_file)

board_record_count = sum(len(deal_record.board_records) for deal_record in deduped_results)
logging.info(f"wrote {len(deduped_results)} deals with {board_record_count} board records to {pickle_file_path}")
