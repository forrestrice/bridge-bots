import pathlib
from bs4 import BeautifulSoup
import bridge
import re


base_path = '/Users/frice/PycharmProjects/bridge/results/'
dealer_pattern = re.compile('(.*) Deals')


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

    #print(row_1)
    print("dealer:{}".format(dealer))
    print("ns_vuln:{}".format(ns_vulnerable))
    print("ew_vuln:{}".format(ew_vulnerable))
    #print(row_2)
    #print(row_3)

def parse_recap(recap_file_path):
    if str(recap_file_path) == '/Users/frice/PycharmProjects/bridge/results/2018-02-19/recap_e_20180219.html':
        recap_page = open(recap_file_path, 'r').read()
        recap_soup = BeautifulSoup(recap_page, 'html.parser')
        hand_tables = recap_soup.find_all('table', class_='bchd')
        for index, hand_table in enumerate(hand_tables):
            print('hand {}'.format(index))

            parse_hand_table(hand_table)


for results_day_path in pathlib.Path(base_path).iterdir():
    print(results_day_path)
    for recap_file in results_day_path.iterdir():
        print('\t'+ str(recap_file))
        parse_recap(recap_file)





