from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf

# from keras.layers import Dense, LSTM

from bridgebots_sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    CategoricalSequenceFeature, HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from bridgebots_sequence.dataset_pipeline import build_tfrecord_dataset
from bridgebots_sequence.feature_utils import BIDDING_VOCAB_SIZE


target = TargetHcp()
print(issubclass(target.__class__, CategoricalSequenceFeature))
print(isinstance(target, ContextFeature))

target_name = target.sequence_name if isinstance(target, ContextFeature) else target.prepared_name
print(target_name)
