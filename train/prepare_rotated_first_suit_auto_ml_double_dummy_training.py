import logging
import pickle
import random

from bridgebots.deal import Card
from bridgebots.deal_enums import BiddingSuit, Direction, Rank, Suit
from train.generate_rotation_permutations import RotationPermutation
from train.streaming_csv_writer import StreamingCsvWriter

logging.basicConfig(level=logging.INFO)
sorted_cards = sorted([Card(suit, rank) for suit in Suit for rank in Rank])
card_headers = []
for direction in Direction:
    for card in sorted_cards:
        card_headers.append(direction.name[0] + str(card.rank.value) + card.suit.name[0])

csv_headers = ["split"] + card_headers + ["tricks"]

suit_file_path = "./data/double_dummy/rotated_suit_auto_ml.csv"
suit_training_writer = StreamingCsvWriter(suit_file_path)
suit_training_writer.write_row(csv_headers)

notrump_file_path = "./data/double_dummy/rotated_notrump_auto_ml.csv"
notrump_training_writer = StreamingCsvWriter(notrump_file_path)
notrump_training_writer.write_row(csv_headers)

splits = ["TRAIN", "VALIDATE", "TEST"]
split_weights = [0.8, 0.1, 0.1]


def generate_deals():
    with open("../results/double_dummy/all_deals.pickle", "rb") as dd_pickle_file:
        while True:
            try:
                yield pickle.load(dd_pickle_file)
            except EOFError:
                break


deal_count = 0
for ddd in generate_deals():
    deal_data = [random.choices(splits, split_weights)[0]]
    for rotation in RotationPermutation.all_rotations:
        score_direction = rotation[0]
        for score_suit in BiddingSuit:
            score = ddd.dd_score.scores[score_direction][score_suit]
            if score_suit == BiddingSuit.NO_TRUMP:
                trump_first_permutations = RotationPermutation.all_suit_permutations
                row_writer = notrump_training_writer
            else:
                playing_suit = Suit(score_suit.value)
                trump_first_permutations = [
                    perm for perm in RotationPermutation.all_suit_permutations if perm.suits[0] == playing_suit
                ]
                row_writer = suit_training_writer

            for trump_first_permutation in trump_first_permutations:
                row_data = deal_data.copy()
                for rotation_direction in rotation:
                    row_data.extend(trump_first_permutation.build_deck_mask(ddd.deal.player_cards[rotation_direction]))
                row_data.append(score)
                row_writer.write_row(row_data)

    deal_count += 1
    if deal_count % 1000 == 0:
        logging.info("processed %s deals", deal_count)

suit_training_writer.close()
notrump_training_writer.close()
