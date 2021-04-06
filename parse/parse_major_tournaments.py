import logging
import pickle
from collections import defaultdict
from pathlib import Path

from parse.pbn import parse_pbn

logging.basicConfig(level=logging.WARNING)


all_results = []
for results_path in Path('/Users/frice/bridge/results/').rglob('*.pbn'):
    file_results = parse_pbn(results_path)
    all_results.extend(file_results)
    logging.debug(f'extracted {len(file_results)} results from {results_path}')

logging.info(f'{len(all_results)} total results')

deal_dict = defaultdict(list)
for deal, table_record in all_results:
    deal_dict[deal].append(table_record)

pickle_file_path = '/Users/frice/bridge/results/major_tournaments_pbn.pickle'
with open(pickle_file_path, "wb") as pickle_file:
    pickle.dump(deal_dict, pickle_file)

logging.info(f'wrote {len(deal_dict)} deals to {pickle_file_path}')
