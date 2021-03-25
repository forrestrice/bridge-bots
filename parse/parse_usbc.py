from pathlib import Path

from parse.pbn import split_pbn

split_records = split_pbn(Path('/Users/frice/bridge/results/usbc/usbc_2012.pbn'))
print(len(split_records))
print(split_records[3])
