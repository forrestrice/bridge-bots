from typing import Dict, Optional, Union

import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import History

from bridgebots_sequence.bidding_context_features import ContextFeature
from bridgebots_sequence.bidding_sequence_features import CategoricalSequenceFeature


@tf.function
def prepare_targets(target: str, sample_weights_name: Optional[str], contexts, sequences):
    targets = sequences[target]
    if sample_weights_name:
        return sequences, targets, sequences[sample_weights_name]
    return sequences, targets


def get_target_shape(target: Union[ContextFeature, CategoricalSequenceFeature]):
    return target.num_tokens if issubclass(target.__class__, CategoricalSequenceFeature) else target.shape


def build_training_metrics(history: History) -> Dict[str, float]:
    evaluation_metric = "val_loss" if "val_loss" in history.history else "loss"
    best_epoch = np.argmin(history.history[evaluation_metric])
    return {metric_name: metric[best_epoch] for metric_name, metric in history.history.items()}
