import pickle
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List

import tensorflow as tf

from bridgebots import DealRecord
from bridgebots_sequence.feature_utils import TARGET_BIDDING_VOCAB
from bridgebots_sequence.inference import BiddingInferenceEngine


def load_deals(source_pickle: Path, allow_duplicate_deals=True):
    with open(source_pickle, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)
    if not allow_duplicate_deals:
        deal_records = [DealRecord(deal_record.deal, deal_record.board_records[0:1]) for deal_record in deal_records]
    return deal_records


@dataclass
class AccuracyMetric:
    correct: int = 0
    incorrect: int = 0

    @property
    def accuracy(self) -> float:
        try:
            return self.correct / (self.correct + self.incorrect)
        except ZeroDivisionError:
            return float("nan")

    def __str__(self):
        return f"accuracy:{self.accuracy}, correct:{self.correct}, incorrect:{self.incorrect}"


@dataclass
class PrecisionMetric:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        try:
            return self.true_positives / (self.true_positives + self.false_positives)
        except ZeroDivisionError:
            return float("nan")

    @property
    def recall(self) -> float:
        try:
            return self.true_positives / (self.true_positives + self.false_negatives)
        except ZeroDivisionError:
            return float("nan")

    def __str__(self):
        return (
            f"precision:{self.precision}, recall:{self.recall}, true_positives:{self.true_positives}, "
            f"false_positives:{self.false_positives}, false_negatives:{self.false_negatives}"
        )


def print_metrics(accuracy_by_position, precision_by_bid):
    print("\n")
    print("Accuracy By Position")
    for position, accuracy_metric in sorted(accuracy_by_position.items(), key=lambda t: t[0]):
        print(position, accuracy_metric)

    total_correct = sum([a.correct for a in accuracy_by_position.values()])
    total_incorrect = sum([a.incorrect for a in accuracy_by_position.values()])
    overall_accuracy = AccuracyMetric(total_correct, total_incorrect)
    print("\nOverall Accuracy:", overall_accuracy)

    print("\n")
    print("Precision By Bid")
    for bid in TARGET_BIDDING_VOCAB:
        print(bid, precision_by_bid[bid])

    total_true_positive = sum([a.true_positives for a in precision_by_bid.values()])
    total_false_positive = sum([a.false_positives for a in precision_by_bid.values()])
    total_false_negative = sum([a.false_negatives for a in precision_by_bid.values()])
    overall_precision = PrecisionMetric(total_true_positive, total_false_positive, total_false_negative)
    print("\nOverall Precision:", overall_precision)


def confusion_evaluation(deal_records: List[DealRecord], engine: BiddingInferenceEngine):
    accuracy_by_position = defaultdict(AccuracyMetric)
    precision_by_bid = defaultdict(PrecisionMetric)

    for deal_record_count, deal_record in enumerate(deal_records):
        dealer = deal_record.deal.dealer
        dealer_vulnerable = deal_record.deal.is_vulnerable(dealer)
        dealer_opp_vulnerable = deal_record.deal.is_vulnerable(dealer.next())
        print(deal_record_count, len(deal_record.board_records))
        for board_record in deal_record.board_records:
            bidding_record_with_eos = [] + board_record.bidding_record + ["EOS"]
            prediction_record = []
            for i in range(len(board_record.bidding_record) + 1):
                player = dealer.offset(i)
                previous_bidding = board_record.bidding_record[0:i]
                player_holding = deal_record.deal.player_cards[player]
                bidding_metadata = []
                predicted_bid = engine.predict(
                    dealer, dealer_vulnerable, dealer_opp_vulnerable, player_holding, previous_bidding, bidding_metadata
                )
                prediction_record.append(predicted_bid)
                target_bid = bidding_record_with_eos[i]
                if target_bid == predicted_bid:
                    accuracy_by_position[i].correct += 1
                    precision_by_bid[predicted_bid].true_positives += 1
                else:
                    accuracy_by_position[i].incorrect += 1
                    precision_by_bid[predicted_bid].false_positives += 1
                    precision_by_bid[target_bid].false_negatives += 1

            print(f"actual_bidding:{bidding_record_with_eos}\npredicted_bidding:{prediction_record}\n")
        if deal_record_count % 10 == 9:
            print_metrics(accuracy_by_position, precision_by_bid)


if __name__ == "__main__":
    tf.config.run_functions_eagerly(True)
    deal_records = load_deals(
        Path("/Users/frice/bridge/bid_learn/deals/validation.pickle"), allow_duplicate_deals=False
    )
    engine = BiddingInferenceEngine(model_path=Path("/Users/frice/Downloads/run_6"))
    confusion_evaluation(deal_records, engine)
