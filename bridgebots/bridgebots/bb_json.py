import json
from collections import defaultdict
from json import JSONDecoder, JSONEncoder
from typing import Dict

from bridgebots.board_record import BidMetadata, BoardRecord, Commentary, DealRecord
from bridgebots.deal import Card, Deal, PlayerHand
from bridgebots.deal_enums import Direction
from bridgebots.lin import parse_multi


def deal_to_json_dict(deal: Deal) -> Dict:
    """
    JSONEncoder will attempt to serialize the hands dict without converting the Direction keys to strings, so we must
    construct a dictionary with string keys
    :param deal:
    :return:
    """
    hands = {direction.abbreviation(): deal.player_cards[direction] for direction in Direction}
    return {
        "dealer": deal.dealer.abbreviation(),
        "ns_vulnerable": deal.ns_vulnerable,
        "ew_vulnerable": deal.ew_vulnerable,
        "hands": hands,
    }


class BridgeBotsEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Deal):
            return deal_to_json_dict(o)
        elif isinstance(o, Card):
            return str(o)
        elif isinstance(o, Direction):
            return o.abbreviation()
        return o.__dict__


class BridgeBotsDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(
            self, object_hook=self.object_hook, object_pairs_hook=self.object_pairs_hook, *args, **kwargs
        )

    def object_hook(self, obj):
        print("OBJECT_HOOK:", obj)

    def object_pairs_hook(self, obj):
        decode_dict = {}
        for key, value in obj:
            if key in ["dealer", "declarer"]:
                decode_dict[key] = Direction.from_str(value)
            elif key == "hands":
                player_hands = {
                    Direction.from_str(d): PlayerHand.from_cards([Card.from_str(c) for c in cards])
                    for d, cards in value.items()
                }
                decode_dict[key] = player_hands
            elif key == "deal":
                decode_dict[key] = Deal(**value)
            elif key == "commentary":
                decode_dict[key] = [Commentary(**v) for v in value]
            elif key == "bidding_metadata":
                decode_dict[key] = [BidMetadata(**v) for v in value]
            elif key == "play_record":
                decode_dict[key] = [Card.from_str(c) for c in value]
            elif key == "board_records":
                decode_dict[key] = [BoardRecord(**v) for v in value]
            else:
                decode_dict[key] = value
        if "deal" in decode_dict and "board_records" in decode_dict:
            return DealRecord(**decode_dict)
        print(type(obj), obj)
        print(len(decode_dict))
        return decode_dict


lin_records = parse_multi()

deal_dict = defaultdict(list)
for deal, table_record in lin_records:
    deal_dict[deal].append(table_record)

deal_records = [DealRecord(deal, board_records) for deal, board_records in deal_dict.items()]
some_deal_records = deal_records[0:1]
a_deal = some_deal_records[0].deal
# pprint(json.dumps(a_deal, cls=DealEncoder), width=120, compact=False)
# pprint(json.dumps(some_deal_records, cls=BridgeBotsEncoder), width=120, compact=False)
# print(json.dumps(some_deal_records, cls=BridgeBotsEncoder))
# pprint(json.loads(json.dumps(some_deal_records, cls=BridgeBotsEncoder)))
loaded = json.loads(json.dumps(some_deal_records, cls=BridgeBotsEncoder), cls=BridgeBotsDecoder)

# loaded_record =
print(loaded[0])
print(loaded[0] == some_deal_records[0])
