import unittest

from bridgebots.lin import _parse_lin_string


class TestParseLin(unittest.TestCase):
    def test_parse_lin_line(self):
        lin_line = "pn|PrinceBen,Forrest_,smalark,granola357|st||md|1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4," \
                   "SK5HADAJT52CJ9762,|rh||ah|Board 15|sv|n|mb|p|mb|1H|mb|2N|an|Unusual No Trump: 2 5card " \
                   "minors|mb|p|mb|3N|mb|p|mb|p|mb|p|pg||pc|H4|pc|H2|pc|HJ|pc|HA|pg||pc|DA|pc|D4|pc|D3|pc|S3|pg||pc" \
                   "|DJ|pc|D8|pc|D6|pc|S4|pg||pc|DT|pc|D9|pc|D7|pc|S6|pg||pc|D2|pc|C3|pc|DK|pc|SJ|pg||pc|DQ|pc|C4|pc" \
                   "|D5|pc|S7|pg||pc|S2|pc|H3|pc|SK|pc|SA|pg||pc|HT|pc|HQ|pc|HK|pc|C2|pg||pc|H5|pc|S5|pc|H9|pc|H8|pg" \
                   "||pc|C5|pc|CT|pc|CA|pc|C6|pg||pc|H7|pc|C7|pc|ST|pc|S8|pg||pc|H6|pc|C9|pc|C8|pc|S9|pg||pc|CQ|pc|CJ" \
                   "|pc|CK|pc|SQ|pg|| "
        lin_dict = _parse_lin_string(lin_line)
        self.assertEqual(["1SQ982HQ82DKQ763CT,SJ643HKJ7653DCAQ4,SK5HADAJT52CJ9762,"], lin_dict["md"])
        self.assertEqual(["Board 15"], lin_dict["ah"])
        self.assertEqual(["n"], lin_dict["sv"])
        self.assertEqual(["p", "1H", "2N", "p", "3N", "p", "p", "p"], lin_dict["mb"])
        self.assertEqual([(2, "Unusual No Trump: 2 5card minors")], lin_dict["an"])
        self.assertEqual(
            [
                "H4",
                "H2",
                "HJ",
                "HA",
                "DA",
                "D4",
                "D3",
                "S3",
                "DJ",
                "D8",
                "D6",
                "S4",
                "DT",
                "D9",
                "D7",
                "S6",
                "D2",
                "C3",
                "DK",
                "SJ",
                "DQ",
                "C4",
                "D5",
                "S7",
                "S2",
                "H3",
                "SK",
                "SA",
                "HT",
                "HQ",
                "HK",
                "C2",
                "H5",
                "S5",
                "H9",
                "H8",
                "C5",
                "CT",
                "CA",
                "C6",
                "H7",
                "C7",
                "ST",
                "S8",
                "H6",
                "C9",
                "C8",
                "S9",
                "CQ",
                "CJ",
                "CK",
                "SQ",
            ],
            lin_dict["pc"],
        )
