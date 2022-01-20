import random

import tensorflow as tf
from keras import Input, Model
from keras.layers import Dense, LSTM

MAX_LENGTH = 10
NUM_CLASSES = 5
VOCAB_SIZE = NUM_CLASSES + 1 # + 1 for padding
NUM_EXAMPLES = 500


def data_gen():
    for i in range(NUM_EXAMPLES):
        length = random.randint(1, MAX_LENGTH)
        sequence = [random.randint(1, NUM_CLASSES) for _ in range(length)]
        sequences = []
        targets = []
        for i in range(length):
            sequences.append(sequence[0:i])
            targets.append(sum(sequence[0:i]))

        padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
            sequences, padding="pre", maxlen=MAX_LENGTH, truncating="post"
        )
        print(padded_sequences, "\n")
        one_hot_sequences = tf.keras.utils.to_categorical(padded_sequences, num_classes=VOCAB_SIZE)
        yield one_hot_sequences, targets


print(next(data_gen()))

sequence_dataset = tf.data.Dataset.from_generator(
    data_gen,
    output_signature=(
        tf.TensorSpec(shape=(None, MAX_LENGTH, VOCAB_SIZE), dtype=tf.float32),  # sequence
        tf.TensorSpec(shape=None, dtype=tf.float32),  # targets
    ),
)
# this works
print("UNBATCHED")
print(list(sequence_dataset.as_numpy_iterator()))

#this fails
print("BATCHED")
batched_dataset = sequence_dataset.batch(3)
print(list(batched_dataset.as_numpy_iterator()))


def build_lstm_model(sequence_length: int = MAX_LENGTH):
    input_layer = Input(shape=(sequence_length, VOCAB_SIZE))
    lstm_outputs, state_h, state_c = LSTM(units=32, return_state=True)(input_layer)
    x = Dense(16, "selu")(lstm_outputs)
    output_layer = Dense(1, "selu")(x)
    return Model(inputs=[input_layer], outputs=output_layer)

"""
lstm_model = build_lstm_model()
lstm_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.MeanSquaredError(),
    metrics=["mae", "mse"],
)
lstm_model.fit(sequence_dataset, epochs=5)
"""