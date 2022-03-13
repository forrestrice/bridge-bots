from typing import Dict, Union

import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import History

from bridgebots_sequence.bidding_context_features import ContextFeature
from bridgebots_sequence.bidding_sequence_features import CategoricalSequenceFeature, SequenceFeature


@tf.function
def prepare_targets(target: str, contexts, sequences):
    targets = sequences[target]
    return sequences, targets


def get_target_shape(target: Union[ContextFeature, CategoricalSequenceFeature]):
    return target.num_tokens if issubclass(target.__class__, CategoricalSequenceFeature) else target.shape


def build_training_metrics(history: History) -> Dict[str, float]:
    best_epoch = np.argmin(history.history["val_loss"])
    return {metric_name: metric[best_epoch] for metric_name, metric in history.history.items()}
