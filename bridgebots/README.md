# Bridgebots Core
This package contains the core components of the bridgebots library. The main focus is representing Contract Bridge concepts such as suits, ranks, cards, deals, bids, alerts, and scores. Data processing utilities such as a PBN parser are also included.

### Installation
`pip install bridgebots`

### Requirements
This package will attempt to maintain an extremely minimal set of external dependencies. As of this writing the only one is [marshmallow](https://github.com/marshmallow-code/marshmallow). 


## Building, Testing, and Contributing
Bridgebots uses [Poetry](https://python-poetry.org/) to manage building, testing, and publishing.

### Build
`poetry install` to install dependencies.

`poetry build` to build a wheel file.

### Test
`poetry run pytest` to run all unit tests.

### Contribute
Feel free to create issues or fork the repository and submit a pull-request. This is a hobby project, so they may not be addressed immediately.

### Style
Format all Python code using [Black](https://github.com/psf/black) with `--line-length 120`.

Use type-hints wherever possible.

Any added functionality should include unit tests.

## Guides
There are a few introductory guides with detailed examples available.
1. [Representing Bridge Components](https://forrestrice.com/posts/Announcing-Bridgebots/)
2. [Deal/Board Records and PBN files](https://forrestrice.com/posts/Introducing-Bridgebots-Part-2/)
3. LIN files and JSON (forthcoming)


## Examples
Examples are mostly provided in a python console format  to show the structure of data. Begin by importing:
```pycon
import bridgebots
from bridgebots import Card, Deal, DealRecord, DealRecordSchema, Direction, PlayerHand, Rank, Suit
from pathlib import Path 
from typing import List
```
### Deal
Construct a deal manually
```pycon
>>> hands = {
    Direction.NORTH: PlayerHand.from_string_lists(
        ["9", "8", "6", "4"], ["K", "Q", "7", "6", "3"], ["A", "K"], ["7", "3"]
    ),
    Direction.SOUTH: PlayerHand.from_string_lists(
        ["A", "K", "Q", "5"], ["A", "9", "4"], ["J", "5", "2"], ["K", "8", "4"]
    ),
    Direction.EAST: PlayerHand.from_string_lists(
        ["2"], ["J", "10", "8", "5", "2"], ["Q", "8", "7", "4", "3"], ["A", "10"]
    ),
    Direction.WEST: PlayerHand.from_string_lists(
        ["J", "10", "7", "3"], [], ["10", "9", "6"], ["Q", "J", "9", "6", "5", "2"]
    ),
}
>>> deal = Deal(dealer=Direction.EAST, ns_vulnerable=True, ew_vulnerable=False, hands=hands)
```

Construct a deal from a PBN style string
```python
>>> deal = bridgebots.from_pbn_deal("N", "EW", "W:Q8652.875.943.AT J97.AJ2.AKQ2.Q87 AK.QT943.87.9632 T43.K6.JT65.KJ54")
```

Interact with a Bridgebots deal
```pycon
>>> len(deal.hands[Direction.NORTH].suits[Suit.SPADES])
3

>>> deal.dealer, deal.ns_vulnerable, deal.ew_vulnerable
(NORTH, False, True)

>>> card = Card(Suit.DIAMONDS, Rank.KING)
>>> card in deal.player_cards[Direction.NORTH], card in deal.player_cards[Direction.SOUTH]
(True, False)

>>> card in deal.hands[Direction.NORTH].cards
True
```

### PBN
Parse a Version 1.0 PBN file into Bridgebots Deal and BoardRecord objects.
```pycon
>>> pbn_path = Path("bridgebots/tests/resources/sample.pbn")
>>> results: List[DealRecord] = bridgebots.parse_pbn(pbn_path)
>>> print(results[0].deal)
Deal(
	dealer=Direction.EAST, ns_vulnerable=True, ew_vulnerable=True
	North: PlayerHand(ST S8 S2 | H6 H2 | DT D7 D6 D4 | CK CQ C4 C2)
	South: PlayerHand(SA S9 S5 S4 | HA HT H9 H8 | DQ D8 | C8 C7 C5)
	East: PlayerHand(SK SQ SJ S7 | HQ HJ H7 H5 H4 | DA DJ | CA CT)
	West: PlayerHand(S6 S3 | HK H3 | DK D9 D5 D3 D2 | CJ C9 C6 C3)
)

>>> print(results[0].board_records[0])
BoardRecord(bidding_record=['1H', 'PASS', '1S', 'PASS', '2C', 'PASS', '2H', 'PASS', '2S', 'PASS', '3NT', 'PASS', 'PASS', 'PASS'], raw_bidding_record=['1H', 'Pass', '1S', '=1=', 'Pass', '2C', '!', 'Pass', '2H', '=2=', 'Pass', '2S', '=3=', 'Pass', '3NT', 'AP'], play_record=[CQ, CA, C8, C3, H4, HT, HK, H6, H3, H2, HQ, HA, C5, C6, CK, CT, D4, DJ, DQ, DK, CJ, C2, S7, C7, C9, C4, H5, S4, S6], declarer=WEST, contract=Contract(level=3, suit=NO_TRUMP, doubled=0), tricks=9, scoring='IMP;Cross', names={NORTH: '', SOUTH: '', EAST: '', WEST: ''}, date='2004.05.05', event='Cavendish Pairs Day 2', bidding_metadata=[BidMetadata(bid_index=2, bid='1S', alerted=False, explanation='0-4 !ss'), BidMetadata(bid_index=4, bid='2C', alerted=True, explanation=None), BidMetadata(bid_index=6, bid='2H', alerted=False, explanation='less than 8 points'), BidMetadata(bid_index=8, bid='2S', alerted=False, explanation='17+ with 4 !S')], commentary=None, score=600)
```
### LIN
#### Parsing
Parse a BBO LIN record.
```pycon
>>> lin_path = Path("bridgebots/tests/resources/sample.lin")
>>> results: List[DealRecord] = bridgebots.parse_single_lin(lin_path)
>>> print(results[0].deal)
Deal(
	dealer=Direction.SOUTH, ns_vulnerable=True, ew_vulnerable=False
	North: PlayerHand(SK S5 | HA | DA DJ DT D5 D2 | CJ C9 C7 C6 C2)
	South: PlayerHand(SQ S9 S8 S2 | HQ H8 H2 | DK DQ D7 D6 D3 | CT)
	East: PlayerHand(SA ST S7 | HT H9 H4 | D9 D8 D4 | CK C8 C5 C3)
	West: PlayerHand(SJ S6 S4 S3 | HK HJ H7 H6 H5 H3 |  | CA CQ C4)
)

>>> print(results[0].board_records[0])
BoardRecord(bidding_record=['PASS', '1H', '2NT', 'PASS', '3NT', 'PASS', 'PASS', 'PASS'], raw_bidding_record=['p', '1H', '2N', 'p', '3N', 'p', 'p', 'p'], play_record=[H4, H2, HJ, HA, DA, D4, D3, S3, DJ, D8, D6, S4, DT, D9, D7, S6, D2, C3, DK, SJ, DQ, C4, D5, S7, S2, H3, SK, SA, HT, HQ, HK, C2, H5, S5, H9, H8, C5, CT, CA, C6, H7, C7, ST, S8, H6, C9, C8, S9, CQ, CJ, CK, SQ], declarer=NORTH, contract=Contract(level=3, suit=NO_TRUMP, doubled=0), tricks=6, scoring=None, names={SOUTH: 'PrinceBen', WEST: 'Forrest_', NORTH: 'smalark', EAST: 'granola357'}, date=None, event=None, bidding_metadata=[BidMetadata(bid_index=2, bid='2NT', alerted=False, explanation='Unusual No Trump: 2 5card minors')], commentary=None, score=-300)
```
BBO multi-board LIN records are also supported using `parse_multi`
#### Creating
Create a BBO LIN string or URL
```pycon
>>> lin_path = Path("bridgebots/tests/resources/sample.lin")
>>> results: List[DealRecord] = bridgebots.parse_single_lin(lin_path)
>>> bridgebots.build_lin_str(results[0].deal, results[0].board_records[0])
pn|PrinceBen,Forrest_,smalark,granola357|st||md|1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,SAT7HT94D984CK853|sv|n|mb|p|mb|1H|mb|2N|an|Unusual No Trump: 2 5card minors|mb|p|mb|3N|mb|p|mb|p|mb|p|pg||pc|H4|pc|H2|pc|HJ|pc|HA|pg||pc|DA|pc|D4|pc|D3|pc|S3|pg||pc|DJ|pc|D8|pc|D6|pc|S4|pg||pc|DT|pc|D9|pc|D7|pc|S6|pg||pc|D2|pc|C3|pc|DK|pc|SJ|pg||pc|DQ|pc|C4|pc|D5|pc|S7|pg||pc|S2|pc|H3|pc|SK|pc|SA|pg||pc|HT|pc|HQ|pc|HK|pc|C2|pg||pc|H5|pc|S5|pc|H9|pc|H8|pg||pc|C5|pc|CT|pc|CA|pc|C6|pg||pc|H7|pc|C7|pc|ST|pc|S8|pg||pc|H6|pc|C9|pc|C8|pc|S9|pg||pc|CQ|pc|CJ|pc|CK|pc|SQ|pg||pg||

>>> bridgebots.build_lin_url(results[0].deal, results[0].board_records[0])
'https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CPrinceBen%2CForrest_%2Csmalark%2Cgranola357%7Cst%7C%7Cmd%7C1SQ982HQ82DKQ763CT%2CSJ643HKJ7653DCAQ4%2CSK5HADAJT52CJ9762%2CSAT7HT94D984CK853%7Csv%7Cn%7Cmb%7Cp%7Cmb%7C1H%7Cmb%7C2N%7Can%7CUnusual+No+Trump%3A+2+5card+minors%7Cmb%7Cp%7Cmb%7C3N%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CH4%7Cpc%7CH2%7Cpc%7CHJ%7Cpc%7CHA%7Cpg%7C%7Cpc%7CDA%7Cpc%7CD4%7Cpc%7CD3%7Cpc%7CS3%7Cpg%7C%7Cpc%7CDJ%7Cpc%7CD8%7Cpc%7CD6%7Cpc%7CS4%7Cpg%7C%7Cpc%7CDT%7Cpc%7CD9%7Cpc%7CD7%7Cpc%7CS6%7Cpg%7C%7Cpc%7CD2%7Cpc%7CC3%7Cpc%7CDK%7Cpc%7CSJ%7Cpg%7C%7Cpc%7CDQ%7Cpc%7CC4%7Cpc%7CD5%7Cpc%7CS7%7Cpg%7C%7Cpc%7CS2%7Cpc%7CH3%7Cpc%7CSK%7Cpc%7CSA%7Cpg%7C%7Cpc%7CHT%7Cpc%7CHQ%7Cpc%7CHK%7Cpc%7CC2%7Cpg%7C%7Cpc%7CH5%7Cpc%7CS5%7Cpc%7CH9%7Cpc%7CH8%7Cpg%7C%7Cpc%7CC5%7Cpc%7CCT%7Cpc%7CCA%7Cpc%7CC6%7Cpg%7C%7Cpc%7CH7%7Cpc%7CC7%7Cpc%7CST%7Cpc%7CS8%7Cpg%7C%7Cpc%7CH6%7Cpc%7CC9%7Cpc%7CC8%7Cpc%7CS9%7Cpg%7C%7Cpc%7CCQ%7Cpc%7CCJ%7Cpc%7CCK%7Cpc%7CSQ%7Cpg%7C%7Cpg%7C%7C'
```
[The Created URL](https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CPrinceBen%2CForrest_%2Csmalark%2Cgranola357%7Cst%7C%7Cmd%7C1SQ982HQ82DKQ763CT%2CSJ643HKJ7653DCAQ4%2CSK5HADAJT52CJ9762%2CSAT7HT94D984CK853%7Csv%7Cn%7Cmb%7Cp%7Cmb%7C1H%7Cmb%7C2N%7Can%7CUnusual+No+Trump%3A+2+5card+minors%7Cmb%7Cp%7Cmb%7C3N%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CH4%7Cpc%7CH2%7Cpc%7CHJ%7Cpc%7CHA%7Cpg%7C%7Cpc%7CDA%7Cpc%7CD4%7Cpc%7CD3%7Cpc%7CS3%7Cpg%7C%7Cpc%7CDJ%7Cpc%7CD8%7Cpc%7CD6%7Cpc%7CS4%7Cpg%7C%7Cpc%7CDT%7Cpc%7CD9%7Cpc%7CD7%7Cpc%7CS6%7Cpg%7C%7Cpc%7CD2%7Cpc%7CC3%7Cpc%7CDK%7Cpc%7CSJ%7Cpg%7C%7Cpc%7CDQ%7Cpc%7CC4%7Cpc%7CD5%7Cpc%7CS7%7Cpg%7C%7Cpc%7CS2%7Cpc%7CH3%7Cpc%7CSK%7Cpc%7CSA%7Cpg%7C%7Cpc%7CHT%7Cpc%7CHQ%7Cpc%7CHK%7Cpc%7CC2%7Cpg%7C%7Cpc%7CH5%7Cpc%7CS5%7Cpc%7CH9%7Cpc%7CH8%7Cpg%7C%7Cpc%7CC5%7Cpc%7CCT%7Cpc%7CCA%7Cpc%7CC6%7Cpg%7C%7Cpc%7CH7%7Cpc%7CC7%7Cpc%7CST%7Cpc%7CS8%7Cpg%7C%7Cpc%7CH6%7Cpc%7CC9%7Cpc%7CC8%7Cpc%7CS9%7Cpg%7C%7Cpc%7CCQ%7Cpc%7CCJ%7Cpc%7CCK%7Cpc%7CSQ%7Cpg%7C%7Cpg%7C%7C)

### JSON
Dump bridgebots DealRecord to JSON
```pycon
>>> lin_path = Path("bridgebots/tests/resources/sample.lin")
>>> results = bridgebots.parse_single_lin(lin_path)
>>> deal_record_schema = DealRecordSchema(many=True)
>>> deal_record_schema.dumps(results)
'[{"deal": {"dealer": "S", "ns_vulnerable": true, "ew_vulnerable": false, "hands": {"S": ["SQ", "S9", "S8", "S2", "HQ", "H8", "H2", "DK", "DQ", "D7", "D6", "D3", "CT"], "W": ["SJ", "S6", "S4", "S3", "HK", "HJ", "H7", "H6", "H5", "H3", "CA", "CQ", "C4"], "N": ["SK", "S5", "HA", "DA", "DJ", "DT", "D5", "D2", "CJ", "C9", "C7", "C6", "C2"], "E": ["SA", "ST", "S7", "HT", "H9", "H4", "D9", "D8", "D4", "CK", "C8", "C5", "C3"]}}, "board_records": [{"bidding_record": ["PASS", "1H", "2NT", "PASS", "3NT", "PASS", "PASS", "PASS"], "raw_bidding_record": ["p", "1H", "2N", "p", "3N", "p", "p", "p"], "play_record": ["H4", "H2", "HJ", "HA", "DA", "D4", "D3", "S3", "DJ", "D8", "D6", "S4", "DT", "D9", "D7", "S6", "D2", "C3", "DK", "SJ", "DQ", "C4", "D5", "S7", "S2", "H3", "SK", "SA", "HT", "HQ", "HK", "C2", "H5", "S5", "H9", "H8", "C5", "CT", "CA", "C6", "H7", "C7", "ST", "S8", "H6", "C9", "C8", "S9", "CQ", "CJ", "CK", "SQ"], "declarer": "N", "contract": "3N", "tricks": 6, "score": -300, "scoring": null, "names": {"S": "PrinceBen", "W": "Forrest_", "N": "smalark", "E": "granola357"}, "date": null, "event": null, "bidding_metadata": [{"bid_index": 2, "bid": "2NT", "alerted": false, "explanation": "Unusual No Trump: 2 5card minors"}], "commentary": null}]}]'
```

Parse a bridgebots JSON record
```pycon
>>> loaded_records = deal_record_schema.loads(deal_record_schema.dumps(results))
>>> loaded_records[0].deal
Deal(
	dealer=Direction.SOUTH, ns_vulnerable=True, ew_vulnerable=False
	North: PlayerHand(SK S5 | HA | DA DJ DT D5 D2 | CJ C9 C7 C6 C2)
	South: PlayerHand(SQ S9 S8 S2 | HQ H8 H2 | DK DQ D7 D6 D3 | CT)
	East: PlayerHand(SA ST S7 | HT H9 H4 | D9 D8 D4 | CK C8 C5 C3)
	West: PlayerHand(SJ S6 S4 S3 | HK HJ H7 H6 H5 H3 |  | CA CQ C4)
)
```
