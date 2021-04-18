import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import LSTM
from tensorflow.python.keras import Input, Model
from tensorflow.python.keras.layers import Dense, Lambda, Reshape
from tensorflow.python.keras.optimizer_v2.adam import Adam

from train.bridge_training_utils import bidding_vocab

LSTM_MEMORY_SIZE = 128


def bidding_model(Tx):
    vocab_size = len(bidding_vocab)
    LSTM_cell = LSTM(LSTM_MEMORY_SIZE, return_state=True)
    reshapor = Reshape((1, vocab_size))
    densor = Dense(vocab_size, activation='softmax')
    X = Input(shape=(Tx, vocab_size))

    a0 = Input(shape=(LSTM_MEMORY_SIZE,), name='a0')
    c0 = Input(shape=(LSTM_MEMORY_SIZE,), name='c0')
    holdings_constants = Input(shape=(208,), name='holdings_constants')
    a = a0
    c = c0

    outputs = []
    for t in range(Tx):
        x = Lambda(lambda z: z[:, t, :])(X)
        x = reshapor(x)
        a, _, c = LSTM_cell(inputs=x, initial_state=[a, c], constants=holdings_constants)
        out = densor(a)
        outputs.append(out)
    model = Model(inputs=[X, a0, c0, holdings_constants], outputs=outputs)
    return model
    # LSTM_cell = LSTM(LSTM_MEMORY_SIZE, return_state = True)


data_prefix = '/Users/frice/bridge/bid_learn/'
holdings, bid_sequences = np.load(data_prefix + 'TRAIN_HOLDING.npy'), np.load(data_prefix + 'TRAIN_BID_SEQUENCE.npy')
print(bid_sequences.shape)
bid_sequences_input = np.copy(bid_sequences)
empty_start_sequence = np.zeros((bid_sequences.shape[0], 1, len(bidding_vocab)))
# empty_start_sequence = np.broadcast_to(np.zeros(40), (bid_sequences.shape[0], 1, 40))
print(empty_start_sequence.shape)
bid_sequences_input = np.concatenate((empty_start_sequence, bid_sequences_input), axis=1)
print(bid_sequences.shape, bid_sequences_input.shape)

'''
pad_end_sequence = np.broadcast(
    tf.keras.utils.to_categorical(bidding_vocab['PAD'], num_classes=len(bidding_vocab)),
    (bid_sequences.shape[0], 1, 40))
    '''
pad_end_sequence = np.reshape(tf.keras.utils.to_categorical(bidding_vocab['PAD'], num_classes=len(bidding_vocab)),
                              (1, len(bidding_vocab)))
stacked_pad_end_sequence = np.broadcast_to(pad_end_sequence, (bid_sequences.shape[0], 1, len(bidding_vocab)))
print(stacked_pad_end_sequence.shape)
bid_sequences_targets = np.concatenate((bid_sequences, stacked_pad_end_sequence), axis=1)
# TODO understand this a bit better
bid_sequences_targets = np.transpose(bid_sequences_targets, (1, 0, 2))
print(f'bid_sequences_targets.shape={bid_sequences_targets.shape}')

num_samples, Tx, vocab_size = bid_sequences_input.shape

model = bidding_model(Tx)
opt = Adam(lr=0.01, beta_1=0.9, beta_2=0.999, decay=0.01)
model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

a0 = np.zeros((num_samples, LSTM_MEMORY_SIZE))
c0 = np.zeros((num_samples, LSTM_MEMORY_SIZE))
#holdings_constants = tf.keras.backend.constant(holdings)

model.fit([bid_sequences_input, a0, c0], list(bid_sequences_targets), epochs=3)


# bidding_model(Tx)'''
