from abc import ABC, abstractmethod
from typing import Any, Dict, List

import numpy as np
import tensorflow as tf
from numpy import ndarray

from bridgebots import Direction
from bridgebots_sequence.feature_utils import TARGET_BIDDING_VOCAB


class ModelInterpreterMixin:
    def model_interpreter(self, from_logits=False):
        return self.logits_interpreter if from_logits else self.interpreter


class ModelInterpreter(ABC):
    @abstractmethod
    def interpret(self, prediction: ndarray, dealer: Direction) -> Any:
        pass

    @abstractmethod
    def interpret_proba(self, prediction: ndarray, sort: bool):
        pass

    # Currently, model interpreters do not have any internal state - they are just collections of functions, so we can
    # compare equality and hash by class
    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class ShapeModelInterpreter(ModelInterpreter):
    def interpret(self, prediction: ndarray, dealer: Direction) -> Dict[Direction, List[int]]:
        return {dealer.offset(i): prediction[i * 4 : i * 4 + 4] for i in range(4)}

    def interpret_proba(self, prediction: ndarray, sort: bool):
        raise NotImplementedError


class HcpModelInterpreter(ModelInterpreter):
    def interpret(self, prediction: ndarray, dealer: Direction) -> Dict[Direction, int]:
        return {dealer.offset(i): prediction[i] for i in range(4)}

    def interpret_proba(self, prediction: ndarray, sort: bool):
        raise NotImplementedError


class BiddingPredictionModelInterpreter(ModelInterpreter):
    bid_vectorization_layer = tf.keras.layers.StringLookup(
        num_oov_indices=1, vocabulary=TARGET_BIDDING_VOCAB, invert=True
    )

    def interpret(self, prediction: ndarray, dealer: Direction):
        predicted_index = np.argmax(prediction)
        predicted_str_tensor = self.bid_vectorization_layer(predicted_index)
        return bytes.decode(predicted_str_tensor.numpy())

    def interpret_proba(self, prediction: ndarray, sort: bool = True):
        bids = [bytes.decode(bid) for bid in self.bid_vectorization_layer(np.arange(40)).numpy()]
        prediction_pairs = list(zip(bids, prediction))
        if sort:
            prediction_pairs.sort(key=lambda pred_pair: pred_pair[1], reverse=True)
        return prediction_pairs


class BiddingLogitsModelInterpreter(BiddingPredictionModelInterpreter):
    def interpret(self, prediction: ndarray, dealer: Direction):
        return super().interpret(tf.nn.softmax(prediction), dealer)

    def interpret_proba(self, prediction: ndarray, sort: bool = True):
        return super().interpret_proba(tf.nn.softmax(prediction), sort)
