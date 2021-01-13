from bs4 import BeautifulSoup

from deal.deal import Deal, PlayerHand
from deal.deal_enums import Direction


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


def parse_section_row(section_row):
    contract = section_row.find('td', class_='bcstcontract').get_text()
    declarer = section_row.find('td', class_='bcstdeclarer').get_text()
    made_str = section_row.find('td', class_='bcstmade').get_text()
    score_ns_str = section_row.find('td', class_='bcstscorens').get_text()
    score_ew_str = section_row.find('td', class_='bcstscoreew').get_text()
    mp_ns = section_row.find('td', class_='bcstmpns').get_text()
    mp_ew = section_row.find('td', class_='bcstmpew').get_text()
    players_ns = section_row.find('td', class_='bcstpairns').get_text()
    players_ew = section_row.find('td', class_='bcstpairew').get_text()

    if 'Ave' in score_ew_str or 'Ave' in score_ns_str:
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
        made = int(made_str.replace(u'\u2212', '-'))
    else:
        made = None
    return {
        "contract": contract,
        "declarer": declarer,
        "made": made,
        "score_ns": score_ns,
        "score_ew": score_ew,
        "mp_ns": float(mp_ns),
        "mp_ew": float(mp_ew),
        "players_ns": players_ns,
        "players_ew": players_ew,
    }


def parse_section_body(section_body):
    section_rows = section_body.find_all('tr')[1:]
    return [parse_section_row(section_row) for section_row in section_rows]


def parse_score_table(score_table):
    section_bodies = score_table.find_all('tbody', class_='bcst')
    return [parse_section_body(section_body) for section_body in section_bodies]


def parse_recap_file(recap_file_path):
    with open(recap_file_path, 'r') as recap_file:
        recap_contents = recap_file.read()
        recap_soup = BeautifulSoup(recap_contents, 'html.parser')

        diagram_tables = recap_soup.find_all('table', class_='bchd')
        print(f'found {len(diagram_tables)} diagram tables')
        deals = [parse_diagram_table(diagram_table) for diagram_table in diagram_tables]

        score_tables = recap_soup.find_all('table', class_='bcst')
        print(f'found {len(score_tables)} score_tables')
        scores = [parse_score_table(score_table) for score_table in score_tables]
        return deals, scores


deals, scores = parse_recap_file('/Users/frice/bridge/results/2020-12-14/recap.html')
print(len(deals), len(scores))
