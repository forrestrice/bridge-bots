import unittest
from pathlib import Path

from bridgebots import (
    BidMetadata,
    BiddingSuit,
    BoardRecord,
    Card,
    Commentary,
    Contract,
    Direction,
    Rank,
    Suit,
    build_lin_str,
    build_lin_url,
    parse_multi_lin,
    parse_single_lin,
)
from bridgebots.lin import (
    _determine_declarer,
    _parse_bidding_record,
    _parse_board_record,
    _parse_deal,
    _parse_lin_string,
    _parse_player_names,
    _parse_tricks,
)


class TestParseLin(unittest.TestCase):
    # fmt: off
    expected_play_record = [
            "H4", "H2", "HJ", "HA",
            "DA", "D4", "D3", "S3",
            "DJ", "D8", "D6", "S4",
            "DT", "D9", "D7", "S6",
            "D2", "C3", "DK", "SJ",
            "DQ", "C4", "D5", "S7",
            "S2", "H3", "SK", "SA",
            "HT", "HQ", "HK", "C2",
            "H5", "S5", "H9", "H8",
            "C5", "CT", "CA", "C6",
            "H7", "C7", "ST", "S8",
            "H6", "C9", "C8", "S9",
            "CQ", "CJ", "CK", "SQ",
        ]
    # fmt: on

    sample_lin = (
        "pn|PrinceBen,Forrest_,smalark,granola357|st||md|1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,"
        "SK5HADAJT52CJ9762,|rh||ah|Board 15|sv|n|mb|p|mb|1H|mb|2N|an|Unusual No Trump: 2 5card "
        "minors|mb|p|mb|3N|mb|p|mb|p|mb|p|pg||pc|H4|pc|H2|pc|HJ|pc|HA|pg||pc|DA|pc|D4|pc|D3|pc|S3|pg||pc"
        "|DJ|pc|D8|pc|D6|pc|S4|pg||pc|DT|pc|D9|pc|D7|pc|S6|pg||pc|D2|pc|C3|pc|DK|pc|SJ|pg||pc|DQ|pc|C4|pc"
        "|D5|pc|S7|pg||pc|S2|pc|H3|pc|SK|pc|SA|pg||pc|HT|pc|HQ|pc|HK|pc|C2|pg||pc|H5|pc|S5|pc|H9|pc|H8|pg"
        "||pc|C5|pc|CT|pc|CA|pc|C6|pg||pc|H7|pc|C7|pc|ST|pc|S8|pg||pc|H6|pc|C9|pc|C8|pc|S9|pg||pc|CQ|pc|CJ"
        "|pc|CK|pc|SQ|pg|| "
    )

    def test_parse_lin_line(self):
        lin_dict = _parse_lin_string(self.sample_lin)
        self.assertEqual(["1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,"], lin_dict["md"])
        self.assertEqual(["Board 15"], lin_dict["ah"])
        self.assertEqual(["n"], lin_dict["sv"])
        self.assertEqual(["p", "1H", "2N", "p", "3N", "p", "p", "p"], lin_dict["mb"])
        self.assertEqual([(2, "Unusual No Trump: 2 5card minors")], lin_dict["an"])
        self.assertEqual(self.expected_play_record, lin_dict["pc"])

    def test_parse_deal_three_hands(self):
        deal = _parse_deal({"md": ["1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,"], "sv": ["e"]})
        self.assertEqual(Direction.SOUTH, deal.dealer)
        self.assertTrue(deal.ew_vulnerable)
        self.assertFalse(deal.ns_vulnerable)
        self.assertEqual([Rank.QUEEN, Rank.EIGHT, Rank.TWO], deal.hands[Direction.SOUTH].suits[Suit.HEARTS])
        self.assertEqual([], deal.hands[Direction.WEST].suits[Suit.DIAMONDS])
        self.assertEqual([Rank.ACE, Rank.TEN, Rank.SEVEN], deal.hands[Direction.EAST].suits[Suit.SPADES])
        self.assertEqual([Rank.KING, Rank.EIGHT, Rank.FIVE, Rank.THREE], deal.hands[Direction.EAST].suits[Suit.CLUBS])

    def test_parse_deal_four_hands(self):
        deal = _parse_deal(
            {"md": ["4SQ853HK3DA43CJT72,SAKHT764DK52CAKQ5,SJ74HAQ95DQT7C986,ST962HJ82DJ986C43"], "sv": ["b"]}
        )
        self.assertEqual(Direction.EAST, deal.dealer)
        self.assertTrue(deal.ew_vulnerable)
        self.assertTrue(deal.ns_vulnerable)
        self.assertEqual(
            [Rank.QUEEN, Rank.EIGHT, Rank.FIVE, Rank.THREE], deal.hands[Direction.SOUTH].suits[Suit.SPADES]
        )
        self.assertEqual([Rank.KING, Rank.FIVE, Rank.TWO], deal.hands[Direction.WEST].suits[Suit.DIAMONDS])
        self.assertEqual([Rank.NINE, Rank.EIGHT, Rank.SIX], deal.hands[Direction.NORTH].suits[Suit.CLUBS])
        self.assertEqual([Rank.JACK, Rank.EIGHT, Rank.TWO], deal.hands[Direction.EAST].suits[Suit.HEARTS])

    def test_parse_bidding_record(self):
        raw_bidding_record = ["1N", "p", "p", "2C!", "p", "2D!", "d", "p", "p", "p"]
        bidding_record, bidding_metadata, contract = _parse_bidding_record(
            raw_bidding_record, {"an": [(0, "15-17"), (3, "!d or !h!s")]}
        )
        self.assertEqual(["1NT", "PASS", "PASS", "2C", "PASS", "2D", "X", "PASS", "PASS", "PASS"], bidding_record)
        expected_bidding_metadata = [
            BidMetadata(0, "1NT", False, "15-17"),
            BidMetadata(3, "2C", True, "!d or !h!s"),
            BidMetadata(5, "2D", True, None),
        ]
        self.assertEqual(expected_bidding_metadata, bidding_metadata)

    def test_parse_contract(self):
        raw_bidding_record = ["5C", "p", "p", "d", "p", "p", "r", "p", "p", "p"]
        bidding_record, bidding_metadata, contract = _parse_bidding_record(raw_bidding_record, {})
        self.assertEqual(["5C", "PASS", "PASS", "X", "PASS", "PASS", "XX", "PASS", "PASS", "PASS"], bidding_record)
        self.assertEqual([], bidding_metadata)
        self.assertEqual("5CXX", contract)

    def test_determine_declarer(self):
        deal = _parse_deal({"md": ["1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,"], "sv": ["e"]})
        bidding_record = ["PASS", "PASS", "1D", "PASS", "1S", "2H", "3C", "PASS", "3D", "PASS", "PASS", "PASS"]
        play_record = [Card.from_str("SA")]
        self.assertEqual(Direction.NORTH, _determine_declarer(play_record, bidding_record, deal))

    def test_parse_tricks_with_passout(self):
        self.assertEqual(0, _parse_tricks({}, Direction.EAST, "PASS", []))

    def test_parse_tricks_with_claim(self):
        self.assertEqual(10, _parse_tricks({"mc": ["10"]}, Direction.NORTH, "2S", []))

    def test_parse_tricks_with_invalid_number_of_cards(self):
        with self.assertRaises(ValueError):
            _parse_tricks({}, Direction.NORTH, "2S", [])

    def test_parse_tricks_from_play(self):
        play_record = [Card.from_str(card_str) for card_str in self.expected_play_record]
        self.assertEqual(6, _parse_tricks({}, Direction.NORTH, "3NT", play_record))
        self.assertEqual(10, _parse_tricks({}, Direction.EAST, "2C", play_record))

    def test_parse_player_names_four_players(self):
        self.assertEqual(
            {
                Direction.SOUTH: "PrinceBen",
                Direction.WEST: "Forrest_",
                Direction.NORTH: "smalark",
                Direction.EAST: "granola357",
            },
            _parse_player_names({"pn": ["PrinceBen,Forrest_,smalark,granola357"]}),
        )

    def test_parse_player_names_teams(self):
        self.assertEqual(
            {
                Direction.SOUTH: "Meckstroth",
                Direction.WEST: "Levin",
                Direction.NORTH: "Rodwell",
                Direction.EAST: "Weinstein",
            },
            _parse_player_names(
                {"pn": ["Meckstroth,Levin,Rodwell,Weinstein,Stansby,Hamman,Martel,Mahmood"], "qx": ["o46"]}
            ),
        )
        self.assertEqual(
            {
                Direction.SOUTH: "Stansby",
                Direction.WEST: "Hamman",
                Direction.NORTH: "Martel",
                Direction.EAST: "Mahmood",
            },
            _parse_player_names(
                {"pn": ["Meckstroth,Levin,Rodwell,Weinstein,Stansby,Hamman,Martel,Mahmood"], "qx": ["c46"]}
            ),
        )

    def test_parse_player_names_missing(self):
        self.assertEqual(
            {
                Direction.SOUTH: "SOUTH",
                Direction.WEST: "WEST",
                Direction.NORTH: "NORTH",
                Direction.EAST: "EAST",
            },
            _parse_player_names({}),
        )

    def test_parse_board_record(self):
        lin_dict = _parse_lin_string(self.sample_lin)
        deal = _parse_deal({"md": ["1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,"], "sv": ["e"]})
        expected_record = BoardRecord(
            bidding_record=["PASS", "1H", "2NT", "PASS", "3NT", "PASS", "PASS", "PASS"],
            raw_bidding_record=["p", "1H", "2N", "p", "3N", "p", "p", "p"],
            play_record=[Card.from_str(c) for c in self.expected_play_record],
            declarer=Direction.NORTH,
            contract=Contract.from_str("3NT"),
            declarer_vulnerable=False,
            tricks=6,
            scoring=None,
            names={
                Direction.NORTH: "smalark",
                Direction.SOUTH: "PrinceBen",
                Direction.EAST: "granola357",
                Direction.WEST: "Forrest_",
            },
            date=None,
            event=None,
            bidding_metadata=[
                BidMetadata(bid_index=2, bid="2NT", alerted=False, explanation="Unusual No Trump: 2 5card minors")
            ],
            commentary=None,
        )
        self.assertEqual(expected_record, _parse_board_record(lin_dict, deal))

    def test_parse_multi(self):
        lin_path = Path(__file__).parent / "resources" / "usbf_sf_14502.lin"
        deal_records = parse_multi_lin(lin_path)
        self.assertEqual(15, len(deal_records))
        self.assertEqual(2, len(deal_records[0].board_records))
        self.assertEqual(
            Commentary(bid_index=1, play_index=None, comment="caitlin: Hi all"),
            deal_records[0].board_records[0].commentary[0],
        )
        self.assertEqual(
            [Rank.QUEEN, Rank.TEN, Rank.FIVE], deal_records[0].deal.hands[Direction.NORTH].suits[Suit.HEARTS]
        )
        self.assertEqual(Contract(4, BiddingSuit.SPADES, 1), deal_records[7].board_records[0].contract)


class TestBuildLin(unittest.TestCase):
    deal_records = parse_single_lin(Path(__file__).parent / "resources" / "sample.lin")

    def test_build_lin_str(self):
        expected_lin_str = (
            "pn|PrinceBen,Forrest_,smalark,granola357|st||md|1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,"
            "SAT7HT94D984CK853|sv|n|mb|p|mb|1H|mb|2N|an|Unusual No Trump: 2 5card minors|mb|p|mb|3N|mb|p|mb|p|mb|p|pg||"
            "pc|H4|pc|H2|pc|HJ|pc|HA|pg||pc|DA|pc|D4|pc|D3|pc|S3|pg||pc|DJ|pc|D8|pc|D6|pc|S4|pg||pc|DT|pc|D9|pc|D7|pc"
            "|S6|pg||pc|D2|pc|C3|pc|DK|pc|SJ|pg||pc|DQ|pc|C4|pc|D5|pc|S7|pg||pc|S2|pc|H3|pc|SK|pc|SA|pg||pc|HT|pc|HQ"
            "|pc|HK|pc|C2|pg||pc|H5|pc|S5|pc|H9|pc|H8|pg||pc|C5|pc|CT|pc|CA|pc|C6|pg||pc|H7|pc|C7|pc|ST|pc|S8|pg||"
            "pc|H6|pc|C9|pc|C8|pc|S9|pg||pc|CQ|pc|CJ|pc|CK|pc|SQ|pg||pg||"
        )
        self.assertEqual(
            expected_lin_str, build_lin_str(self.deal_records[0].deal, self.deal_records[0].board_records[0])
        )

    def test_build_lin_url(self):
        expected_lin_url = (
            "https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CPrinceBen%2CForrest_%2Csmalark%2Cgranola357%7Cst"
            "%7C%7Cmd%7C1SQ982HQ82DKQ763CT%2CSJ643HKJ7653DCAQ4%2CSK5HADAJT52CJ9762%2CSAT7HT94D984CK853%7Csv%7Cn%7Cmb%"
            "7Cp%7Cmb%7C1H%7Cmb%7C2N%7Can%7CUnusual+No+Trump%3A+2+5card+minors%7Cmb%7Cp%7Cmb%7C3N%7Cmb%7Cp%7Cmb%7Cp%7C"
            "mb%7Cp%7Cpg%7C%7Cpc%7CH4%7Cpc%7CH2%7Cpc%7CHJ%7Cpc%7CHA%7Cpg%7C%7Cpc%7CDA%7Cpc%7CD4%7Cpc%7CD3%7Cpc%7CS3%7C"
            "pg%7C%7Cpc%7CDJ%7Cpc%7CD8%7Cpc%7CD6%7Cpc%7CS4%7Cpg%7C%7Cpc%7CDT%7Cpc%7CD9%7Cpc%7CD7%7Cpc%7CS6%7Cpg%7C%7C"
            "pc%7CD2%7Cpc%7CC3%7Cpc%7CDK%7Cpc%7CSJ%7Cpg%7C%7Cpc%7CDQ%7Cpc%7CC4%7Cpc%7CD5%7Cpc%7CS7%7Cpg%7C%7Cpc%7CS2%7C"
            "pc%7CH3%7Cpc%7CSK%7Cpc%7CSA%7Cpg%7C%7Cpc%7CHT%7Cpc%7CHQ%7Cpc%7CHK%7Cpc%7CC2%7Cpg%7C%7Cpc%7CH5%7Cpc%7CS5%7C"
            "pc%7CH9%7Cpc%7CH8%7Cpg%7C%7Cpc%7CC5%7Cpc%7CCT%7Cpc%7CCA%7Cpc%7CC6%7Cpg%7C%7Cpc%7CH7%7Cpc%7CC7%7Cpc%7CST%7C"
            "pc%7CS8%7Cpg%7C%7Cpc%7CH6%7Cpc%7CC9%7Cpc%7CC8%7Cpc%7CS9%7Cpg%7C%7Cpc%7CCQ%7Cpc%7CCJ%7Cpc%7CCK%7Cpc%7CSQ%7C"
            "pg%7C%7Cpg%7C%7C"
        )
        self.assertEqual(
            expected_lin_url, build_lin_url(self.deal_records[0].deal, self.deal_records[0].board_records[0])
        )
