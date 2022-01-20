import pickle
import random
from pathlib import Path
from typing import List

import tensorflow as tf
from tensorflow.python.lib.io.tf_record import TFRecordCompressionType

from bridgebots import DealRecord
from sequence.dev.bridge_sequence_utils import (
    BiddingIndices,
    BiddingIndicesSequence,
    HcpTarget,
    Holding,
    HoldingSequence,
    PlayerPosition,
    PlayerPositionSequence, Vulnerability,
)
from sequence.dev.one_hand_tfdata import OneHandExampleGenerator, OneHandSequenceExampleGenerator

MAX_RECORDS = 10_000


def create_all_training_data():
    pickle_file_path = "/Users/frice/bridge/vugraph_project/all_deals.pickle"
    with open(pickle_file_path, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)

    print("loaded records: ", len(deal_records))

    base_path = Path("/Users/frice/bridge/bid_learn/one_hand/")

    splits = [("train", []), ("validation", []), ("test", [])]
    split_weights = [0.8, 0.1, 0.1]
    for deal_record in deal_records:
        split_name, training_data_list = random.choices(splits, split_weights)[0]
        training_data_list.append(deal_record)

    for split, split_records in splits:
        records_chunks = [split_records[i : i + MAX_RECORDS] for i in range(0, len(split_records), MAX_RECORDS)]
        split_directory = base_path / split
        split_directory.mkdir(parents=True, exist_ok=True)
        for i, chunk in enumerate(records_chunks):
            chunk_path = split_directory / (str(i) + ".pickle")
            with open(chunk_path, "wb") as split_file:
                pickle.dump(chunk, split_file)
                print(f"wrote {len(chunk)} records to {split_file.name}")


def create_toy_data():
    pickle_file_path = "/Users/frice/bridge/vugraph_project/all_deals.pickle"
    with open(pickle_file_path, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    toy_data_sizes = {"TRAIN": 100, "VALIDATION": 10, "TEST": 10}
    deal_index = 0
    base_path = Path("/Users/frice/bridge/bid_learn/one_hand/toy")
    for split, size in toy_data_sizes.items():
        split_records = []
        for i in range(size):
            split_records.append(deal_records[deal_index])
            deal_index += 1
        with open(base_path / (split + ".pickle"), "wb") as split_file:
            pickle.dump(split_records, split_file)
            print(f"wrote {len(split_records)} records to {split_file.name}")


def create_examples_data():
    pickle_file_path = "/Users/frice/bridge/bid_learn/one_hand/toy/TRAIN.pickle"
    with open(pickle_file_path, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    features = [PlayerPosition(), Holding(), BiddingIndices()]
    deal_targets = [HcpTarget()]
    example_gen = iter(OneHandExampleGenerator(deal_records, features, deal_targets))

    example_path = "/Users/frice/bridge/bid_learn/one_hand/toy/train.tfrecords"
    write_count = 0
    with tf.io.TFRecordWriter(example_path, TFRecordCompressionType.NONE) as file_writer:
        for example in example_gen:
            print(example)
            # print(example.SerializeToString())
            file_writer.write(example.SerializeToString())
            parsed_example = tf.io.parse_single_example(
                example.SerializeToString(),
                features={
                    "PlayerPosition": tf.io.FixedLenFeature([], dtype=tf.int64),
                    "Holding": tf.io.FixedLenFeature([52], dtype=tf.int64),
                    "HcpTarget": tf.io.FixedLenFeature([4], dtype=tf.int64),
                },
            )
            # print(parsed_example)
            # tf.print(parsed_example["PlayerPosition"])
            # tf.print(parsed_example["Holding"])
            write_count += 1
            # if write_count > 20:
            # break
    print(f"wrote {write_count} results to {example_path}")


def create_sequence_examples():
    pickle_file_path = "/Users/frice/bridge/bid_learn/one_hand/VALIDATION.pickle"
    with open(pickle_file_path, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    features = [BiddingIndicesSequence(), HoldingSequence(), PlayerPositionSequence()]
    deal_targets = [HcpTarget(), Vulnerability()]
    example_gen = iter(OneHandSequenceExampleGenerator(deal_records, features, deal_targets))
    example_path = "/Users/frice/bridge/bid_learn/one_hand/sequence_validation.tfrecords"
    write_count = 0
    with tf.io.TFRecordWriter(example_path, TFRecordCompressionType.NONE) as file_writer:
        for example in example_gen:
            file_writer.write(example.SerializeToString())
            write_count += 1
            if write_count % 1_000 == 0:
                print(f"write_count={write_count}")
    print(f"wrote {write_count} results to {example_path}")
    """
        parsed_example = tf.io.parse_single_sequence_example(
            serialized_example,
            context_features={"HcpTarget": tf.io.FixedLenFeature([4], dtype=tf.int64)},
            sequence_features={"BiddingIndicesSequence":tf.io.FixedLenSequenceFeature([1], dtype=tf.int64),
                               "HoldingSequence":tf.io.FixedLenSequenceFeature([52], dtype=tf.int64),
                               "PlayerPositionSequence":tf.io.FixedLenSequenceFeature([1], dtype=tf.int64)},
        )"""


create_sequence_examples()
# create_examples_data()
# create_toy_data()
# create_all_training_data()
