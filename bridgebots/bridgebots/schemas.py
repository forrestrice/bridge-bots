from collections import defaultdict
from pathlib import Path

from marshmallow import Schema, ValidationError, fields, post_load

from bridgebots.board_record import BidMetadata, BoardRecord, Commentary, DealRecord
from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import Direction
from bridgebots.lin import parse_multi


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

    class Meta:
        ordered = True

    @post_load
    def load_deal(self, deal_dict, **kwargs):
        print("load_deal", deal_dict)
        return Deal.from_cards(**deal_dict)


class CommentarySchema(Schema):
    bid_index = fields.Int(missing=None)
    play_index = fields.Int(missing=None)
    comment = fields.Str()

    class Meta:
        ordered = True

    @post_load
    def load_commentary(self, commentary_dict, **kwargs):
        return Commentary(**commentary_dict)


class BidMetadataSchema(Schema):
    bid_index = fields.Int()
    bid = fields.Str()
    alerted = fields.Bool()
    explanation = fields.Str(missing=None)

    class Meta:
        ordered = True

    @post_load
    def load_bid_metadata(self, bid_metadata_dict, **kwargs):
        return BidMetadata(**bid_metadata_dict)


class BoardRecordSchema(Schema):
    bidding_record = fields.List(fields.Str)
    raw_bidding_record = fields.List(fields.Str)
    play_record = fields.List(CardField())
    declarer = DirectionField()
    contract = fields.Str()
    tricks = fields.Int()
    scoring = fields.Str(missing=None)
    north = fields.Str(missing="NORTH")
    south = fields.Str(missing="SOUTH")
    east = fields.Str(missing="EAST")
    west = fields.Str(missing="WEST")
    date = fields.Str(missing=None)  # TODO make this datetime?
    event = fields.Str(missing=None)
    bidding_metadata = fields.List(fields.Nested(BidMetadataSchema()))
    commentary = fields.List(fields.Nested(CommentarySchema()))

    class Meta:
        ordered = True

    @post_load
    def load_board_record(self, board_record_dict, **kwargs):
        return BoardRecord(**board_record_dict)


class DealRecordSchema(Schema):
    deal = fields.Nested(DealSchema())
    board_records = fields.List(fields.Nested(BoardRecordSchema()))

    class Meta:
        ordered = True

    @post_load
    def load_deal_record(self, deal_record_dict, **kwargs):
        return DealRecord(**deal_record_dict)


lin_records = parse_multi(Path("/Users/frice/bridge/lin_parse/usbf_sf_14502.lin"))
some_deal_records = lin_records[0:1]
print(some_deal_records[0])

deal_record_schema = DealRecordSchema(many=True)
dumped_records = deal_record_schema.dumps(some_deal_records)
print(dumped_records)
loaded_records = deal_record_schema.loads(dumped_records)
print(loaded_records == some_deal_records)
