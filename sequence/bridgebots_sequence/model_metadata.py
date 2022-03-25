from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from bridgebots_sequence.bidding_context_features import ContextFeature
from bridgebots_sequence.bidding_sequence_features import CategoricalSequenceFeature, SequenceFeature
from bridgebots_sequence.interpreter import ModelInterpreter


@dataclass(frozen=True)
class ModelMetadata:
    training_data: Path
    validation_data : Optional[Path]
    context_features: List[ContextFeature]
    sequence_features: List[SequenceFeature]
    target : Union[ContextFeature, CategoricalSequenceFeature]
    model_interpreter: ModelInterpreter
    description: str
    training_metrics : Dict[str, float]

