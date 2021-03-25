from pathlib import Path
from pprint import pprint
from typing import Dict, List

from deal.deal import Deal
from deal.deal_enums import Direction
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
        record_string = record_string.replace('[', '').replace(']', '')
        key, value = record_string.split(maxsplit=1)
        record_dict[key] = value.replace('"', '')
        if key in ['Auction', 'Play']:
            actions_record = []
            i += 1
            # Read action lines until we reach a new key
            while i < len(record_strings):
                actions_str = record_strings[i]
                if '[' in actions_str:
                    break
                actions_record.extend(actions_str.split())
                i += 1
            action_key = 'bidding_record' if key == 'Auction' else 'play_record'
            record_dict[action_key] = actions_record
        else:
            i += 1
    return record_dict


def parse_deal(record_dict: Dict) -> Deal:
    vuln_str = record_dict['Vulnerable']
    ns_vuln = False
    ew_vuln = False
    if vuln_str == 'NS':
        ns_vuln = True
    elif vuln_str == 'EW':
        ew_vuln = True
    elif vuln_str == 'All':
        ns_vuln = True
        ew_vuln = True

    dealer_str = record_dict['Dealer']
    dealer = Direction.from_char(dealer_str)

    deal_str = record_dict['Deal']
    pass


def parse_table_record(record_dict: Dict) -> TableRecord:
    pass


def parse_pbn(file_path: Path):
    records_strings = split_pbn(file_path)
    record_dict = build_record_dict(records_strings[0])
    deal, table_record = parse_deal(record_dict), parse_table_record(record_dict)
    return deal, table_record
    # return [parse_record_string(record_string) for record_string in record_strings]


d, tr = parse_pbn(Path('/Users/frice/bridge/results/usbc/usbc_2012.pbn'))
pprint(d)
