import dataclasses
from pathlib import Path
from typing import List

import tensorflow as tf

from bridgebots import BoardRecord, Deal, DealRecord, parse_multi_lin
from bridgebots_sequence.bidding_context_features import ContextFeature, TargetHcp, Vulnerability
from bridgebots_sequence.bidding_sequence_features import (
    BidAlertedSequenceFeature,
    BidExplainedSequenceFeature,
    BiddingSequenceFeature,
    HoldingSequenceFeature,
    PlayerPositionSequenceFeature,
    SequenceFeature,
    TargetBiddingSequence,
)
from bridgebots_sequence.create_sequence_examples import OneHandSequenceExampleGenerator


def create_evaluation_records(deal: Deal, board_record: BoardRecord) -> DealRecord:
    board_records = []
    for i in range(len(board_record.bidding_record) + 1):
        bidding_metadata_subsequence = [
            bid_metadata for bid_metadata in board_record.bidding_metadata if bid_metadata.bid_index < i
        ]
        board_records.append(
            dataclasses.replace(
                board_record,
                bidding_record=board_record.bidding_record[0:i],
                bidding_metadata=bidding_metadata_subsequence,
                score=board_record.score,
                declarer_vulnerable=deal.is_vulnerable(board_record.declarer),
            )
        )
    return DealRecord(deal, board_records)


def create_evaluation_dataset(
    deal_records: List[DealRecord], context_features: List[ContextFeature], sequence_features: List[SequenceFeature]
) -> tf.data.Dataset:
    def string_gen():
        return (
            example.SerializeToString()
            for example in iter(OneHandSequenceExampleGenerator(deal_records, context_features, sequence_features))
        )

    return tf.data.Dataset.from_generator(string_gen, output_signature=tf.TensorSpec(shape=(), dtype=tf.string))


if __name__ == "__main__":
    records = parse_multi_lin(
        Path("/Users/frice/bridge/vugraph_project/www.sarantakos.com/bridge/vugraph/2015/vandy/f1.lin")
    )
    target_deal = records[0].deal
    target_board = records[0].board_records[0]
    evaluation_records = create_evaluation_records(target_deal, target_board)
    print(target_deal, target_board)
    print("EVALUATION")
    for board_record in evaluation_records.board_records:
        print(board_record.bidding_record)

    sequence_features = [
        BiddingSequenceFeature(),
        HoldingSequenceFeature(),
        PlayerPositionSequenceFeature(),
        BidAlertedSequenceFeature(),
        BidExplainedSequenceFeature(),
        TargetBiddingSequence(),
    ]
    context_features = [TargetHcp(), Vulnerability()]
    evaluation_dataset = create_evaluation_dataset([evaluation_records], context_features, sequence_features)
    for example in evaluation_dataset:
        print(example)
        break
