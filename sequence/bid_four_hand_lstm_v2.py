import pickle
from typing import List

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.python.keras import Input, Model
from tensorflow.python.keras.layers import Dense

from sequence.bidding_training_data import BiddingSequenceDataGenerator, BiddingTrainingData
from train.bridge_training_utils import bidding_vocab


def build_lstm_model(sequence_length: int, vocab_size: int):
    input_layer = Input(shape=(sequence_length, vocab_size))
    x = tf.keras.layers.LSTM(128)(input_layer)
    output_layer = tf.keras.layers.Dense(len(bidding_vocab))(x)
    return Model(inputs=input_layer, outputs=output_layer)


def build_lstm_model_with_holding(sequence_length: int, vocab_size: int):
    bidding_input_layer = Input(shape=(sequence_length, vocab_size))
    lstm_output = tf.keras.layers.LSTM(128)(bidding_input_layer)

    holding_input_layer = Input(shape=(52 * 4))
    h = Dense(104, "selu")(holding_input_layer)
    h = Dense(52, "selu")(h)
    holding_output = Dense(26, "selu")(h)

    x = layers.concatenate([lstm_output, holding_output])
    output_layer = tf.keras.layers.Dense(len(bidding_vocab))(x)
    return Model(inputs=[bidding_input_layer, holding_input_layer], outputs=output_layer)


def build_lstm_model_v3(sequence_length: int, vocab_size: int):
    bidding_input_layer = Input(shape=(sequence_length, vocab_size))
    lstm_outputs, state_h, state_c = tf.keras.layers.LSTM(units=128, return_state=True)(bidding_input_layer)

    holding_input_layer = Input(shape=(52 * 4))

    x = layers.concatenate([lstm_outputs, state_c, holding_input_layer])
    x = Dense(256, "selu")(x)
    x = Dense(128, "selu")(x)
    x = Dense(64, "selu")(x)
    output_layer = tf.keras.layers.Dense(len(bidding_vocab))(x)
    return Model(inputs=[bidding_input_layer, holding_input_layer], outputs=output_layer)


bid_learn_prefix = "/Users/frice/bridge/bid_learn/"
with open(bid_learn_prefix + "TRAIN.pickle", "rb") as pickle_file:
    bidding_training_data: List[BiddingTrainingData] = pickle.load(pickle_file)

print(len(bidding_training_data))
data_generator = BiddingSequenceDataGenerator(20, bidding_training_data)

bid_lstm_model = build_lstm_model_v3(sequence_length=45, vocab_size=len(bidding_vocab))

bid_lstm_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    metrics="accuracy",
)

bid_lstm_model.fit(data_generator, epochs=10)
bid_lstm_model.save(bid_learn_prefix + "lstm_model_v3")
