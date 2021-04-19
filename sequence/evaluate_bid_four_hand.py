import pickle
from typing import List

from tensorflow import keras

from sequence.bidding_training_data import BiddingSequenceDataGenerator, BiddingTrainingData

bid_learn_prefix = "/Users/frice/bridge/bid_learn_noeos/"


lstm_model = keras.models.load_model(bid_learn_prefix + "lstm_model_v3_noeos")

with open(bid_learn_prefix + "VALIDATION.pickle", "rb") as pickle_file:
    bidding_validation_data: List[BiddingTrainingData] = pickle.load(pickle_file)

data_generator = BiddingSequenceDataGenerator(20, bidding_validation_data)

lstm_model.evaluate(data_generator)
