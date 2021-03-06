import logging
import pickle
import random
from typing import Dict

from bridgebots.deal import Card
from bridgebots.deal_enums import BiddingSuit, Direction, Rank, Suit
from train.streaming_csv_writer import StreamingCsvWriter

logging.basicConfig(level=logging.INFO)
sorted_cards = sorted([Card(suit, rank) for suit in Suit for rank in Rank])
card_headers = []
for direction in Direction:
    for card in sorted_cards:
        card_headers.append(direction.name[0] + str(card.rank.value) + card.suit.name[0])

csv_headers = ["split"] + card_headers + ["direction", "suit", "tricks"]

file_path = "./data/double_dummy/auto_ml.csv"
training_writer = StreamingCsvWriter(file_path)
training_writer.write_row(csv_headers)

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
        direction_data = deal_data.copy()
        direction_data.append(direction.value)
        scores: Dict[BiddingSuit, int] = ddd.dd_score.scores[direction]
        for bidding_suit in BiddingSuit:
            row_data = direction_data.copy()
            row_data.append(bidding_suit.value)
            row_data.append(scores[bidding_suit])
            assert 212 == len(row_data)
            training_writer.write_row(row_data)

    deal_count += 1
    if deal_count % 1000 == 0:
        logging.info("processed %s deals", deal_count)


training_writer.close()
