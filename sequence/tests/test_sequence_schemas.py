import unittest

from bridgebots_sequence.bidding_context_features import TargetHcp, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
)
from bridgebots_sequence.model_metadata import ModelMetadata
from bridgebots_sequence.sequence_schemas import ModelMetadataSchema


class TestSchemas(unittest.TestCase):
    def test_model_features_schema(self):
        context_features = [TargetHcp(), Vulnerability()]
        sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
        model_metadata = ModelMetadata(context_features, sequence_features, "test model")
        model_metadata_schema = ModelMetadataSchema()
        expected_metadata = {
            "context_features": ["TargetHcp", "Vulnerability"],
            "sequence_features": ["BiddingSequenceFeature", "HoldingSequenceFeature", "PlayerPositionSequenceFeature"],
            "description": "test model",
        }
        self.assertEqual(expected_metadata, model_metadata_schema.dump(model_metadata))
        self.assertEqual(model_metadata, model_metadata_schema.load(model_metadata_schema.dump(model_metadata)))
