from dataclasses import dataclass
from typing import List

from bridgebots_sequence.bidding_context_features import ContextFeature
from bridgebots_sequence.bidding_sequence_features import SequenceFeature


@dataclass(frozen=True)
class ModelMetadata:
    context_features: List[ContextFeature]
    sequence_features: List[SequenceFeature]
    description: str
