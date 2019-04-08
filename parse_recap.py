import pathlib
from bs4 import BeautifulSoup
from bridge import PlayerHand,Hand
import re

from hand_dao import HandDao

base_path = '/home/forrest/bridge/results/'
dealer_pattern = re.compile('(.*) Deals')
hand_dao = HandDao()
processed_files = hand_dao.get_processed_files()


def parse_suit(suit_row):
    suit_text = suit_row.find('td', class_='bchand').text
    if suit_text == '—':
        return []
    else:
        return suit_text.split()

def parse_player_hand(player_hand_table):
    suit_rows = player_hand_table.find_all('tr')
    spades = parse_suit(suit_rows[0])
    hearts = parse_suit(suit_rows[1])
    diamonds = parse_suit(suit_rows[2])
    clubs = parse_suit(suit_rows[3])
    return PlayerHand(clubs, diamonds, hearts, spades)


def parse_hand_table(hand_table):
    row_1 = hand_table.find('tr', class_='bchd1')
    row_2 = hand_table.find('tr', class_='bchd2')
    row_3 = hand_table.find('tr', class_='bchd3')

    dealer_text = row_1.find('span', class_='bclabeldealer').text
    dealer = dealer_pattern.match(dealer_text).group(1)

    ns_vulnerable = False
    ew_vulnerable = False
    vuln_text = row_1.find('span', class_='bclabelvul').text
    if vuln_text == 'N-S Vul':
        ns_vulnerable = True
    elif vuln_text == 'E-W Vul':
        ew_vulnerable = True
    elif vuln_text == 'Both Vul':
        ew_vulnerable = True
        ns_vulnerable = True

    north_hand = parse_player_hand(row_1.find('table', class_=['bchand','bchandhl']))
    ew_hands = row_2.find_all('table', class_=['bchand','bchandhl'])
    west_hand = parse_player_hand(ew_hands[0])
    east_hand = parse_player_hand(ew_hands[1])
    south_hand = parse_player_hand(row_3.find('table', class_=['bchand','bchandhl']))
    return Hand(dealer, ns_vulnerable,ew_vulnerable, north_hand, east_hand, south_hand, west_hand)


def parse_recap(recap_file_path):
    # if str(recap_file_path) == '/Users/frice/PycharmProjects/bridge/results/2017-02-13/recap_b_20170213.html':
    recap_page = open(recap_file_path, 'r').read()
    recap_soup = BeautifulSoup(recap_page, 'html.parser')
    hand_tables = recap_soup.find_all('table', class_='bchd')
    for index, hand_table in enumerate(hand_tables):
        # if (index == 8):  # testing
        # print('hand {}'.format(index))
        try:
            hand = parse_hand_table(hand_table)
            hand_dao.write_hand(hand)
        except Exception as error:
            print("Error processing hand {0} of file {1}".format(index, recap_file_path))


# print(hand)



for results_day_path in pathlib.Path(base_path).iterdir():
    print(results_day_path)
    for recap_file in results_day_path.iterdir():
        recap_file_string = str(recap_file)
        if recap_file_string not in processed_files:
            try:
                print('\t'+ str(recap_file))
                parse_recap(recap_file)
                hand_dao.record_porcessed_file(recap_file_string)
            except Exception as error:
                print("Encountered exception while processing {0}: {1}".format(recap_file_string, error))
        else:
            print("Already processed {0}".format(recap_file_string))

hand_dao.close()



