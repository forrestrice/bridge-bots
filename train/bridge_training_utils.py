from deal.deal import Card
from deal.deal_enums import Rank, Suit, all_bids

sorted_cards = sorted([Card(suit, rank) for suit in Suit for rank in Rank])

bidding_vocab = {bid: index + 1 for index, bid in enumerate(all_bids)}
bidding_vocab["EOS"] = len(bidding_vocab)
bidding_vocab["PAD"] = 0
print(bidding_vocab)


def canonicalize_bid(bid: str) -> str:
    bid = bid.upper().strip("!")
    if bid.endswith("N"):
        bid = bid + "T"
    if bid == "DBL":
        bid = "X"
    elif bid == "REDBL":
        bid = "XX"
    return bid
