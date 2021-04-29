from typing import Optional

legal_bids = {
    "PASS",
    "X",
    "XX",
    "1C",
    "1D",
    "1H",
    "1S",
    "1NT",
    "2C",
    "2D",
    "2H",
    "2S",
    "2NT",
    "3C",
    "3D",
    "3H",
    "3S",
    "3NT",
    "4C",
    "4D",
    "4H",
    "4S",
    "4NT",
    "5C",
    "5D",
    "5H",
    "5S",
    "5NT",
    "6C",
    "6D",
    "6H",
    "6S",
    "6NT",
    "7C",
    "7D",
    "7H",
    "7S",
    "7NT",
}


def canonicalize_bid(bid: str) -> Optional[str]:
    bid = bid.upper()
    if bid.endswith("N"):
        bid = bid + "T"
    if bid == "DBL":
        bid = "X"
    elif bid == "REDBL":
        bid = "XX"
    return bid if bid in legal_bids else None
