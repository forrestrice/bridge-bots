import logging
import pickle
import random
from typing import Dict, List

import numpy as np
import tensorflow as tf

from deal.deal import Deal
from deal.table_record import TableRecord
from train.bridge_training_utils import bidding_vocab, canonicalize_bid, sorted_cards

SEQUENCE_LENGTH = 40


def build_bidding_indices(table_record: TableRecord) -> np.ndarray:
    bidding_indices = np.zeros((1, SEQUENCE_LENGTH))
    i = 0
    for bid in table_record.bidding_record:
        if bid[0] in ['=', '!', '$']:
            continue
        bidding_indices[0, i] = bidding_vocab[canonicalize_bid(bid)]
        i += 1
    bidding_indices[0, i] = bidding_vocab['EOS']
    bidding_indices[0, i + 1:] = bidding_vocab['PAD']
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


pickle_file_path = '/Users/frice/bridge/results/major_tournaments_pbn.pickle'
with open(pickle_file_path, "rb") as pickle_file:
    deal_records: Dict[Deal, List[TableRecord]] = pickle.load(pickle_file)

print(f'processing {len(deal_records)} records')

splits = [('TRAIN', [], []), ('VALIDATION', [], []), ('TEST', [], [])]
# splits = [('TRAIN', []), ('VALIDATION', []), ('TEST', [])]
split_weights = [0.8, 0.1, 0.1]

# ensure deals are always in the same split
for deal, table_records in deal_records.items():
    split_name, holding_arrays, bidding_sequences = random.choices(splits, split_weights)[0]
    try:
        holding_array = build_holding_array(deal)
    except KeyError as e:
        logging.warning(f'Skipping invalid holding: {deal.hands}')
        continue

    # tiled_holding_array = np.tile(holding_array, (1, SEQUENCE_LENGTH, 1))
    for table_record in table_records:
        if len(table_record.bidding_record) == 0:
            continue
        try:
            bidding_indices = build_bidding_indices(table_record)
        except KeyError as e:
            logging.warning(f'Skipping invalid bidding sequence: {table_record.bidding_record}, {e}')
            continue
        one_hot_bidding = tf.keras.utils.to_categorical(bidding_indices, num_classes=len(bidding_vocab))

        # model_input = np.concatenate((one_hot_bidding, tiled_holding_array), axis=2)
        # X.append(model_input)
        # y.append(one_hot_bidding)
        holding_arrays.append(holding_array)
        bidding_sequences.append(one_hot_bidding)

save_prefix = '/Users/frice/bridge/bid_learn/'
for name, holding_arrays, bidding_sequences in splits:
    print(name)
    print(f'samples: holdings {len(holding_arrays)} bid sequences: {len(bidding_sequences)}')
    holding_combined = np.squeeze(np.asarray(holding_arrays))
    bidding_sequences_combined = np.squeeze(np.asarray(bidding_sequences))
    print(
        f'holding_combined.shape={holding_combined.shape}, '
        f'bidding_sequences_combined.shape={bidding_sequences_combined.shape}')
    np.save(save_prefix + name + '_HOLDING', holding_combined)
    np.save(save_prefix + name + '_BID_SEQUENCE', bidding_sequences_combined)

'''
for name, X, y in splits:
    print(name)
    print(f'samples: {len(X)}')
    X_array = np.squeeze(np.asarray(X))
    y_array = np.squeeze(np.asarray(y))
    print(f'X_array.shape={X_array.shape}, y_array.shape={y_array.shape}')
    np.save(save_prefix + name + '_X', X_array)
    np.save(save_prefix + name + '_y', y_array)
'''
