import unittest

from bridgebots import (
    BidMetadata,
    BidMetadataSchema,
    BiddingSuit,
    BoardRecord,
    BoardRecordSchema,
    Card,
    Commentary,
    CommentarySchema,
    Contract,
    ContractSchema,
    DealRecord,
    DealRecordSchema,
    DealSchema,
    Direction,
    deal_utils,
)


class TestSchemas(unittest.TestCase):
    # fmt: off
    play_record = [
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

    deal = deal_utils.from_pbn_deal(
        "N", "None", "W:98.KT5.J75.KJT84 K753.Q94.AT84.62 QJ6.AJ8762.62.73 AT42.3.KQ93.AQ95"
    )

    board_record = BoardRecord(
        bidding_record=["PASS", "1H", "2NT", "PASS", "3NT", "PASS", "PASS", "PASS"],
        raw_bidding_record=["p", "1H", "2N", "p", "3N", "p", "p", "p"],
        play_record=[Card.from_str(c) for c in play_record],
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
        commentary=[Commentary(bid_index=None, play_index=3, comment="Beautiful")],
    )

    def test_deal_schema(self):

        deal_schema = DealSchema()
        expected_deal_dict = {
            "dealer": "N",
            "ns_vulnerable": False,
            "ew_vulnerable": False,
            "hands": {
                "W": ["S9", "S8", "HK", "HT", "H5", "DJ", "D7", "D5", "CK", "CJ", "CT", "C8", "C4"],
                "N": ["SK", "S7", "S5", "S3", "HQ", "H9", "H4", "DA", "DT", "D8", "D4", "C6", "C2"],
                "E": ["SQ", "SJ", "S6", "HA", "HJ", "H8", "H7", "H6", "H2", "D6", "D2", "C7", "C3"],
                "S": ["SA", "ST", "S4", "S2", "H3", "DK", "DQ", "D9", "D3", "CA", "CQ", "C9", "C5"],
            },
        }
        self.assertEqual(expected_deal_dict, deal_schema.dump(self.deal))
        self.assertEqual(self.deal, deal_schema.load(expected_deal_dict))

    def test_commentary_schema(self):
        commentary = Commentary(bid_index=1, play_index=None, comment="caitlin: Hi all")
        commentary_schema = CommentarySchema()
        expected_commentary = {"bid_index": 1, "play_index": None, "comment": "caitlin: Hi all"}
        self.assertEqual(expected_commentary, commentary_schema.dump(commentary))
        self.assertEqual(commentary, commentary_schema.load(expected_commentary))

    def test_bid_metadata_schema(self):
        bid_metadata = BidMetadata(3, "2C", True, "!d or !h!s")
        bid_metadata_schema = BidMetadataSchema()
        expected_bid_metadata = {"bid_index": 3, "bid": "2C", "alerted": True, "explanation": "!d or !h!s"}
        self.assertEqual(expected_bid_metadata, bid_metadata_schema.dump(bid_metadata))
        self.assertEqual(bid_metadata, bid_metadata_schema.load(expected_bid_metadata))

    def test_contract_schema(self):
        contract = Contract(2, BiddingSuit.DIAMONDS, 1)
        contract_schema = ContractSchema()
        expected_contract = {"level": 2, "suit": "D", "doubled": 1}
        self.assertEqual(expected_contract, contract_schema.dump(contract))
        self.assertEqual(contract, contract_schema.load(expected_contract))

    def test_board_record_schema(self):
        board_record_schema = BoardRecordSchema()
        expected_board_record = {
            "bidding_record": ["PASS", "1H", "2NT", "PASS", "3NT", "PASS", "PASS", "PASS"],
            "raw_bidding_record": ["p", "1H", "2N", "p", "3N", "p", "p", "p"],
            "play_record": self.play_record,
            "declarer": "N",
            "contract": {"level": 3, "suit": "N", "doubled": 0},
            "score": -150,
            "tricks": 6,
            "scoring": None,
            "names": {"N": "smalark", "S": "PrinceBen", "E": "granola357", "W": "Forrest_"},
            "date": None,
            "event": None,
            "bidding_metadata": [
                {"bid_index": 2, "bid": "2NT", "alerted": False, "explanation": "Unusual No Trump: 2 5card minors"}
            ],
            "commentary": [{"bid_index": None, "play_index": 3, "comment": "Beautiful"}],
        }
        self.assertEqual(expected_board_record, board_record_schema.dump(self.board_record))
        self.assertEqual(self.board_record, board_record_schema.load(expected_board_record))

    def test_deal_record_schema(self):
        deal_record_schema = DealRecordSchema()
        deal_record = DealRecord(self.deal, [self.board_record])
        dumped_deal_record = deal_record_schema.dump(deal_record)
        loaded_deal_record = deal_record_schema.load(dumped_deal_record)
        self.assertEqual(self.deal, loaded_deal_record.deal)
        self.assertEqual(self.board_record, loaded_deal_record.board_records[0])
