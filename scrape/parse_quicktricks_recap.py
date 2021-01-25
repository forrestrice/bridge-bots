import csv
import operator
import re
import traceback
from functools import reduce
from pathlib import Path

from bs4 import BeautifulSoup

from deal.deal import Deal, PlayerHand
from deal.deal_enums import BiddingSuit, Direction, Rank, Suit


def parse_suit_cell(suit_cell):
    text = suit_cell.get_text()
    if text and '—' not in text:
        return text.split()
    else:
        return []


def parse_diagram_cell(hand_cell):
    suit_cells = hand_cell.find_all('td', class_='bchand')
    suit_string_lists = [parse_suit_cell(suit_cell) for suit_cell in suit_cells]
    suit_string_lists.reverse()
    return PlayerHand.from_string_lists(*suit_string_lists)


def parse_label_cell(label_cell):
    dealer_str = label_cell.find('span', class_='bclabeldealer').get_text()
    vul_str = label_cell.find('span', class_='bclabelvul').get_text()
    dealer = [direction for direction in list(Direction) if direction.name.lower() in dealer_str.lower()][0]

    if "Both" in vul_str:
        ns_vul = True
        ew_vul = True
    elif "N-S" in vul_str:
        ns_vul = True
        ew_vul = False
    elif "E-W" in vul_str:
        ns_vul = True
        ew_vul = False
    else:
        ns_vul = False
        ew_vul = False
    return dealer, ns_vul, ew_vul


def parse_diagram_table(diagram_table):
    label_cell = diagram_table.find('td', class_='bchdlabels')
    north_cell = diagram_table.find('td', class_='bchd')
    east_cell = diagram_table.find('td', class_='bchd2c')
    west_cell = diagram_table.find('td', class_='bchd2a')
    south_cell = diagram_table.find('td', class_='bchd3b')
    hand_cards = {
        Direction.NORTH: parse_diagram_cell(north_cell),
        Direction.SOUTH: parse_diagram_cell(south_cell),
        Direction.EAST: parse_diagram_cell(east_cell),
        Direction.WEST: parse_diagram_cell(west_cell),
    }
    dealer, ns_vul, ew_vul = parse_label_cell(label_cell)
    return Deal(dealer, ns_vul, ew_vul, hand_cards)


nonint_scores = {'Ave', 'Ave-', 'Ave+', 'Pass', ''}


def parse_section_row(section_row):
    try:
        try:
            contract = section_row.find('td', class_='bcstcontract').get_text()
            declarer = section_row.find('td', class_='bcstdeclarer').get_text()
            made_str = section_row.find('td', class_='bcstmade').get_text().replace(u'\u2212', '-')
        except AttributeError:
            contract = 'unknown'
            declarer = 'unknown'
            made_str = 'unknown'
        score_ns_str = section_row.find('td', class_='bcstscorens').get_text().replace(u'\u2212', '-')
        score_ew_str = section_row.find('td', class_='bcstscoreew').get_text().replace(u'\u2212', '-')
        try:
            mp_ns = float(section_row.find('td', class_='bcstmpns').get_text())
            mp_ew = float(section_row.find('td', class_='bcstmpew').get_text())
        except (AttributeError, ValueError):
            mp_ns = None
            mp_ew = None
        try:
            imp_ns = float(section_row.find('td', class_='bcstimpns').get_text().replace(u'\u2212', '-'))
            imp_ew = float(section_row.find('td', class_='bcstimpew').get_text().replace(u'\u2212', '-'))
        except (AttributeError, ValueError):
            imp_ns = None
            imp_ew = None

        players_ns = section_row.find('td', class_='bcstpairns').get_text()
        players_ew = section_row.find('td', class_='bcstpairew').get_text()
        if '-' not in players_ew and '-' not in players_ns:
            return None

        if contract == 'NP':
            return None
        if not nonint_scores.isdisjoint({score_ns_str, score_ew_str}) or 'F' in score_ew_str or 'F' in score_ns_str:
            score_ns = score_ns_str
            score_ew = score_ew_str
        else:
            if score_ns_str:
                score_ns = int(score_ns_str)
                score_ew = -int(score_ns_str)
            else:
                score_ns = -int(score_ew_str)
                score_ew = int(score_ew_str)

        if made_str:
            made = made_str if made_str == 'unknown' else int(made_str)
        else:
            made = None
        return {
            "contract": contract,
            "declarer": declarer,
            "made": made,
            "score_ns": score_ns,
            "score_ew": score_ew,
            "mp_ns": mp_ns,
            "mp_ew": mp_ew,
            "imp_ns": imp_ns,
            "imp_ew": imp_ew,
            "players_n": players_ns.split("-")[1],
            "players_s": players_ns.split("-")[2],
            "players_e": players_ew.split("-")[1],
            "players_w": players_ew.split("-")[2],
        }
    except (AttributeError, IndexError) as e:
        traceback.print_exc()
        print(f"{e} exception parsing row {section_row}")


section_regex = re.compile("bcstsection")


def parse_section_body(section_body):
    section_rows = section_body.find_all('tr')
    section_name_tr = section_body.find('tr', {'class': section_regex})
    if section_name_tr:
        section_name = section_name_tr.getText()
        section_rows = section_rows[1:]
    else:
        section_name = "unnamed"
    return section_name.strip("Section").strip(), [parse_section_row(section_row) for section_row in section_rows]


def parse_score_table(score_table):
    section_bodies = score_table.find_all('tbody', class_='bcst')
    return {name: rows for name, rows in [parse_section_body(section_body) for section_body in section_bodies]}


def parse_recap_file(recap_file_path):
    with open(recap_file_path, 'r') as recap_file:
        try:
            recap_contents = recap_file.read()
            recap_soup = BeautifulSoup(recap_contents, 'html.parser')

            diagram_tables = recap_soup.find_all('table', class_='bchd')
            deals = [parse_diagram_table(diagram_table) for diagram_table in diagram_tables]

            score_tables = recap_soup.find_all('table', class_='bcst')
            scores = [parse_score_table(score_table) for score_table in score_tables]
            return list(zip(deals, scores))
        except AttributeError as e:
            traceback.print_exc()
            print(f"Error {e} parsing {recap_file_path}. Skipping")
            return []


direction_mappings = {
    'players_e': Direction.EAST,
    'players_w': Direction.WEST,
    'players_n': Direction.NORTH,
    'players_s': Direction.SOUTH,
}


def target_player_to_direction(row, target_player):
    for direction_label, direction in direction_mappings.items():
        if row[direction_label] == target_player:
            return direction
    return None


roles = [('declarer', 'offense'), ('defense_lead', 'defense'), ('dummy', 'offense'), ('defense_third', 'defense')]


def target_direction_role(target_direction, row, deal):
    if row['contract'] == 'Pass':
        role_direction = deal.dealer
    elif row['contract'] == '' or row['contract'] == 'unknown':
        return 'unknown', 'unknown'
    else:
        role_direction = Direction.from_char(row['declarer'])
    for role in roles:
        if role_direction == target_direction:
            return role
        else:
            role_direction = role_direction.next()


direction_score_mapping = {
    Direction.EAST: ("mp_ew", "imp_ew"),
    Direction.WEST: ("mp_ew", "imp_ew"),
    Direction.NORTH: ("mp_ns", "imp_ns"),
    Direction.SOUTH: ("mp_ns", "imp_ns"),
}

percentage_scoring_days = [
    '2020-07-06',
    '2020-08-24',
    '2020-07-13',
    '2020-08-31',
    '2020-08-03',
    '2020-07-20',
    '2020-08-17',
    '2020-08-10',
    '2020-10-12',
    '2020-08-31',
    '2020-07-13',
    '2020-08-24',
    '2020-07-06',
    '2020-07-27',
]


def score_section(target_direction, num_rows, row, play_date):
    if str(play_date) in percentage_scoring_days:
        mp = row[direction_score_mapping[target_direction][0]]
        return mp, "matchpoints"
    if row.get("imp_ns") is not None:
        imp = row[direction_score_mapping[target_direction][1]]
        return imp, "imps"
    else:
        try:
            mp = row[direction_score_mapping[target_direction][0]]
            return mp / (num_rows - 1), "matchpoints"
        except TypeError as e:
            print("error scoring:", e, mp, num_rows - 1)


combined_sections = {'2019-11-18': [['B'], ['E', 'F']],
                     '2019-05-20': [['D'], ['B', 'C', 'E']],  # TODO some boards are just c and e
                     '2019-11-04': [['B'], ['E', 'F']],
                     '2020-09-21': [['A', 'B'], ['C', 'D']],
                     '2019-02-04': [['B'], ['E', 'F']],
                     '2018-04-23': [['B', 'E', 'F']]
                     }

skip_days = ['2019-05-20']

symbol_mapping = {
    '♠': BiddingSuit.SPADES,
    '♥': BiddingSuit.HEARTS,
    '♦': BiddingSuit.DIAMONDS,
    '♣': BiddingSuit.CLUBS,
    'NT': BiddingSuit.NO_TRUMP
}


def parse_contract(contract_str):
    if 'unknown' == contract_str or '' == contract_str:
        return 'unknown', 'unknown', 'unknown', 'unknown'
    if 'Pass' == contract_str:
        return 0, 'pass', False, False
    print(contract_str, contract_str.encode('UTF-8'))
    double_count = contract_str.count('×')
    contract_str = contract_str.strip('×')
    contract_str = contract_str.replace(u'\u202f', u'\u2009')
    contract_str = contract_str.replace(u'\u0809', u'\u2009')
    print(len(contract_str), contract_str.split(u'\u2009'), len(contract_str.split(u'\u2009')))
    level, suit_symbol = contract_str.split(u'\u2009')
    return level, symbol_mapping[suit_symbol], double_count == 1, double_count == 2


def get_shape(deal, target_direction):
    hand = deal.hands[target_direction]
    shape = [len(hand.suits[suit]) for suit in Suit]
    shape.reverse()
    shape_str = ''.join([str(s) for s in shape])
    shape.sort()
    shape.reverse()
    sorted_shape_str = ''.join([str(s) for s in shape])
    return shape_str, sorted_shape_str


hcp_mapping = {
    Rank.ACE: 4,
    Rank.KING: 3,
    Rank.QUEEN: 2,
    Rank.JACK: 1,
}


def get_hcp(deal, target_direction):
    hand = deal.hands[target_direction]
    hcp = 0
    for suit_ranks in hand.suits.values():
        for rank, hcp_value in hcp_mapping.items():
            if rank in suit_ranks:
                hcp += hcp_value
    return hcp


def get_record_hcp(deal, target_direction):
    my_hcp = get_hcp(deal, target_direction)
    partner_hcp = get_hcp(deal, target_direction.next().next())
    return my_hcp, my_hcp + partner_hcp


def process_recap_file(records, recap_path, target_player):
    print(f"PARSING:{recap_path}")
    play_date = recap_path.parent.name
    if play_date in skip_days:
        return
    deal_scores = parse_recap_file(recap_path)
    if not deal_scores:
        print(f"no deals found for {recap_path}. Skipping")
        return
    day_combined_sections = combined_sections.get(play_date)
    deal_sections = []
    for deal, score in deal_scores:
        if day_combined_sections:
            processed_sections = []
            for section_group in day_combined_sections:
                grouped_rows = [score[i] for i in section_group if i in score]
                combined_rows = reduce(operator.add, grouped_rows, [])
                processed_sections.append(combined_rows)
        else:
            processed_sections = score.values()
        deal_sections.append((deal, processed_sections))

    # Compute the max number of players in each section (some boards have a fewer, but mp scores are not reduced)
    max_section_lengths = [0] * len(deal_sections[0][1])
    for deal, section_list in deal_sections:
        for i, section in enumerate(section_list):
            max_section_lengths[i] = max(max_section_lengths[i], len(section))

    for deal, section_list in deal_sections:
        for section_index, section in enumerate(section_list):
            for row in section:
                if not row:
                    continue
                target_direction = target_player_to_direction(row, target_player)
                if target_direction:
                    role, team_role = target_direction_role(target_direction, row, deal)
                    score, scoring_form = score_section(target_direction, max_section_lengths[section_index], row,
                                                        play_date)
                    if scoring_form == 'matchpoints' and score > 1 and play_date not in percentage_scoring_days:
                        print("wrong score for row:", row, score, row["mp_ns"], row["mp_ew"])
                    contract_level, contract_suit, doubled, redoubled = parse_contract(row['contract'])
                    suits_shape, sorted_shape = get_shape(deal, target_direction)
                    hcp, team_hcp = get_record_hcp(deal, target_direction)
                    record = {
                        'role': role,
                        'team_role': team_role,
                        'score': score,
                        'contract_level': contract_level,
                        'contract_suit': contract_suit,
                        'doubled': doubled,
                        'redoubled': redoubled,
                        'play_date': play_date,
                        'scoring_form': scoring_form,
                        'suits_shape': suits_shape,
                        'sorted_shape': sorted_shape,
                        'hcp': hcp,
                        'team_hcp': team_hcp
                    }
                    records.append(record)
                    break


error_files = [
    '/Users/frice/bridge/results/2020-05-25/recap.html',
]

records = []
for recap_path in Path('/Users/frice/bridge/results').rglob('*recap.html'):
    # for recap_path_str in error_files:
    #   recap_path = Path(recap_path_str)
    process_recap_file(records, recap_path, 'Rice')

print(f'processed {len(records)} records')

results_path = '/Users/frice/bridge/results/all_qt_results.csv'
with open(results_path, 'w', newline='') as csvfile:
    fieldnames = ['role', 'team_role', 'score', 'contract_level', 'contract_suit', 'doubled', 'redoubled', 'play_date',
                  'scoring_form', 'suits_shape', 'sorted_shape', 'hcp', 'team_hcp']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        writer.writerow(record)

print(f'DONE. Wrote csv to {results_path}')
