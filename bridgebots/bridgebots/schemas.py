from marshmallow import Schema, ValidationError, fields, post_load

from bridgebots.deal import Card, Deal, PlayerHand
from bridgebots.deal_enums import Direction


class CardField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return repr(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return Card.from_str(value)
        except ValueError as error:
            raise ValidationError(f"Invalid card: {value}") from error


class DirectionField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        try:
            return value.abbreviation()
        except AttributeError as error:
            raise ValidationError(f"Invalid direction: {value}") from error

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return Direction.from_str(value)
        except ValueError as error:
            raise ValidationError(f"Invalid direction: {value}") from error


class DealSchema(Schema):
    dealer = DirectionField()
    ns_vulnerable = fields.Bool()
    ew_vulnerable = fields.Bool()
    player_cards = fields.Dict(keys=DirectionField(), values=fields.List(CardField()), data_key="hands")

    @post_load
    def load_deal(self, deal_dict, **kwargs):
        print("load_deal", deal_dict)
        return Deal.from_cards(**deal_dict)

deal_schema = DealSchema()
#print(deal_schema.dump({"dealer" : Direction.NORTH, "ns_vulnerable":True, "ew_vulnerable":False}))

hands = {
        Direction.NORTH: PlayerHand.from_string_lists(
            ["9", "8", "6", "4"], ["K", "Q", "7", "6", "3"], ["A", "K"], ["7", "3"]
        ),
        Direction.SOUTH: PlayerHand.from_string_lists(
            ["A", "K", "Q", "5"], ["A", "9", "4"], ["J", "5", "2"], ["K", "8", "4"]
        ),
        Direction.EAST: PlayerHand.from_string_lists(
            ["2"], ["J", "10", "8", "5", "2"], ["Q", "8", "7", "4", "3"], ["A", "10"]
        ),
        Direction.WEST: PlayerHand.from_string_lists(
            ["J", "10", "7", "3"], [], ["10", "9", "6"], ["Q", "J", "9", "6", "5", "2"]
        ),
    }
test_deal = Deal(Direction.EAST, True, False, hands)
dumped_deal = deal_schema.dump(test_deal)
print(dumped_deal)
loaded = deal_schema.load(dumped_deal)
print(loaded)
