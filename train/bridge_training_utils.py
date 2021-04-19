from bridgebots.deal import Card
from bridgebots.deal_enums import Rank, Suit

SORTED_CARDS = sorted([Card(suit, rank) for suit in Suit for rank in Rank])

ALL_BIDS = [str(level) + suit_char for level in range(1, 8) for suit_char in ["C", "D", "H", "S", "NT"]]
ALL_BIDS.extend(["PASS", "X", "XX"])

BIDDING_VOCAB = {bid: index + 1 for index, bid in enumerate(ALL_BIDS)}
BIDDING_VOCAB["EOS"] = len(BIDDING_VOCAB)
BIDDING_VOCAB["PAD"] = 0


def canonicalize_bid(bid: str) -> str:
    bid = bid.upper().strip("!")
    if bid.endswith("N"):
        bid = bid + "T"
    if bid == "DBL":
        bid = "X"
    elif bid == "REDBL":
        bid = "XX"
    return bid
