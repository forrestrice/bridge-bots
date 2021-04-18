import logging
import logging
import pickle
import random
from typing import Dict

from deal.deal import Card
from deal.deal_enums import BiddingSuit, Direction, Rank, Suit
from train.streaming_csv_writer import StreamingCsvWriter

logging.basicConfig(level=logging.INFO)
sorted_cards = sorted([Card(suit, rank) for suit in Suit for rank in Rank])
card_headers = []
for direction in Direction:
    for card in sorted_cards:
        card_headers.append(direction.name[0] + str(card.rank.value) + card.suit.name[0])

csv_headers = card_headers + ["direction", "CT", "DT", "HT", "ST", "NTT"]

data_dir = "./data/double_dummy/"
splits = ["training.csv", "validation.csv", "test.csv"]
training_writers = []
split_weights = [0.7, 0.1, 0.2]

file_paths = [data_dir + file_name for file_name in splits]

for file_path in file_paths:
    training_writer = StreamingCsvWriter(file_path)
    training_writers.append(training_writer)
    training_writer.write_row(csv_headers)


def generate_deals():
    with open("../results/double_dummy/all_deals.pickle", "rb") as dd_pickle_file:
        while True:
            try:
                yield pickle.load(dd_pickle_file)
            except EOFError:
                break


deal_count = 0
for ddd in generate_deals():

    training_writer = random.choices(training_writers, split_weights)[0]
    deal_data = []
    for direction in Direction:
        direction_data = []
        player_cards = sorted(ddd.deal.hands[direction].cards)
        player_card_index = 0
        for card in sorted_cards:
            if player_card_index < len(player_cards) and card == player_cards[player_card_index]:
                player_card_index += 1
                direction_data.append(1)
            else:
                direction_data.append(0)
        assert 13 == sum(direction_data)
        deal_data.extend(direction_data)

    # Write 4 rows, one for the double dummy score of each direction
    for direction in Direction:
        row_data = deal_data.copy()
        row_data.append(direction.value)
        scores: Dict[BiddingSuit, int] = ddd.dd_score.scores[direction]
        for bidding_suit in BiddingSuit:
            row_data.append(scores[bidding_suit])

        assert 214 == len(row_data)
        training_writer.write_row(row_data)

    deal_count += 1
    if deal_count % 1000 == 0:
        logging.info("processed %s deals", deal_count)

for training_writer in training_writers:
    training_writer.close()
