import math
from abc import ABC, abstractmethod
from typing import List

import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import Sequence

from bridgebots import BoardRecord, Card, DealRecord, Direction, Rank, Suit
from bridgebots.bids import LEGAL_BIDS
from bridgebots.deal_utils import count_hcp
from sequence.bridge_sequence_utils import BIDDING_VOCAB, DealTarget, numpy_holding


class OneHandBiddingSequenceDataGenerator(Sequence):
    def __init__(
        self,
        batch_size: int,
        deal_records: List[DealRecord],
        deal_target: DealTarget = None,
        # bidding_training_data: List[BiddingTrainingData],
        bidding_sequence_length: int = 45,
        shuffle_on_epoch_end: bool = True,
        shuffle_on_start: bool = True,
    ):
        self.shuffle_on_epoch_end = shuffle_on_epoch_end
        self.bidding_sequence_length = bidding_sequence_length
        self.batch_size = batch_size
        self.deal_records = deal_records
        self.deal_target = deal_target
        # self.bidding_training_data = bidding_training_data
        self.data_indices = np.arange(len(deal_records))
        # self.bidding_vocab_size = len(BIDDING_VOCAB)
        self.rnd = np.random.RandomState(0)
        if shuffle_on_start:
            self.rnd.shuffle(self.data_indices)

    def __len__(self):
        return math.ceil(len(self.deal_records) / self.batch_size)

    def on_epoch_end(self) -> None:
        if self.shuffle_on_epoch_end:
            self.rnd.shuffle(self.data_indices)

    def __getitem__(self, batch_idx: int):
        batch_indices = self.data_indices[batch_idx * self.batch_size : (batch_idx + 1) * self.batch_size]
        batch_training_data = [self.deal_records[i] for i in batch_indices]
        batch_sequences = np.empty((0, self.bidding_sequence_length, len(BIDDING_VOCAB)))
        # batch_targets = np.empty((0, len(BIDDING_VOCAB)))
        batch_targets = np.empty((0, self.deal_target.shape()))
        batch_holdings = np.empty((0, 52))
        batch_players = np.empty((0, 4))

        for deal_record in batch_training_data:
            dealer = deal_record.deal.dealer
            player_holdings = {direction: numpy_holding(direction, deal_record) for direction in Direction}

            for board_record in deal_record.board_records:
                sequences, targets = self.generate_sequences_and_targets(deal_record, board_record)
                batch_sequences = np.concatenate((batch_sequences, sequences), axis=0)
                batch_targets = np.concatenate((batch_targets, targets), axis=0)
                board_players = []
                board_holdings = np.empty((0, 52))
                for offset in range(len(sequences)):
                    player = dealer.offset(offset)
                    board_players.append(offset % 4)
                    # one_hot_player = tf.keras.utils.to_categorical([player.value], num_classes=4)
                    # board_players.append(one_hot_player)
                    board_holdings = np.concatenate((board_holdings, player_holdings[player]), axis=0)
                    # board_holdings.append(player_holdings[player])
                one_hot_players = tf.keras.utils.to_categorical(board_players, num_classes=4)
                batch_players = np.concatenate((batch_players, one_hot_players), axis=0)
                batch_holdings = np.concatenate((batch_holdings, board_holdings), axis=0)

        return [batch_sequences, batch_holdings, batch_players], batch_targets
        # holdings
        # targets = self.generate_targets(sequences)

    def generate_sequences_and_targets(self, deal_record: DealRecord, board_record: BoardRecord):
        sequences = []
        bidding_record_indices = [BIDDING_VOCAB[bid] for bid in board_record.bidding_record]
        for i in range(0, len(bidding_record_indices)):
            sequences.append(bidding_record_indices[0:i])

        targets = self.generate_targets(deal_record, board_record, sequences)

        padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
            sequences, padding="pre", maxlen=self.bidding_sequence_length, truncating="post"
        )
        one_hot_bidding = tf.keras.utils.to_categorical(padded_sequences, num_classes=len(BIDDING_VOCAB))
        return one_hot_bidding, targets

    def generate_targets(self, deal_record: DealRecord, board_record: BoardRecord, sequences):
        if self.deal_target:
            targets = self.deal_target.calculate(deal_record)
            return [targets for s in sequences]
        raise ValueError("No target function")


# gen = OneHandBiddingSequenceDataGenerator(1, [], target_deal_function=hcp_targets)
