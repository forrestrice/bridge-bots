import unittest
from pathlib import Path

from bridgebots_sequence.bidding_context_features import TargetHcp, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
)
from bridgebots_sequence.inference import HcpModelInterpreter
from bridgebots_sequence.model_metadata import ModelMetadata
from bridgebots_sequence.sequence_schemas import ModelMetadataSchema


class TestSchemas(unittest.TestCase):
    def test_model_features_schema(self):
        context_features = [TargetHcp(), Vulnerability()]
        sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
        model_metadata = ModelMetadata(
            Path("some/path/training"),
            Path("some/path/validation"),
            context_features,
            sequence_features,
            TargetHcp(),
            HcpModelInterpreter(),
            "test model",
            {"loss": 20.2, "val_loss": 25.0},
        )
        model_metadata_schema = ModelMetadataSchema()
        expected_metadata = {
            "training_data": "some/path/training",
            "validation_data": "some/path/validation",
            "context_features": ["TargetHcp", "Vulnerability"],
            "sequence_features": ["BiddingSequenceFeature", "HoldingSequenceFeature", "PlayerPositionSequenceFeature"],
            "target": "TargetHcp",
            "model_interpreter": "HcpModelInterpreter",
            "description": "test model",
            "training_metrics": {"loss": 20.2, "val_loss": 25.0},
        }
        self.assertEqual(expected_metadata, model_metadata_schema.dump(model_metadata))
        self.assertEqual(model_metadata, model_metadata_schema.load(model_metadata_schema.dump(model_metadata)))
