import tensorflow as tf
from keras import Input
from keras.layers import Dense, LSTM
from tensorflow.keras import Input, Model, layers

from sequence.bridge_sequence_utils import BIDDING_VOCAB_SIZE, MAX_BIDDING_SEQUENCE

filename = "/Users/frice/bridge/bid_learn/one_hand/sequence_train.tfrecords"


def decode_fn(record_bytes):
    return tf.io.parse_single_sequence_example(
        record_bytes,
        context_features={"HcpTarget": tf.io.FixedLenFeature([4], dtype=tf.int64)},
        sequence_features={
            "BiddingIndicesSequence": tf.io.FixedLenSequenceFeature([1], dtype=tf.int64),
            "HoldingSequence": tf.io.FixedLenSequenceFeature([52], dtype=tf.int64),
            "PlayerPositionSequence": tf.io.FixedLenSequenceFeature([1], dtype=tf.int64),
        },
    )


tf_record_dataset = tf.data.TFRecordDataset([filename])

decoded_dataset = tf_record_dataset.map(decode_fn)
for example in decoded_dataset:
    # print(example)
    break


@tf.function
def create_subsequences(context, sequences):
    #tf.print("context", context, type(context))
    #tf.print("bidding", sequences["BiddingIndicesSequence"], type(sequences["BiddingIndicesSequence"]))
    bidding = sequences["BiddingIndicesSequence"]
    subsequences = []
    for i in range(len(bidding)):
        bidding_subsequence = bidding[0:i]
        #tf.print("bidding_subsequence", bidding_subsequence)
        subsequences.append(bidding_subsequence)
        # dataset = tf.data.Dataset.from_tensor_slices(bidding_subsequence)
        # tf.print("dataset", dataset)
        # datasets.append(tf.data.Dataset.from_tensor_slices(bidding_subsequence))

    sequences["training_sequences"] = subsequences

    return tf.data.Dataset.from_tensor_slices(sequences)


@tf.function
def create_subsequences_smart(context, sequences):
    # sequence_array = tf.TensorArray(tf.int64, size=0, dynamic_size=True)
    bidding = sequences["BiddingIndicesSequence"]
    #print("python print bidding", bidding)
    #print("python print sequences", sequences)
    #tf.print("bidding", bidding, type(bidding))
    bidding_length = tf.size(bidding)
    #tf.print("bidding_length", bidding_length, tf.shape(bidding))
    transposed_bidding = tf.transpose(bidding)
    #tf.print("transposed_tf", transposed_bidding, summarize=-1)
    tiled_bidding = tf.tile(transposed_bidding, tf.shape(bidding))
    #tf.print("tiled_tf", tiled_bidding, summarize=-1)
    ragged_bidding = tf.gather(tiled_bidding, tf.ragged.range(tf.range(bidding_length)), batch_dims=1)
    #tf.print("ragged_bidding_tf", ragged_bidding, summarize=-1)
    sequence_keys = ["HoldingSequence", "PlayerPositionSequence"]
    dataset_dict = {sequence_key: sequences[sequence_key] for sequence_key in sequence_keys}
    dataset_dict["ragged_bidding"] = ragged_bidding
    #tf.print("expand_hcp_tf", tf.expand_dims(context["HcpTarget"], axis=1), summarize=-1)
    tiled_hcp = tf.tile(tf.transpose(tf.expand_dims(context["HcpTarget"], axis=1)), tf.shape(bidding))
    #tf.print("tiled_hcp_tf", tiled_hcp, summarize=-1)
    dataset_dict["HcpTarget"] = tiled_hcp
    return tf.data.Dataset.from_tensor_slices(dataset_dict)


# subsequence_dataset = decoded_dataset.flat_map(create_subsequences)
subsequence_dataset = decoded_dataset.flat_map(create_subsequences_smart)
print(f"subsequence_dataset.element_spec={subsequence_dataset.element_spec}")
for i, subsequences in enumerate(subsequence_dataset):
    # print("FLATMAPPED:", subsequences)
    print(i, subsequences)
    # print(tf.shape(subsequences['ragged_bidding']))
    if i > 10:
        break


def convert_ragged(ragged_dataset):
    ragged_dataset["bidding"] = ragged_dataset["ragged_bidding"]
    # ragged_dataset["bidding"] = bidding
    return ragged_dataset


convert_ragged_dataset = subsequence_dataset.map(convert_ragged)
print(f"convert_ragged_dataset.element_spec={convert_ragged_dataset.element_spec}")
for i, example in enumerate(convert_ragged_dataset):
    print(i, example)
    if i > 10:
        break

bucketed_dataset = convert_ragged_dataset.bucket_by_sequence_length(
    element_length_func=lambda elem: tf.shape(elem["bidding"])[0],
    bucket_boundaries=[4, 8, 16],
    bucket_batch_sizes=[64, 32, 16, 8],
)


print("BUCKETED Dataset")
for i, example in enumerate(bucketed_dataset):
    # print("FLATMAPPED:", subsequences)
    print(i, example)
    if i > 3:
        break


def make_categorical(example):
    one_hot_bidding = tf.one_hot(example["bidding"], BIDDING_VOCAB_SIZE)
    example["one_hot_bidding"] = one_hot_bidding
    one_hot_player = tf.squeeze(tf.one_hot(example["PlayerPositionSequence"], 4), 1)
    example["one_hot_player_position"] = one_hot_player
    return example


one_hot_dataset = bucketed_dataset.map(make_categorical)
print("ONE_HOT Dataset")
for i, example in enumerate(one_hot_dataset):
    print(i, example)
    if i > 3:
        break

def split_targets(bidding_example):
    target = bidding_example["HcpTarget"]
    return (bidding_example, target)

split_targets_dataset = one_hot_dataset.map(split_targets)
print("SPLIT Dataset")
for i, example in enumerate(split_targets_dataset):
    print(i, example)
    print("bidding shape", tf.shape(example[0]["one_hot_bidding"]))
    if i > 3:
        break





def build_lstm_model(output_shape: int, sequence_length: int = MAX_BIDDING_SEQUENCE):
    bidding_input_layer = Input(shape=(None, BIDDING_VOCAB_SIZE), name="one_hot_bidding")
    lstm_outputs, state_h, state_c = LSTM(units=128, return_state=True)(bidding_input_layer)

    player_input_layer = Input(shape=(4), name="one_hot_player_position")
    holding_input_layer = Input(shape=(52), name="HoldingSequence")

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

bid_lstm_model.fit(split_targets_dataset, epochs=10)