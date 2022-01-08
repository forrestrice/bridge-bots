import pickle
from collections import Counter
from typing import List

from bridgebots import DealRecord

def toy():
    names = ["hello", "goodbye"]


def inspect():
    counter = Counter()
    pickle_file_path = "/Users/frice/bridge/vugraph_project/all_deals.pickle"
    with open(pickle_file_path, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    for i, deal_record in enumerate(deal_records):
        if i % 1_000 == 0 and i > 0:
            print(f"processed {i} records")
        for board_record in deal_record.board_records:
            counter.update(board_record.names.values())

    print(counter.most_common(1000))


def inspect_sequence_lengths():
    counter = Counter()
    pickle_file_path = "/Users/frice/bridge/vugraph_project/all_deals.pickle"
    with open(pickle_file_path, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    for i, deal_record in enumerate(deal_records):
        if i % 1_000 == 0 and i > 0:
            print(f"processed {i} records")
        for board_record in deal_record.board_records:
            counter.update({str(len(board_record.bidding_record)): 1})

    print(counter.most_common(1000))

inspect_sequence_lengths()
