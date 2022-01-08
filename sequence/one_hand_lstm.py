import pickle
from pathlib import Path

import tensorflow as tf
from keras.layers import Dense, LSTM
from tensorflow.keras import Input, Model, layers

from sequence.bridge_sequence_utils import BIDDING_VOCAB_SIZE, HcpDealTarget
from sequence.one_hand_bidding_training_data import OneHandBiddingSequenceDataGenerator

bid_learn_prefix = Path("/Users/frice/bridge/bid_learn/one_hand/")
training_path = bid_learn_prefix / "TRAIN.pickle"
with open(training_path, "rb") as training_file:
    deal_records = pickle.load(training_file)
    print(len(deal_records))

deal_target = HcpDealTarget()
data_generator = OneHandBiddingSequenceDataGenerator(50, deal_records, deal_target=deal_target)


def build_lstm_model(sequence_length: int, output_shape: int):
    bidding_input_layer = Input(shape=(sequence_length, BIDDING_VOCAB_SIZE))
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True)(bidding_input_layer)

    holding_input_layer = Input(shape=52)
    player_input_layer = Input(shape=4)

    # x = layers.concatenate([lstm_outputs, state_c, holding_input_layer])
    x = layers.concatenate([lstm_outputs, holding_input_layer, player_input_layer])
    x = Dense(256, "selu")(x)
    x = Dense(128, "selu")(x)
    x = Dense(64, "selu")(x)
    output_layer = tf.keras.layers.Dense(output_shape)(x)
    return Model(inputs=[bidding_input_layer, holding_input_layer, player_input_layer], outputs=output_layer)


bid_lstm_model = build_lstm_model(sequence_length=45, output_shape=deal_target.shape())
bid_lstm_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.MeanSquaredError(),
    # loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    metrics=["accuracy", "mae", "mse"],
)

bid_lstm_model.fit(data_generator, epochs=1)
bid_lstm_model.save(bid_learn_prefix / "lstm_hcp_1_epochs")
