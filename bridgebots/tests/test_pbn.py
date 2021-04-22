import unittest
from pathlib import Path

from bridgebots.pbn import _build_record_dict, _sort_play_record, parse_pbn


class TestParsePbnFile(unittest.TestCase):
    def test_parse_file(self):
        sample_pbn_path = Path(__file__).parent / "sample.pbn"
        records = parse_pbn(sample_pbn_path)
        self.assertEqual(3, len(records))


class TestPbnRecordDict(unittest.TestCase):
    def test_ignore_non_key_lines(self):
        pbn_strings = [
            "% PBN 1.0" "{Brad Moss of USA and Fred Gitelman of Canada won the Cavendish",
            "Teams earlier this week, and with one 27-board session to go,",
            "they are in front again.",
            "}",
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

    def test_auction_with_all_pass(self):
        pbn_strings = ['[Auction "N"]', "1D X AP"]
        record_dict = _build_record_dict(pbn_strings)
        expected = {
            "Auction": "N",
            "bidding_record": ["1D", "X", "Pass", "Pass", "Pass"],
        }
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
