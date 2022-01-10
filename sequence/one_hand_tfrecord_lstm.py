import tensorflow as tf
from keras import Input
from keras.layers import Dense, LSTM
from tensorflow.keras import Input, Model, layers

from sequence.bridge_sequence_utils import (
    BIDDING_VOCAB_SIZE,
    BiddingIndices,
    HcpTarget,
    Holding,
    MAX_BIDDING_SEQUENCE,
    PlayerPosition,
)


def build_schema(features, deal_targets):
    schema = {type(feature).__name__: feature.schema() for feature in features}
    schema.update({type(target).__name__: target.schema() for target in deal_targets})
    return schema


def decode_fn(record_bytes):
    print(f"record_bytes={record_bytes}")
    features = [PlayerPosition(), Holding(), BiddingIndices()]
    deal_targets = [HcpTarget()]
    schema = build_schema(features, deal_targets)
    print(schema)
    """
        {
            "BiddingIndices": tf.io.VarLenFeature(dtype=tf.int64),
            "HcpTarget": tf.io.FixedLenFeature([4], dtype=tf.int64),
            "Holding": tf.io.FixedLenFeature([52], dtype=tf.int64),
            "PlayerPosition": tf.io.FixedLenFeature([], dtype=tf.int64),
        }
    """
    return tf.io.parse_single_example(
        # Data
        record_bytes,
        # Schema
        # {"x": tf.io.FixedLenFeature([], dtype=tf.float32), "y": tf.io.FixedLenFeature([], dtype=tf.float32)},
        schema,
    )


filename = "/Users/frice/bridge/bid_learn/one_hand/toy/train.tfrecords"

tf_record_dataset = tf.data.TFRecordDataset([filename])
# for example in tf_record_dataset:
# print(example)
#    break
decoded_dataset = tf_record_dataset.map(decode_fn)
for example in decoded_dataset:
    pass
    # print("mapped:")
    # print(example)


def prepare_sequence(bidding_example):
    bidding_indices = bidding_example["BiddingIndices"]

    tf.print("bidding_indices:", bidding_indices)
    print(bidding_indices)
    padded_sequence = tf.keras.preprocessing.sequence.pad_sequences(
        bidding_indices, padding="pre", maxlen=MAX_BIDDING_SEQUENCE, truncating="post"
    )
    one_hot_bidding = tf.keras.utils.to_categorical(padded_sequence, num_classes=BIDDING_VOCAB_SIZE)
    one_hot_players = tf.keras.utils.to_categorical(bidding_example["PlayerPosition"], num_classes=4)
    return (one_hot_bidding, one_hot_players, bidding_example["Holding"]), bidding_example["HcpTarget"]


"""
prepared_dataset = decoded_dataset.map(prepare_sequence)
for prepared in prepared_dataset:
    print("prepared:\n", prepared)
"""


def sparse_bidding_to_dense(bidding_example):
    bidding_indices = bidding_example["BiddingIndices"]
    bidding_example["BiddingIndices"] = tf.sparse.to_dense(bidding_indices)
    return bidding_example


dense_dataset = decoded_dataset.map(sparse_bidding_to_dense)
dense_count = 0
for entry in dense_dataset:
    print(entry)
    print(type(entry))
    dense_count += 1
    if dense_count > 30:
        break

padded_dataset = dense_dataset.padded_batch(
    10,
    padded_shapes={"BiddingIndices": [MAX_BIDDING_SEQUENCE], "HcpTarget": (4,), "Holding": (52,), "PlayerPosition": ()},
)

for padded_batch in padded_dataset:
    print("PADDED BATCH:")
    print(type(padded_batch))
    print(padded_batch)
    break

def make_categorical(bidding_example):
    one_hot_bidding = tf.one_hot(bidding_example["BiddingIndices"], BIDDING_VOCAB_SIZE)
    bidding_example["BiddingIndices"] = one_hot_bidding
    one_hot_player = tf.one_hot(bidding_example["PlayerPosition"], 4)
    bidding_example["PlayerPosition"] = one_hot_player
    return bidding_example

one_hot_dataset = padded_dataset.map(make_categorical)
for cat_batch in one_hot_dataset:
    print(cat_batch)
    break

def build_lstm_model(output_shape: int, sequence_length: int = MAX_BIDDING_SEQUENCE):
    bidding_input_layer = Input(shape=(sequence_length, BIDDING_VOCAB_SIZE), name="BiddingIndices")
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True)(bidding_input_layer)

    player_input_layer = Input(shape=(4), name="PlayerPosition")
    holding_input_layer = Input(shape=(52), name="Holding")

    # consider including cell state
    # x = layers.concatenate([lstm_outputs, state_c, holding_input_layer])
    x = layers.concatenate([lstm_outputs, holding_input_layer, player_input_layer])
    x = Dense(256, "selu")(x)
    x = Dense(128, "selu")(x)
    x = Dense(64, "selu")(x)
    output_layer = tf.keras.layers.Dense(output_shape)(x)
    return Model(inputs=[bidding_input_layer, player_input_layer, holding_input_layer], outputs=output_layer)


bid_lstm_model = build_lstm_model(output_shape=4)
bid_lstm_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.MeanSquaredError(),
    metrics=["mae", "mse"],
)

def split_targets(bidding_example):
    target = bidding_example["HcpTarget"]
    return (bidding_example, target)


bid_lstm_model.fit(one_hot_dataset.map(split_targets), epochs=1)
#bid_lstm_model.save(bid_learn_prefix / "tfdata_lstm_hcp_1_epochs")
"""
some_bytes= b'\n\x8b\x01\n\x14\n\x0eBiddingIndices\x12\x02\x1a\x00\n\x17\n\x0ePlayerPosition\x12\x05\x1a\x03\n\x01\x00\n\x15\n\tHcpTarget\x12\x08\x1a\x06\n\x04\x05\x0c\t\x0e\nC\n\x07Holding\x128\x1a6\n4\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x01\x00\x01\x01\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x01\x00\x01\x01\x00\x00'
example = tf.io.parse_single_example(some_bytes,         {"BiddingIndices":tf.io.VarLenFeature(dtype=tf.int64),
         "HcpTarget":tf.io.FixedLenFeature([], dtype=tf.int64, default_value=0),
         "Holding":tf.io.FixedLenFeature([], dtype=tf.int64),
         "PlayerPosition":tf.io.FixedLenFeature([], dtype=tf.int64),
         })
"""
"""
tf_record_dataset = tf.data.TFRecordDataset([filename])
print(example)
"""
