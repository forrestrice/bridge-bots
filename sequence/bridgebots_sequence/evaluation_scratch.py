from functools import partial
from pathlib import Path
from typing import List

import tensorflow as tf

# from keras.layers import Dense, LSTM

from bridgebots_sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
)
from bridgebots_sequence.dataset_pipeline import build_tfrecord_dataset
from bridgebots_sequence.feature_utils import BIDDING_VOCAB_SIZE

loaded_model = tf.keras.models.load_model("/Users/frice/Downloads/hcp_sos_2")

sequence_features = [BiddingSequenceFeature(), HoldingSequenceFeature(), PlayerPositionSequenceFeature()]
context_features = [TargetHcp(), Vulnerability()]
validation_dataset = build_tfrecord_dataset(
    Path("/Users/frice/bridge/bid_learn/deals/validation.tfrecord"), context_features, sequence_features
)

for example in validation_dataset:
    print("EXAMPLE\n")
    #    print(example)
    break
unbatched_validation = validation_dataset.unbatch()
for example in unbatched_validation:
    # print("UNBATCHED")
    # print(example)
    break

# print(loaded_model.summary())
# target = context_features[0]
# targeted_validation_dataset = validation_dataset.map(
#    partial(prepare_targets, target), num_parallel_calls=tf.data.AUTOTUNE
# ).prefetch(tf.data.AUTOTUNE)
single_item_batched = unbatched_validation.map(lambda c, s: s).batch(1)
for i, single_item_batch in enumerate(single_item_batched):
    print(single_item_batch)
    print(single_item_batch["bidding"])
    print(loaded_model.predict(single_item_batch))
    print("------------")
    if i > 3:
        break
