from pathlib import Path
from typing import List

import tensorflow as tf

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
from bridgebots_sequence.feature_utils import holding_from_cards


class BiddingInferenceEngine:
    def __init__(
        self, context_features: List[ContextFeature], sequence_features: List[SequenceFeature], model_path: Path
    ):
        self.context_features = context_features
        self.sequence_features = sequence_features
        self.model: tf.keras.models.Model = tf.keras.models.load_model(model_path)

    def _build_sequence_example(
        self,
        dealer: Direction,
        dealer_vulnerable: bool,
        dealer_opp_vulnerable: bool,
        player_holding: List[Card],
        bidding_record: List[str],
        bidding_metadata: List[BidMetadata],
    ) -> tf.train.SequenceExample:
        # We "lie" to the model about the player holdings since we only have access to one hand. We will only use the prediction for the current player so this will not affect the prediction
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

    def predict(
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


if __name__ == "__main__":
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
# def build_inference_input(context_features: List[ContextFeature], sequence_features: List[SequenceFeature])
