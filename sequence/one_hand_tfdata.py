from typing import List

import numpy as np
import tensorflow as tf
from numpy.typing import ArrayLike

from bridgebots import BoardRecord, DealRecord, Direction
from sequence.bridge_sequence_utils import (
    BIDDING_VOCAB,
    BIDDING_VOCAB_SIZE,
    BiddingExampleData,
    DealTarget,
    MAX_BIDDING_SEQUENCE,
    holding, numpy_holding,
)


class OneHandBiddingGenerator:
    def __init__(
        self,
        deal_records: List[DealRecord],
        deal_target: DealTarget = None,
        bidding_sequence_max_length: int = MAX_BIDDING_SEQUENCE,
    ):
        self.deal_records = deal_records
        self.deal_target = deal_target
        self.bidding_sequence_max_length = bidding_sequence_max_length

    def __call__(self):
        for deal_record in self.deal_records:
            dealer = deal_record.deal.dealer
            player_holdings = [numpy_holding(dealer.offset(i), deal_record) for i in range(4)]
            for board_record in deal_record.board_records:
                one_hot_bidding, one_hot_players, player_holdings, targets = self.generate_board_data(
                    deal_record, board_record, player_holdings
                )
                yield (one_hot_bidding, one_hot_players, player_holdings), targets

    def generate_board_data(self, deal_record: DealRecord, board_record: BoardRecord, holdings: List[ArrayLike]):
        sequences = []
        player_ids = []
        player_holdings = []
        bidding_record_indices = [BIDDING_VOCAB[bid] for bid in board_record.bidding_record]
        for i in range(0, len(bidding_record_indices)):
            player_ids.append(i % 4)
            player_holdings.append(holdings[i % 4])
            sequences.append(bidding_record_indices[0:i])

        targets = self.generate_targets(deal_record, board_record, sequences)

        padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
            sequences, padding="pre", maxlen=self.bidding_sequence_max_length, truncating="post"
        )
        one_hot_bidding = tf.keras.utils.to_categorical(padded_sequences, num_classes=BIDDING_VOCAB_SIZE)
        one_hot_players = tf.keras.utils.to_categorical(player_ids, num_classes=4)
        return one_hot_bidding, one_hot_players, np.array(player_holdings), targets

    def generate_targets(self, deal_record: DealRecord, board_record: BoardRecord, sequences):
        if self.deal_target:
            targets = self.deal_target.calculate(deal_record)
            return np.array([targets for s in sequences])
        raise ValueError("No target function")


class OneHandExampleGenerator:
    """Map DealRecords to TFRecords"""

    def __init__(self, deal_records: List[DealRecord], features: List, deal_targets: List):
        self.deal_targets = deal_targets
        self.deal_records = deal_records
        self.features = features

    def __iter__(self):
        for deal_record in self.deal_records:
            dealer = deal_record.deal.dealer
            player_holdings = {dealer.offset(i): holding(dealer.offset(i), deal_record) for i in range(4)}
            # deal targets do not change with each sequence so can be cached
            calculated_deal_targets = {
                type(deal_target).__name__: deal_target.calculate(deal_record) for deal_target in self.deal_targets
            }
            for board_record in deal_record.board_records:
                bidding_sequences = self.generate_bidding_sequences(dealer, board_record)
                for direction, bidding_sequence in bidding_sequences:
                    example_data = BiddingExampleData(
                        direction, bidding_sequence, deal_record, board_record, player_holdings
                    )
                    print(example_data)
                    yield self.build_example(example_data, calculated_deal_targets)

    def generate_bidding_sequences(self, dealer: Direction, board_record: BoardRecord):
        """Create each bidding subsequence in the bidding record. Keep the sequences in order but track which
        player's turn it was to act."""
        sequences = []
        for i in range(0, max(len(board_record.bidding_record), MAX_BIDDING_SEQUENCE)):
            sequences.append((dealer.offset(i), board_record.bidding_record[0:i]))
        return sequences

    def build_example(self, bidding_data: BiddingExampleData, calculated_deal_targets: List):
        feature_map = {type(feature).__name__: feature.calculate(bidding_data) for feature in self.features}
        feature_map.update(calculated_deal_targets)
        features = tf.train.Features(feature=feature_map)
        return tf.train.Example(features=features)
