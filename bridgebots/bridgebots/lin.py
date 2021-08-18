import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from bridgebots.bids import canonicalize_bid
from bridgebots.board_record import BidMetadata, BoardRecord, Commentary, DealRecord
from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import BiddingSuit, Direction, Suit
from bridgebots.deal_utils import from_lin_deal
from bridgebots.play_utils import trick_evaluator

_BID_TRANSLATION = {"PASS": "p", "DBL": "d", "RDBL": "r"}
_PASS_OUT_AUCTION = ["PASS"] * 4


def _parse_lin_string(lin_str: str) -> Dict:
    """
    Accumulate all the LIN node contents. The node name becomes a key in the returned dict, and all the obeserved values
     for that key are stored in a list as the dictionary value
    :param lin_str: A LIN board record as a single line
    :return: A dictionary containing parsed LIN nodes
    """
    lin_dict = defaultdict(list)
    while not (lin_str.isspace() or lin_str == ""):
        key, value, lin_str = lin_str.split("|", maxsplit=2)
        if key == "an":  # Bid explanation node
            lin_dict[key].append((len(lin_dict["mb"]) - 1, value))  # Track which bid this announcement applies to
        elif key == "nt":  # Commentary node
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


def _parse_deal(lin_dict: dict) -> Deal:
    """
    Parse the hands, vulnerability, and dealer from the LIN file and create a Deal object
    :return: a Deal representation of the parsed LIN file
    """
    lin_dealer_str = lin_dict["md"][0][0]
    vulnerability_str = lin_dict["sv"][0]
    holding_str = lin_dict["md"][0][1:]
    return from_lin_deal(lin_dealer_str, vulnerability_str, holding_str)


def _parse_bidding_record(raw_bidding_record: List[str], lin_dict: Dict) -> Tuple[List[str], List[BidMetadata]]:
    """
    Convert LIN bids to their bridgebots representation. Create BiddingMetadata to capture alerts and bid explanations.
    :return: A pair of the parsed bidding record and the list of BiddingMetadata associated with the auction
    """
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


def _determine_declarer(play_record: List[Card], bidding_record: List[str], deal: Deal) -> Direction:
    """
    Use the play or bidding to determine which Direction declared the Board
    :return: the Direction that declared the Board
    """
    if bidding_record == _PASS_OUT_AUCTION:
        return deal.dealer
    first_card = play_record[0]
    leader = next(direction for direction in Direction if first_card in deal.player_cards[direction])
    return leader.previous()


def _parse_tricks(
    lin_dict: dict,
    declarer: Direction,
    contract: str,
    play_record: List[Card],
) -> int:
    """
    Use the play record and claim record to determine how many tricks were taken by declarer
    :return: the number of tricks taken by declarer
    """
    if "mc" in lin_dict:  # Use claim node if it is present
        return int(lin_dict["mc"][0])

    if len(play_record) != 52:
        raise ValueError(f"Not enough cards played: {len(play_record)}")

    trump_suit = BiddingSuit.from_str(contract[1:2])
    tricks = [play_record[i : i + 4] for i in range(0, 52, 4)]
    lead_direction = declarer.next()
    offense_directions = [declarer, declarer.partner()]
    offense_tricks = 0
    for trick in tricks:
        evaluator = trick_evaluator(trump_suit, trick[0].suit)
        winning_index, winning_card = max(enumerate(trick), key=lambda c: evaluator(c[1]))
        lead_direction = Direction((lead_direction.value + winning_index) % 4)
        if lead_direction in offense_directions:
            offense_tricks += 1
    return offense_tricks


def _parse_player_names(lin_dict: Dict) -> Dict[Direction, str]:
    """
    :return: A mapping from Direction to the name of the player sitting that direction
    """
    if "pn" in lin_dict:
        player_names = lin_dict["pn"][0].split(",")
        if "qx" in lin_dict and len(player_names) > 4:  # True if LIN file is from a team match
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
    """
    Construct a BoardRecord object from the parsed lin_dict and deal
    """
    player_names = _parse_player_names(lin_dict)
    raw_bidding_record = lin_dict["mb"]
    bidding_record, bidding_metadata = _parse_bidding_record(raw_bidding_record, lin_dict)
    contract = bidding_record[-4]  # Last bid before pass out
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


def _build_bidding_str(board_record: BoardRecord) -> str:
    """
    Build the bidding section of a LIN file for the given BoardRecord. Use BiddingMetadata to include alerts and
    explanations.
    """
    metadata_by_index = {metadata.bid_index: metadata for metadata in board_record.bidding_metadata}
    bidding_str = ""
    for bid_index, bid in enumerate(board_record.bidding_record):
        translated_bid = _BID_TRANSLATION.get(bid, bid).replace("NT", "N")
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


def _build_play_str(board_record: BoardRecord) -> str:
    """
    Construct the play record section of a LIN file. If fewer than 52 cards were played, include a claim node to
    indicate the final result.
    """
    play_str = ""
    trick_count = 0
    # Separate each trick with a pg node
    for card in board_record.play_record:
        play_str += f"pc|{card}|"
        trick_count = (trick_count + 1) % 4
        if trick_count == 0:
            play_str += "pg||"
    if len(board_record.play_record) < 52:
        play_str += f"mc|{board_record.tricks}|"
    return play_str


def parse_single(file_path: Path) -> List[DealRecord]:
    """
    Parse a board-per-line LIN file
    :param file_path: path to single-board LIN file
    :return: A list of parsed DealRecords, one for each line of the LIN file
    """
    with open(file_path) as lin_file:
        deal_records = []
        for line in lin_file:
            lin_dict = _parse_lin_string(line)
            deal = _parse_deal(lin_dict)
            board_record = _parse_board_record(lin_dict, deal)
            deal_records.append(DealRecord(deal, [board_record]))
        return deal_records


def parse_multi(file_path: Path) -> List[DealRecord]:
    """
    Parse a multi-board session LIN file
    :param file_path: path to multi-board LIN file
    :return: A list of parsed DealRecords corresponding to the session in the LIN file
    """
    with open(file_path) as lin_file:
        title_line = _parse_lin_string(lin_file.readline())
        results = _parse_lin_string(lin_file.readline())
        player_names = _parse_lin_string(lin_file.readline())
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
            lin_dict = _parse_lin_string(board_single_string)
            lin_dict["pn"] = player_names["pn"]
            deal = _parse_deal(lin_dict)
            board_record = _parse_board_record(lin_dict, deal)
            records.append(DealRecord(deal, [board_record]))
        return records


def build_lin_str(deal: Deal, board_record: BoardRecord) -> str:
    """
    Convert a Deal and a BoardRecord to a LIN format representation
    """
    # In LIN format (1=S, 2=W, 3=N, 4=E)
    lin_dealer = (deal.dealer.value + 2) % 4 + 1
    holding_direction = Direction.SOUTH
    player_holding_strings = []
    for i in range(4):
        player_hand = deal.hands[holding_direction]
        player_holding_str = ""
        # Create a string like 3SAJ983H9D98732C75 from the PlayerHolding
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

    bidding_str = _build_bidding_str(board_record)
    play_str = _build_play_str(board_record)

    lin_str = ""
    lin_str += f"pn|{board_record.south},{board_record.west},{board_record.north},{board_record.east}|"
    lin_str += f"st||md|{lin_dealer}{','.join(player_holding_strings)}|"
    lin_str += f"sv|{vuln_str}|"
    lin_str += bidding_str
    lin_str += play_str
    lin_str += "pg||"
    return lin_str


def build_lin_url(deal: Deal, board_record: BoardRecord) -> str:
    """
    Build a BridgeBase url for the supplied Deal and BoardRecord
    """
    lin_str = build_lin_str(deal, board_record)
    encoded_lin_str = urllib.parse.quote_plus(lin_str)
    return f"https://www.bridgebase.com/tools/handviewer.html?lin={encoded_lin_str}"


#lin_records = parse_multi(Path("/Users/frice/bridge/lin_parse/usbf_sf_14502.lin"))
#print(build_lin_url(lin_records[1].deal, lin_records[1].board_records[0]))

lin_records = parse_single(Path("/Users/frice/bridge/lin_parse/sample_hand.lin"))
print(lin_records)

