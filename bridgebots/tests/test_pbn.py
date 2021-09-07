import unittest
from pathlib import Path

from bridgebots.board_record import BidMetadata
from bridgebots.deal_enums import Direction, Rank, Suit
from bridgebots.pbn import _build_record_dict, _parse_bidding_record, _sort_play_record, parse_pbn


class TestParsePbnFile(unittest.TestCase):
    def test_parse_file(self):
        sample_pbn_path = Path(__file__).parent / "resources" / "sample.pbn"
        records = parse_pbn(sample_pbn_path)
        self.assertEqual(3, len(records))

        deal_1, board_record_1 = records[0].deal, records[0].board_records[0]
        self.assertEqual(True, deal_1.ns_vulnerable)
        self.assertEqual(True, deal_1.ew_vulnerable)
        self.assertEqual(Direction.EAST, deal_1.dealer)
        self.assertEqual(
            [Rank.KING, Rank.QUEEN, Rank.JACK, Rank.SEVEN], deal_1.hands[Direction.EAST].suits[Suit.SPADES]
        )
        self.assertEqual(
            [
                "1H",
                "Pass",
                "1S",
                "=1=",
                "Pass",
                "2C",
                "!",
                "Pass",
                "2H",
                "=2=",
                "Pass",
                "2S",
                "=3=",
                "Pass",
                "3NT",
                "AP",
            ],
            board_record_1.raw_bidding_record,
        )

        self.assertEqual(
            ["1H", "PASS", "1S", "PASS", "2C", "PASS", "2H", "PASS", "2S", "PASS", "3NT", "PASS", "PASS", "PASS"],
            board_record_1.bidding_record,
        )

        self.assertEqual(
            [
                BidMetadata(2, "1S", False, "0-4 !ss"),
                BidMetadata(4, "2C", True, None),
                BidMetadata(6, "2H", False, "less than 8 points"),
                BidMetadata(8, "2S", False, "17+ with 4 !S"),
            ],
            board_record_1.bidding_metadata,
        )

        self.assertEqual(
            [
                "CQ",
                "CA",
                "C8",
                "C3",
                "H4",
                "HT",
                "HK",
                "H6",
                "H3",
                "H2",
                "HQ",
                "HA",
                "C5",
                "C6",
                "CK",
                "CT",
                "D4",
                "DJ",
                "DQ",
                "DK",
                "CJ",
                "C2",
                "S7",
                "C7",
                "C9",
                "C4",
                "H5",
                "S4",
                "S6",
            ],
            [str(card) for card in board_record_1.play_record],
        )
        self.assertEqual(Direction.WEST, board_record_1.declarer)
        self.assertEqual("3NT", board_record_1.contract)
        self.assertEqual(9, board_record_1.tricks)
        self.assertEqual("IMP;Cross", board_record_1.scoring)
        self.assertEqual("2004.05.05", board_record_1.date)
        self.assertEqual("Cavendish Pairs Day 2", board_record_1.event)

        deal_2, board_record_2 = records[1].deal, records[1].board_records[0]
        self.assertEqual(
            (
                "{ Indonesians Franky Karwur and Denny Sacul, recent winners of the IOC Grand Prix in Lausanne and "
                "Rhodes Olympiad finalists in 1996, are mainstays of their  consistent national team. True gentlemen at"
                " and away from the table, they focus on partnership and error-free bridge. 51 VP out of first, they "
                "need a win here to stay in the hunt. Their opponents, Wubbo de Boer and Bauke Muller of Holland, "
                "Bermuda Bowl champs in 1993, are a further 24 behind . Our first deal, a partscore, is played "
                "successfully in diamonds at every table but one (Auken/von Arnim fail in 3C). Karwur/Sacul achieve par"
                " [datum is N/S minus 110] at 3D. However, getting there is half the fun, as the old Greyhound Bus "
                "adverts used to boast. Muller\\\\'s (probably necessary) balanced takeout double is hardly a classic, "
                "and de Boer shows no mercy, bidding both his majors on very slender values. Sacul (1D showed 2+ cards)"
                " saves the day by converting 3C to 3D, expecting 2/3 in dummy on the auction. Muller leads a "
                "challenging low heart but Sacul puts up the king: plus 110. {Your host for this match, John "
                "Carruthers} }"
            ),
            board_record_2.commentary,
        )
        self.assertEqual(board_record_2.names[Direction.NORTH], "Wubbo De Boer")
        self.assertEqual(board_record_2.names[Direction.SOUTH], "Bauke Muller")
        self.assertEqual(board_record_2.names[Direction.EAST], "Denny Sacul")
        self.assertEqual(board_record_2.names[Direction.WEST], "Franky Karwur")


class TestPbnRecordDict(unittest.TestCase):
    def test_ignore_non_key_lines(self):
        pbn_strings = [
            "% PBN 1.0",
            "Random String",
            '[Contract "3NT"]',
        ]
        record_dict = _build_record_dict(pbn_strings)
        self.assertEqual({"Contract": "3NT"}, record_dict)

    def test_auction(self):
        pbn_strings = ['[Auction "S"]', "1D X 2S Pass", "Pass 2NT Pass 3NT", "Pass Pass Pass"]
        record_dict = _build_record_dict(pbn_strings)
        expected = {
            "Auction": "S",
            "bidding_record": ["1D", "X", "2S", "Pass", "Pass", "2NT", "Pass", "3NT", "Pass", "Pass", "Pass"],
        }
        self.assertEqual(expected, record_dict)

    def test_auction_with_alerts(self):
        pbn_strings = ['[Auction "N"]', "1D =1= X ! AP"]
        record_dict = _build_record_dict(pbn_strings)
        expected = {"Auction": "N", "bidding_record": ["1D", "=1=", "X", "!", "AP"]}
        self.assertEqual(expected, record_dict)

    def test_play(self):
        pbn_strings = ['[Play "N"]', "S6 S3 ST SQ", "C9 C2 C5 CQ", "CT C3 CA CK"]
        record_dict = _build_record_dict(pbn_strings)
        expected = {
            "Play": "N",
            "play_record": [["S6", "S3", "ST", "SQ"], ["C9", "C2", "C5", "CQ"], ["CT", "C3", "CA", "CK"]],
        }
        self.assertEqual(expected, record_dict)

    def test_partial_play(self):
        pbn_strings = ['[Play "N"]', "S6 S3 ST SQ", "C9 C2 C5 CQ", "CT C3 CA CK", "*", '[NextTag "Foo"]']
        record_dict = _build_record_dict(pbn_strings)
        expected = {
            "Play": "N",
            "play_record": [["S6", "S3", "ST", "SQ"], ["C9", "C2", "C5", "CQ"], ["CT", "C3", "CA", "CK"]],
            "NextTag": "Foo",
        }
        self.assertEqual(expected, record_dict)

    def test_commentary_at_end(self):
        pbn_strings = [
            '[Contract "3NT"]',
            "{Brad Moss of USA and Fred Gitelman of Canada won the Cavendish",
            "Teams earlier this week, and with one 27-board session to go,",
            "they are in front again.",
            "}",
        ]
        record_dict = _build_record_dict(pbn_strings)
        self.assertEqual(
            {
                "Contract": "3NT",
                "Commentary": (
                    "{Brad Moss of USA and Fred Gitelman of Canada won the Cavendish Teams earlier this week, and with "
                    "one 27-board session to go, they are in front again. }"
                ),
            },
            record_dict,
        )

    def test_commentary_in_middle(self):
        pbn_strings = [
            '[Contract "3NT"]',
            "{Brad Moss of USA and Fred Gitelman of Canada won the Cavendish",
            "Teams earlier this week, and with one 27-board session to go,",
            "they are in front again.",
            "}",
            '[Declarer "W"]',
        ]
        record_dict = _build_record_dict(pbn_strings)
        self.assertEqual(
            {
                "Contract": "3NT",
                "Commentary": (
                    "{Brad Moss of USA and Fred Gitelman of Canada won the Cavendish Teams earlier this week, and with "
                    "one 27-board session to go, they are in front again. }"
                ),
                "Declarer": "W",
            },
            record_dict,
        )


class TestPbnPlayRecord(unittest.TestCase):
    def test_sort_suit_play_record(self):
        trick_records = [["H6", "HK", "HQ", "H5"], ["CT", "C4", "D9", "CK"], ["H2", "H3", "DJ", "H8"]]
        hearts_play_record = _sort_play_record(trick_records, "3H")
        hearts_play_strings = [str(card) for card in hearts_play_record]
        self.assertEqual(["H6", "HK", "HQ", "H5", "C4", "D9", "CK", "CT", "H8", "H2", "H3", "DJ"], hearts_play_strings)
        diamonds_play_record = _sort_play_record(trick_records, "2D")
        diamonds_play_strings = [str(card) for card in diamonds_play_record]
        self.assertEqual(
            ["H6", "HK", "HQ", "H5", "C4", "D9", "CK", "CT", "DJ", "H8", "H2", "H3"], diamonds_play_strings
        )

    def test_sort_notrump_play_record(self):
        trick_records = [["H6", "HK", "HQ", "C3"], ["CT", "C4", "D9", "CK"], ["H2", "H3", "DJ", "S8"]]
        nt_play_record = _sort_play_record(trick_records, "2NT")
        nt_play_strings = [str(card) for card in nt_play_record]
        self.assertEqual(["H6", "HK", "HQ", "C3", "C4", "D9", "CK", "CT", "S8", "H2", "H3", "DJ"], nt_play_strings)
        pass

    def test_placeholder_symbols(self):
        trick_records = [["H6", "HK", "HQ", "C3"], ["CT", "C4", "D9", "CK"], ["H2", "-", "--", "S8"]]
        nt_play_record = _sort_play_record(trick_records, "2NT")
        nt_play_strings = [str(card) for card in nt_play_record]
        self.assertEqual(["H6", "HK", "HQ", "C3", "C4", "D9", "CK", "CT", "S8", "H2"], nt_play_strings)

    def test_sort_pass_out(self):
        self.assertEqual([], _sort_play_record([], "Pass"))
        self.assertEqual([], _sort_play_record([], "PASS"))

    def test_handle_malformed_play_record(self):
        self.assertEqual([], _sort_play_record([], "junk"))
        self.assertEqual([], _sort_play_record([["H3"]], "2NT"))


class TestPbnBiddingRecord(unittest.TestCase):
    def test_bidding_record_without_annotations(self):
        raw_auction = ["Pass", "1D", "X", "XX", "1S", "X", "Pass", "2C", "2H", "Pass", "Pass", "Pass"]
        bidding_record, bidding_metadata = _parse_bidding_record(raw_auction, {})
        self.assertEqual(
            ["PASS", "1D", "X", "XX", "1S", "X", "PASS", "2C", "2H", "PASS", "PASS", "PASS"], bidding_record
        )
        self.assertEqual([], bidding_metadata)

    def test_bidding_metadata_without_notes(self):
        raw_auction = ["Pass", "1D", "X", "=0=", "Pass", "Pass", "Pass"]
        bidding_record, bidding_metadata = _parse_bidding_record(raw_auction, {})
        self.assertEqual(["PASS", "1D", "X", "PASS", "PASS", "PASS"], bidding_record)
        self.assertEqual([BidMetadata(2, "X", False, "=0=")], bidding_metadata)

    def test_bidding_metadata_with_notes(self):
        raw_auction = ["Pass", "1D", "=1=", "X", "=2=", "Pass", "Pass", "Pass"]
        record_dict = {"Note_1": "2+", "Note_2": "Majors"}
        bidding_record, bidding_metadata = _parse_bidding_record(raw_auction, record_dict)
        self.assertEqual(["PASS", "1D", "X", "PASS", "PASS", "PASS"], bidding_record)
        self.assertEqual([BidMetadata(1, "1D", False, "2+"), BidMetadata(2, "X", False, "Majors")], bidding_metadata)

    def test_alert(self):
        raw_auction = ["Pass", "1D", "!", "X", "!", "Pass", "Pass", "Pass"]
        bidding_record, bidding_metadata = _parse_bidding_record(raw_auction, {})
        self.assertEqual(["PASS", "1D", "X", "PASS", "PASS", "PASS"], bidding_record)
        self.assertEqual([BidMetadata(1, "1D", True, None), BidMetadata(2, "X", True, None)], bidding_metadata)

    def test_bidding_metadata_with_duplicate_notes(self):
        raw_auction = ["1C", "2NT", "=0=", "!", "3H", "=0=", "=1=", "pass", "3S", "pass", "3NT", "pass", "pass", "pass"]
        bidding_record, bidding_metadata = _parse_bidding_record(raw_auction, {"Note_1": "Spades"})
        self.assertEqual(["1C", "2NT", "3H", "PASS", "3S", "PASS", "3NT", "PASS", "PASS", "PASS"], bidding_record)
        self.assertEqual(
            [BidMetadata(1, "2NT", True, "=0="), BidMetadata(2, "3H", False, "=0= | Spades")], bidding_metadata
        )

    def test_bidding_record_with_all_pass(self):
        raw_auction = ["1C", "1S", "AP"]
        bidding_record, bidding_metadata = _parse_bidding_record(raw_auction, {})
        self.assertEqual(["1C", "1S", "PASS", "PASS", "PASS"], bidding_record)
        self.assertEqual([], bidding_metadata)
