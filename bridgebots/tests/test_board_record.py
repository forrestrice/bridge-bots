import unittest

from bridgebots import BiddingSuit, Contract


class TestContract(unittest.TestCase):
    def test_contract_from_str(self):
        self.assertEqual(Contract(0, None, 0), Contract.from_str("PASS"))
        self.assertEqual(Contract(3, BiddingSuit.CLUBS, 0), Contract.from_str("3C"))
        self.assertEqual(Contract(2, BiddingSuit.NO_TRUMP, 1), Contract.from_str("2NTX"))
        self.assertEqual(Contract(6, BiddingSuit.DIAMONDS, 2), Contract.from_str("6DXX"))

    def test_contract_to_str(self):
        self.assertEqual("PASS", str(Contract(0, None, 0)))
        self.assertEqual("3C", str(Contract(3, BiddingSuit.CLUBS, 0)))
        self.assertEqual("2NTX", str(Contract(2, BiddingSuit.NO_TRUMP, 1)))
        self.assertEqual("6DXX", str(Contract(6, BiddingSuit.DIAMONDS, 2)))

    def test_invalid_contract(self):
        with self.assertRaises(ValueError):
            Contract.from_str("")
        with self.assertRaises(ValueError):
            Contract.from_str("3")
        with self.assertRaises(ValueError):
            Contract.from_str("3Z")
