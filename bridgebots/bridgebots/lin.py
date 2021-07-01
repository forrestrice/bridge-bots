import re
import urllib.parse
from collections import defaultdict
from functools import partial
from typing import Dict, List, Tuple

from bridgebots.bids import canonicalize_bid
from bridgebots.board_record import BidMetadata, BoardRecord, Commentary
from bridgebots.deal import Card, Deal, PlayerHand
from bridgebots.deal_enums import BiddingSuit, Direction, Rank, Suit

DECK_SET = frozenset({Card(suit, rank) for rank in Rank for suit in Suit})


def parse_lin_string(lin_str: str):
    lin_dict = defaultdict(list)
    while not (lin_str.isspace() or lin_str == ""):
        key, value, lin_str = lin_str.split("|", maxsplit=2)
        if key == "an":
            lin_dict[key].append((len(lin_dict["mb"]) - 1, value))  # Track which bid this announcement applies to
        elif key == "nt":
            bid_index = None
            play_index = None
            if "pc" in lin_dict:
                play_index = len(lin_dict["pc"]) - 1
            else:
                bid_index = len(lin_dict["mb"]) - 1
            lin_dict[key].append(Commentary(bid_index, play_index, value))
        else:
            lin_dict[key].append(value)
    return lin_dict


_char_to_dealer_direction = {"1": Direction.SOUTH, "2": Direction.WEST, "3": Direction.NORTH, "4": Direction.EAST}
suit_char_regex = re.compile("[SHDC]")

NS_VULNERABLE_STRINGS = {"b", "n"}
EW_VULNERABLE_STRINGS = {"b", "e"}


def _parse_deal(lin_dict: dict) -> Deal:
    dealer_char = lin_dict["md"][0][0]
    dealer = _char_to_dealer_direction[dealer_char]
    holdings_str = lin_dict["md"][0][1:].strip(",")  # remove trailing comma
    holdings = holdings_str.split(",")
    # 1S98643HAJT54DCJT4,SQJTH98DKT7542C76,S5HKQ3DJ93CAKQ832,
    # OR
    # 4SJ5H9DAT862CQ8752,SKQT94HAK73DQ4C93,S872HQT5DJ97CAT64,SA63HJ8642DK53CKJ
    players_suit_holdings = [suit_char_regex.split(holding)[1:] for holding in holdings]
    player_hands = {}
    current_direction = Direction.SOUTH
    for suit_holdings in players_suit_holdings:
        suit_holdings.reverse()
        suit_holdings_lists = [list(suit_holding) for suit_holding in suit_holdings]
        player_hands[current_direction] = PlayerHand.from_string_lists(*suit_holdings_lists)
        current_direction = current_direction.next()

    if len(player_hands) == 3:
        held_cards = {card for player_hand in player_hands.values() for card in player_hand.cards}
        remaining_cards = DECK_SET - held_cards
        player_hands[current_direction] = PlayerHand.from_cards(remaining_cards)

    ns_vulnerable = lin_dict["sv"][0] in NS_VULNERABLE_STRINGS
    ew_vulnerable = lin_dict["sv"][0] in EW_VULNERABLE_STRINGS
    deal = Deal(dealer, ns_vulnerable, ew_vulnerable, player_hands)
    return deal


def _parse_bidding_record(raw_bidding_record: List[str], lin_dict: Dict) -> Tuple[List[str], List[BidMetadata]]:
    bidding_record = []
    bidding_metadata = []
    bid_announcements = {bid_index: announcement for (bid_index, announcement) in lin_dict.get("an", [])}
    for bid_index, bid in enumerate(raw_bidding_record):
        canonical_bid = canonicalize_bid(bid)
        if canonical_bid is None:
            raise ValueError(f"encountered unknown bid:{bid}")
        bidding_record.append(canonical_bid)
        alerted = "!" in bid
        if alerted or bid_index in bid_announcements:
            bidding_metadata.append(BidMetadata(bid_index, canonical_bid, alerted, bid_announcements.get(bid_index)))
    return bidding_record, bidding_metadata


pass_out_auction = ["PASS"] * 4


def _determine_declarer(play_record: List[Card], bidding_record: List[str], deal: Deal) -> Direction:
    if bidding_record == pass_out_auction:
        return deal.dealer
    first_card = play_record[0]
    leader = next(direction for direction in Direction if first_card in deal.player_cards[direction])
    return leader.previous()


# TODO shared with pbn
def _evaluate_card(trump_suit: Suit, suit_led: Suit, card: Card) -> int:
    """
    :return: Score a card on its ability to win a trick given the trump suit and the suit that was led to the trick
    """
    score = card.rank.value[0]
    if card.suit == trump_suit:
        score += 100
    elif card.suit != suit_led:
        score -= 100
    return score


def _parse_tricks(
    lin_dict: dict,
    declarer: Direction,
    contract: str,
    play_record: List[Card],
) -> int:
    if "mc" in lin_dict:
        return int(lin_dict["mc"][0])

    if len(play_record) != 52:
        raise ValueError(f"Not enough cards played: {len(play_record)}")

    trump_suit = BiddingSuit.from_str(contract[1:2]).to_suit()
    tricks = [play_record[i : i + 4] for i in range(0, 52, 4)]
    lead_direction = declarer.next()
    offense_directions = [declarer, declarer.partner()]
    offense_tricks = 0
    for trick in tricks:
        suit_led = trick[0].suit
        evaluator = partial(_evaluate_card, trump_suit, suit_led)
        winning_index, winning_card = max(enumerate(trick), key=lambda c: evaluator(c[1]))
        lead_direction = Direction((lead_direction.value + winning_index) % 4)
        if lead_direction in offense_directions:
            offense_tricks += 1
    return offense_tricks


def _parse_player_names(lin_dict: Dict) -> Dict[Direction, str]:
    if "pn" in lin_dict:
        player_names = lin_dict["pn"][0].split(",")
        if "qx" in lin_dict and len(player_names) > 4:
            if lin_dict["qx"][0].startswith("o"):
                player_names = player_names[0:4]
            else:
                player_names = player_names[4:8]
    else:
        player_names = ["SOUTH", "WEST", "NORTH", "EAST"]
    direction = Direction.SOUTH
    name_dict = {}
    for i in range(4):
        name_dict[direction] = player_names[i]
        direction = direction.next()
    return name_dict


def _parse_board_record(lin_dict: Dict, deal: Deal) -> BoardRecord:
    player_names = _parse_player_names(lin_dict)
    raw_bidding_record = lin_dict["mb"]
    bidding_record, bidding_metadata = _parse_bidding_record(raw_bidding_record, lin_dict)
    contract = bidding_record[-4]
    play_record = [Card.from_str(cs) for cs in lin_dict["pc"]]
    declarer = _determine_declarer(play_record, bidding_record, deal)
    tricks = _parse_tricks(lin_dict, declarer, contract, play_record)

    return BoardRecord(
        bidding_record=bidding_record,
        raw_bidding_record=raw_bidding_record,
        play_record=play_record,
        declarer=declarer,
        contract=contract,
        tricks=tricks,
        scoring=None,
        north=player_names[Direction.NORTH],
        south=player_names[Direction.SOUTH],
        east=player_names[Direction.EAST],
        west=player_names[Direction.WEST],
        date=None,
        event=None,
        bidding_metadata=bidding_metadata,
        commentary=lin_dict.get("nt"),
    )


def parse_single():
    with open("/Users/frice/bridge/lin_parse/sample_hand.lin") as lin_file:
        for line in lin_file:
            lin_dict = parse_lin_string(line)
            deal = _parse_deal(lin_dict)
            board_record = _parse_board_record(lin_dict, deal)
            return [(deal, board_record)]


def parse_multi() -> List[Tuple[Deal, BoardRecord]]:
    # https://www.bridgebase.com/tools/handviewer.html?bbo=y&linurl=https://www.bridgebase.com/tools/vugraph_linfetch.php?id=14502
    with open("/Users/frice/bridge/lin_parse/usbf_sf_14502.lin") as lin_file:
        title_line = parse_lin_string(lin_file.readline())
        results = parse_lin_string(lin_file.readline())
        player_names = parse_lin_string(lin_file.readline())
        board_strings = []
        current_board = ""
        for line in lin_file:
            if line.startswith("qx") or line == "":
                if current_board != "":
                    board_strings.append(current_board)
                current_board = ""
            current_board = current_board + line

        # Create single-line LIN for each record
        board_single_strings = [board_string.replace("\n", "") for board_string in board_strings]
        records = []
        for board_single_string in board_single_strings:
            lin_dict = parse_lin_string(board_single_string)
            lin_dict["pn"] = player_names["pn"]
            deal = _parse_deal(lin_dict)
            board_record = _parse_board_record(lin_dict, deal)
            records.append((deal, board_record))
        return records




bid_translation = {"PASS": "p", "DBL": "d", "RDBL": "r"}


def build_bidding_str(board_record: BoardRecord) -> str:
    metadata_by_index = {metadata.bid_index: metadata for metadata in board_record.bidding_metadata}
    bidding_str = ""
    for bid_index, bid in enumerate(board_record.bidding_record):
        translated_bid = bid_translation.get(bid, bid).replace("NT", "N")
        explanation_str = ""
        if bid_index in metadata_by_index:
            bid_metadata = metadata_by_index.get(bid_index)
            if bid_metadata.alerted:
                translated_bid += "!"
            if bid_metadata.explanation is not None:
                explanation_str = f"an|{bid_metadata.explanation}|"
        bidding_str += f"mb|{translated_bid}|{explanation_str}"
    bidding_str += "pg||"
    return bidding_str


def build_play_str(board_record):
    play_str = ""
    trick_count = 0
    for card in board_record.play_record:
        play_str += f"pc|{card}|"
        trick_count = (trick_count + 1) % 4
        if trick_count == 0:
            play_str += "pg||"
    if len(board_record.play_record) < 52:
        play_str += f"mc|{board_record.tricks}|"
    return play_str



def build_lin_str(deal: Deal, board_record: BoardRecord) -> str:
    print(deal, board_record)
    lin_dealer = (deal.dealer.value + 2) % 4 + 1
    holding_direction = Direction.SOUTH
    player_holding_strings = []
    for i in range(4):
        player_hand = deal.hands[holding_direction]
        player_holding_str = ""
        for suit in reversed(Suit):
            player_holding_str += suit.abbreviation() + "".join(
                [rank.abbreviation() for rank in player_hand.suits[suit]]
            )
        player_holding_strings.append(player_holding_str)
        holding_direction = holding_direction.next()
    if deal.ew_vulnerable and deal.ns_vulnerable:
        vuln_str = "b"
    elif deal.ew_vulnerable:
        vuln_str = "e"
    elif deal.ns_vulnerable:
        vuln_str = "n"
    else:
        vuln_str = "o"

    bidding_str = build_bidding_str(board_record)
    play_str = build_play_str(board_record)

    lin_str = ""
    lin_str += f"pn|{board_record.south},{board_record.west},{board_record.north},{board_record.east}|"
    lin_str += f"st||md|{lin_dealer}{','.join(player_holding_strings)}|"
    lin_str += f"sv|{vuln_str}|"
    lin_str += bidding_str
    lin_str += play_str
    lin_str += "pg||"

    #print(lin_str)
    return lin_str

def build_lin_url(deal: Deal, board_record: BoardRecord):
    lin_str = build_lin_str(deal, board_record)
    encoded_lin_str = urllib.parse.quote_plus(lin_str)
    print(lin_str)
    return f"https://www.bridgebase.com/tools/handviewer.html?lin={encoded_lin_str}"


lin_records = parse_multi()
#lin_records = parse_single()
print(build_lin_url(*lin_records[1]))
