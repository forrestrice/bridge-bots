from pathlib import Path

from parse.pbn import parse_pbn

all_results = []
for results_path in Path('/Users/frice/bridge/results/usbc').rglob('*.pbn'):
    print(results_path)
    file_results = parse_pbn(results_path)
    all_results.extend(file_results)
    print(f'extracted {len(file_results)} results from {results_path}')


print(len(all_results))
