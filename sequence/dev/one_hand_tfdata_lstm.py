import pickle
from pathlib import Path

import tensorflow as tf
from keras import Input
from keras.layers import Dense, LSTM
from tensorflow.keras import Input, Model, layers

from sequence.dev.bridge_sequence_utils import BIDDING_VOCAB_SIZE, HcpDealTarget, MAX_BIDDING_SEQUENCE
from sequence.dev.one_hand_tfdata import OneHandBiddingGenerator

bid_learn_prefix = Path("/Users/frice/bridge/bid_learn/one_hand/toy")
training_path = bid_learn_prefix / "TRAIN.pickle"
with open(training_path, "rb") as training_file:
    deal_records = pickle.load(training_file)
    print(f"loaded {len(deal_records)} deal records")

target = HcpDealTarget()
data_gen = OneHandBiddingGenerator(deal_records, target)

bid_dataset = tf.data.Dataset.from_generator(
    data_gen,
    output_signature=(
        (
            tf.TensorSpec(shape=(None, MAX_BIDDING_SEQUENCE, BIDDING_VOCAB_SIZE), dtype=tf.float32),  # bidding
            tf.TensorSpec(shape=(None, 4), dtype=tf.float32),  # 4 players
            tf.TensorSpec(shape=(None, 52), dtype=tf.float32),  # player holding
        ),
        tf.TensorSpec(shape=(None, target.shape()), dtype=tf.float32),  # targets
    ),
)
# shuffle, repeat, preftech, batch
num_examples = sum((len(deal_record.board_records) for deal_record in deal_records))
performance_dataset = (
    bid_dataset.shuffle(num_examples, reshuffle_each_iteration=True).batch(2).prefetch(tf.data.AUTOTUNE)
    #bid_dataset.shuffle(num_examples, reshuffle_each_iteration=True).batch(50).prefetch(tf.data.AUTOTUNE)
)

print(list(performance_dataset.as_numpy_iterator()))
exit()

def build_lstm_model(output_shape: int, sequence_length: int = MAX_BIDDING_SEQUENCE):
    bidding_input_layer = Input(shape=(sequence_length, BIDDING_VOCAB_SIZE))
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True)(bidding_input_layer)

    player_input_layer = Input(shape=(4))
    holding_input_layer = Input(shape=(52))

    # consider including cell state
    # x = layers.concatenate([lstm_outputs, state_c, holding_input_layer])
    x = layers.concatenate([lstm_outputs, holding_input_layer, player_input_layer])
    x = Dense(256, "selu")(x)
    x = Dense(128, "selu")(x)
    x = Dense(64, "selu")(x)
    output_layer = tf.keras.layers.Dense(output_shape)(x)
    return Model(inputs=[bidding_input_layer, player_input_layer, holding_input_layer], outputs=output_layer)


bid_lstm_model = build_lstm_model(output_shape=target.shape())
bid_lstm_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.MeanSquaredError(),
    metrics=["mae", "mse"],
)

bid_lstm_model.fit(performance_dataset, epochs=1)
bid_lstm_model.save(bid_learn_prefix / "tfdata_lstm_hcp_1_epochs")
