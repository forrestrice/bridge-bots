import logging
import pickle
import random
from typing import Dict, List

import numpy as np

from bridge.deal import Deal
from bridge.table_record import TableRecord
from sequence.bidding_training_data import BiddingTrainingData
from train.bridge_training_utils import bidding_vocab, canonicalize_bid, sorted_cards


def build_bidding_indices(table_record: TableRecord) -> List[int]:
    bidding_indices = []
    for bid in table_record.bidding_record:
        if bid[0] in ["=", "!", "$"]:
            continue
        bidding_indices.append(bidding_vocab[canonicalize_bid(bid)])
    bidding_indices.append(bidding_vocab["EOS"])
    return bidding_indices


def build_holding_array(deal: Deal) -> np.ndarray:
    holding_array = np.zeros((1, 52 * 4))
    direction = deal.dealer
    for di in range(0, 4):
        direction_cards = deal.player_cards[direction]
        for ci, card in enumerate(sorted_cards):
            if card in direction_cards:
                holding_array[0, 52 * di + ci] = 1
        direction = direction.next()
    return holding_array


pickle_file_path = "/Users/frice/bridge/results/major_tournaments_pbn.pickle"
with open(pickle_file_path, "rb") as pickle_file:
    deal_records: Dict[Deal, List[TableRecord]] = pickle.load(pickle_file)

print(f"processing {len(deal_records)} records")

splits = [("TRAIN", []), ("VALIDATION", []), ("TEST", [])]
split_weights = [0.8, 0.1, 0.1]

# ensure deals are always in the same split
for deal, table_records in deal_records.items():
    split_name, training_data_list = random.choices(splits, split_weights)[0]
    try:
        holding_array = build_holding_array(deal)
    except KeyError as e:
        logging.warning(f"Skipping invalid holding: {deal.hands}")
        continue

    for table_record in table_records:
        if len(table_record.bidding_record) == 0:
            continue
        try:
            bidding_indices = build_bidding_indices(table_record)
        except KeyError as e:
            logging.warning(f"Skipping invalid bidding sequence: {table_record.bidding_record}, {e}")
            continue
        training_data_list.append(BiddingTrainingData(bidding_indices, holding_array))

save_prefix = "/Users/frice/bridge/bid_learn/"
for name, training_data_list in splits:
    print(name)
    print(f"samples: {len(training_data_list)}")
    with open(save_prefix + name + ".pickle", "wb") as pickle_file:
        pickle.dump(training_data_list, pickle_file)
