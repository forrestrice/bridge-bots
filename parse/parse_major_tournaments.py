import logging
from pathlib import Path

from parse.pbn import parse_pbn

logging.basicConfig(level=logging.DEBUG)

all_results = []
for results_path in Path('/Users/frice/bridge/results/').rglob('*.pbn'):
    print(results_path)
    file_results = parse_pbn(results_path)
    all_results.extend(file_results)
    print(f'extracted {len(file_results)} results from {results_path}')


print(len(all_results))
