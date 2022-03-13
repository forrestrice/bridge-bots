import dataclasses
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import tensorflow as tf
from numpy import ndarray

from bridgebots import BidMetadata, Card, Direction
from bridgebots_sequence.bidding_context_features import BiddingContextExampleData, ContextFeature, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BidAlertedSequenceFeature,
    BidExplainedSequenceFeature,
    BiddingSequenceExampleData,
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from bridgebots_sequence.dataset_pipeline import build_inference_dataset
from bridgebots_sequence.feature_utils import TARGET_BIDDING_VOCAB, holding_from_cards
from bridgebots_sequence.model_metadata import ModelMetadata
from bridgebots_sequence.sequence_schemas import ModelMetadataSchema


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


class BiddingInferenceEngine:
    def __init__(
        self,
        model_path: Path,

    ):
        self.model_metadata = self._load_meatadata(model_path)
        self.model: tf.keras.models.Model = tf.keras.models.load_model(model_path)

    def _load_meatadata(self, model_path: Path):
        with open(model_path / "metadata.json", "r") as metadata_file:
            model_metadata : ModelMetadata = ModelMetadataSchema().loads(metadata_file.read())
        # The target can not be included for inference since it is unknown
        context_features = [cf for cf in model_metadata.context_features if cf != model_metadata.target]
        sequence_features = [sf for sf in model_metadata.sequence_features if sf != model_metadata.target]
        return dataclasses.replace(model_metadata, context_features=context_features, sequence_features=sequence_features)


    def _build_sequence_example(
        self,
        dealer: Direction,
        dealer_vulnerable: bool,
        dealer_opp_vulnerable: bool,
        player_holding: List[Card],
        bidding_record: List[str],
        bidding_metadata: List[BidMetadata],
    ) -> tf.train.SequenceExample:
        # We "lie" to the model about the player holdings since we only have access to one hand. We will only use the
        # prediction for the current player so this will not affect the final prediction
        player_holdings = {dealer.offset(i): holding_from_cards(player_holding) for i in range(4)}
        bidding_context_data = BiddingContextExampleData(
            dealer_vulnerable=dealer_vulnerable, dealer_opp_vulnerable=dealer_opp_vulnerable, deal=None
        )
        calculated_context_features = {
            context_feature.name: context_feature.calculate(bidding_context_data)
            for context_feature in self.context_features
        }
        context = tf.train.Features(feature=calculated_context_features)

        bidding_data = BiddingSequenceExampleData(dealer, bidding_record, bidding_metadata, player_holdings)
        calculated_sequence_features = {
            feature.name: feature.calculate(bidding_data) for feature in self.sequence_features
        }
        feature_lists = tf.train.FeatureLists(feature_list=calculated_sequence_features)
        return tf.train.SequenceExample(context=context, feature_lists=feature_lists)

    def _build_inference_dataset(self, sequence_example: tf.train.SequenceExample) -> tf.data.Dataset:
        def string_gen():
            yield sequence_example.SerializeToString()

        string_dataset = tf.data.Dataset.from_generator(
            string_gen, output_signature=tf.TensorSpec(shape=(), dtype=tf.string)
        )
        return build_inference_dataset(string_dataset, self.context_features, self.sequence_features)

    def _predict(
        self,
        dealer: Direction,
        dealer_vulnerable: bool,
        dealer_opp_vulnerable: bool,
        player_holding: List[Card],
        bidding_record: List[str],
        bidding_metadata: List[BidMetadata],
    ):

        sequence_example = self._build_sequence_example(
            dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, bidding_record, bidding_metadata
        )
        inference_dataset = self._build_inference_dataset(sequence_example)
        predictions = self.model.predict(inference_dataset)
        # Bidding Models are trained to expect a batch of examples and to return predictions for every time-step in the
        # bidding. Return the first (only) output in the batch and the prediction for the last time-step.
        return predictions[0][-1]

    def predict(
        self,
        dealer: Direction,
        dealer_vulnerable: bool,
        dealer_opp_vulnerable: bool,
        player_holding: List[Card],
        bidding_record: List[str],
        bidding_metadata: List[BidMetadata],
    ):
        prediction = self._predict(
            dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, bidding_record, bidding_metadata
        )
        return self.model_interpreter.interpret(prediction, dealer)

    def predict_proba(
        self,
        dealer: Direction,
        dealer_vulnerable: bool,
        dealer_opp_vulnerable: bool,
        player_holding: List[Card],
        bidding_record: List[str],
        bidding_metadata: List[BidMetadata],
        sort: bool = True,
    ):
        prediction = self._predict(
            dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, bidding_record, bidding_metadata
        )
        return self.model_interpreter.interpret_proba(prediction, sort)



if __name__ == "__main__":
    tf.config.run_functions_eagerly(True)
    model_path = Path("/Users/frice/bridge/models/toy/predict_bidding")
    with open(model_path / "metadata.json", "r") as metadata_file:
        model_metadata = ModelMetadataSchema().loads(metadata_file.read())
    engine = BiddingInferenceEngine(
        context_features=[Vulnerability()],
        sequence_features=[
            BiddingSequenceFeature(),
            HoldingSequenceFeature(),
            PlayerPositionSequenceFeature(),
            BidAlertedSequenceFeature(),
            BidExplainedSequenceFeature(),
        ],
        model_path=Path("/Users/frice/Downloads/hcp_sos_2"),
        model_interpreter=HcpModelInterpreter(),
    )
    dealer = Direction.WEST
    dealer_vulnerable = False
    dealer_opp_vulnerable = False
    bidding_record = ["PASS", "PASS", "PASS", "1D", "1S", "1NT", "3S", "X", "PASS"]
    bidding_metadata = []
    player_holding = [
        Card.from_str(s) for s in ["SA", "SK", "ST", "H7", "H6", "D7", "D6", "CQ", "CT", "C7", "C6", "C5", "C3"]
    ]
    print(
        engine.predict(
            dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, bidding_record, bidding_metadata
        )
    )
    print(
        engine.predict_proba(
            dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, bidding_record, bidding_metadata
        )
    )
    """
    engine = BiddingInferenceEngine(
        context_features=[Vulnerability()],
        sequence_features=[
            BiddingSequenceFeature(),
            HoldingSequenceFeature(),
            PlayerPositionSequenceFeature(),
            BidAlertedSequenceFeature(),
            BidExplainedSequenceFeature(),
        ],
        model_path=Path('/Users/frice/Downloads/hcp_sos_1')
    )
    dealer = Direction.WEST
    dealer_vulnerable = False
    dealer_opp_vulnerable = False
    bidding_record = ["PASS", "PASS", "PASS", "1D", "1S", "1NT","3S","X","PASS"]
    bidding_metadata = []
    player_holding = [Card.from_str(s) for s in ["SA", "SK", "ST", "H7", "H6", "D7", "D6", "CQ", "CT", "C7", "C6", "C5", "C3"]]
    print(engine.predict(dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, bidding_record, bidding_metadata))
    """
# def build_inference_input(context_features: List[ContextFeature], sequence_features: List[SequenceFeature])
