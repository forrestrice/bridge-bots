import logging
from functools import partial
from pathlib import Path
from typing import Dict, List

from deal.deal import Card, Deal
from deal.deal_enums import BiddingSuit, Direction, Suit
from deal.table_record import TableRecord


def split_pbn(file_path: Path):
    with open(file_path, 'r') as pbn_file:
        records = []
        current_record = ''
        while True:
            line = pbn_file.readline()
            if line == '':
                return records
            elif line == '*\n':
                records.append(current_record.splitlines())
                current_record = ''
            else:
                current_record += line


def build_record_dict(record_strings: List[str]) -> Dict:
    record_dict = {}
    # Janky while loop to handle non bracketed lines
    i = 0
    while i < len(record_strings):
        record_string = record_strings[i]
        # if record_string == '' or record_string.startswith('%'):
        if not record_string.startswith('['):
            i += 1
            continue
        if '[' in record_string and ']' not in record_string:
            while ']' not in record_string:
                i += 1
                record_string = record_string + record_strings[i]
        record_string = record_string.replace('[', '').replace(']', '')
        key, value = record_string.split(maxsplit=1)
        record_dict[key] = value.replace('"', '')
        if key == 'Auction':
            auction_record = []
            i += 1
            while i < len(record_strings):
                auction_str = record_strings[i]
                if '[' in auction_str:
                    break
                auction_record.extend(auction_str.split())
                i += 1
            auction_record = auction_record[:-1]  # Replace 'AP' with 3 passes
            auction_record.extend(['Pass'] * 3)
            record_dict['bidding_record'] = auction_record

        elif key == 'Play':
            actions_record = []
            i += 1
            while i < len(record_strings):
                actions_str = record_strings[i]
                if '[' in actions_str:
                    break
                actions_record.append(actions_str.split())
                i += 1
            record_dict['play_record'] = actions_record
        else:
            i += 1
    return record_dict


def evaluate_card(trump_suit: Suit, suit_led: Suit, card: Card) -> int:
    score = card.rank.value[0]
    if card.suit == trump_suit:
        score += 100
    elif card.suit != suit_led:
        score -= 100
    return score


def sort_play_record(trick_records: List[List[str]], contract: str) -> List[Card]:
    if contract == '':
        logging.warning(f'empty contract, cannot determine play ordering: {trick_records}')
        return []
    if contract == 'Pass':
        return []
    try:
        trump_suit = BiddingSuit.from_str(contract[1:2]).to_suit()
        play_record = []
        start_index = 0
        for trick_record in trick_records:
            trick_cards = []
            for i in range(0, 4):
                card_index = (start_index + i) % 4
                card_str = trick_record[card_index]
                if card_str not in ['-', '--']:
                    card = Card.from_str(card_str)
                    play_record.append(card)
                    trick_cards.append(card)
            if len(trick_cards) == 4:
                suit_led = trick_cards[0].suit
                evaluator = partial(evaluate_card, trump_suit, suit_led)
                winning_index, winning_card = max(enumerate(trick_cards), key=lambda c: evaluator(c[1]))
                start_index = (start_index + winning_index) % 4
        return play_record
    except (IndexError, KeyError) as e:
        logging.warning(f'Malformed play record: {trick_records} exception:{e}')
        return []


def parse_table_record(record_dict: Dict) -> TableRecord:
    declarer_str = record_dict['Declarer']
    declarer = Direction.from_char(declarer_str) if declarer_str and declarer_str != '' else None
    bidding_record = record_dict.get('bidding_record') or []
    play_record_strings = record_dict.get('play_record') or []
    play_record = sort_play_record(play_record_strings, record_dict['Contract'])
    result_str = record_dict.get('Result')
    result = int(result_str) if result_str and result_str != '' else None

    return TableRecord(bidding_record=bidding_record,
                       play_record=play_record,
                       declarer=declarer,
                       contract=record_dict['Contract'],
                       tricks=result,
                       scoring=record_dict.get('Scoring'),
                       north=record_dict.get('North'),
                       south=record_dict.get('South'),
                       east=record_dict.get('East'),
                       west=record_dict.get('West'),
                       date=record_dict.get('Date'),
                       event=record_dict.get('Event'))


def parse_pbn(file_path: Path):
    records_strings = split_pbn(file_path)
    results = []
    for record_strings in records_strings:
        record_dict = build_record_dict(record_strings)
        # print(record_dict)
        deal = Deal.from_pbn_deal(record_dict['Dealer'], record_dict['Vulnerable'], record_dict['Deal'])
        table_record = parse_table_record(record_dict)
        results.append((deal, table_record))
    return results
