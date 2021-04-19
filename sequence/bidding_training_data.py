import math
from typing import List

import numpy as np
import tensorflow as tf
from tensorflow.python.keras.utils.data_utils import Sequence

from train.bridge_training_utils import BIDDING_VOCAB


class BiddingTrainingData:
    def __init__(self, bidding_indices: List[int], holding_array: np.ndarray):
        self.bidding_indices = bidding_indices
        self.holding_array = holding_array


class BiddingSequenceDataGenerator(Sequence):
    def __init__(
        self,
        batch_size: int,
        bidding_training_data: List[BiddingTrainingData],
        bidding_sequence_length: int = 45,
        shuffle_on_epoch_end: bool = True,
        shuffle_on_start: bool = True,
    ):
        self.shuffle_on_epoch_end = shuffle_on_epoch_end
        self.bidding_sequence_length = bidding_sequence_length
        self.batch_size = batch_size
        self.bidding_training_data = bidding_training_data
        self.data_indices = np.arange(len(bidding_training_data))
        self.bidding_vocab_size = len(BIDDING_VOCAB)
        self.rnd = np.random.RandomState(0)
        if shuffle_on_start:
            self.rnd.shuffle(self.data_indices)

    def __len__(self):
        return math.ceil(len(self.bidding_training_data) / self.batch_size)

    def __getitem__(self, batch_idx: int):
        batch_indices = self.data_indices[batch_idx * self.batch_size : (batch_idx + 1) * self.batch_size]
        batch_training_data = [self.bidding_training_data[i] for i in batch_indices]
        batch_sequences = np.empty((0, self.bidding_sequence_length, self.bidding_vocab_size))
        batch_targets = np.empty((0, self.bidding_vocab_size))
        batch_holdings = np.empty((0, 52 * 4))
        for single_training_data in batch_training_data:
            sequences, targets = self.generate_sequences_and_targets(single_training_data)
            batch_sequences = np.concatenate((batch_sequences, sequences), axis=0)
            batch_targets = np.concatenate((batch_targets, targets), axis=0)
            tiled_holdings = np.tile(single_training_data.holding_array, (len(sequences), 1))
            batch_holdings = np.concatenate((batch_holdings, tiled_holdings), axis=0)

        return [batch_sequences, batch_holdings], batch_targets

    def on_epoch_end(self) -> None:
        """ Reshuffle data on epoch end """
        if self.shuffle_on_epoch_end:
            self.rnd.shuffle(self.data_indices)

    def generate_sequences_and_targets(self, data_sample: BiddingTrainingData):
        sequences = []
        targets = []
        for i in range(len(data_sample.bidding_indices)):
            sequences.append(data_sample.bidding_indices[0:i])
            targets.append(data_sample.bidding_indices[i])

        padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
            sequences, padding="pre", maxlen=self.bidding_sequence_length, truncating="post"
        )
        one_hot_bidding = tf.keras.utils.to_categorical(padded_sequences, num_classes=self.bidding_vocab_size)
        one_hot_targets = tf.keras.utils.to_categorical(targets, num_classes=self.bidding_vocab_size)
        return one_hot_bidding, one_hot_targets
