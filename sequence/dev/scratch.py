import pickle
from collections import defaultdict
from pathlib import Path
from typing import List

from bridgebots import DealRecord

all_deals_pickle = Path("/Users/frice/bridge/vugraph_project/all_deals.pickle")

with open(all_deals_pickle, "rb") as pickle_file:
    deal_records: List[DealRecord] = pickle.load(pickle_file)

bidding_length_frequency = defaultdict(int)

for deal_record in deal_records:
    for board_record in deal_record.board_records:
        bidding_length_frequency[str(len(board_record.bidding_record))] += 1


for bidding_len, frequency in sorted(bidding_length_frequency.items(), key=lambda x: int(x[0])):
    print(bidding_len, frequency)
