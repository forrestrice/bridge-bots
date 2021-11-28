import typing

from marshmallow import Schema, ValidationError, fields, post_load

from bridgebots.board_record import BidMetadata, BoardRecord, Commentary, Contract, DealRecord
from bridgebots.deal import Card, Deal
from bridgebots.deal_enums import Direction

"""
Marshmallow schemas for serializing and deserializing bridgebots objects to/from JSON
"""


class CardField(fields.Field):
    def _serialize(self, value: Card, attr: str, obj: typing.Any, **kwargs) -> str:
        return repr(value)

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> Card:
        try:
            return Card.from_str(value)
        except ValueError as error:
            raise ValidationError(f"Invalid card: {value}") from error


class DirectionField(fields.Field):
    def _serialize(self, value: Direction, attr: str, obj: typing.Any, **kwargs) -> str:
        try:
            return value.abbreviation()
        except AttributeError as error:
            raise ValidationError(f"Invalid direction: {value}") from error

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> Direction:
        try:
            return Direction.from_str(value)
        except ValueError as error:
            raise ValidationError(f"Invalid direction: {value}") from error


class ContractField(fields.Field):
    def _serialize(self, value: Contract, attr: str, obj: typing.Any, **kwargs) -> str:
        try:
            return str(value)
        except AttributeError as error:
            raise ValidationError(f"Invalid contract: {value}") from error

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> Contract:
        try:
            return Contract.from_str(value)
        except ValueError as error:
            raise ValidationError(f"Invalid contract: {value}") from error


class DealSchema(Schema):
    dealer = DirectionField()
    ns_vulnerable = fields.Bool()
    ew_vulnerable = fields.Bool()
    player_cards = fields.Dict(keys=DirectionField, values=fields.List(CardField), data_key="hands")

    class Meta:
        ordered = True

    @post_load
    def load_deal(self, deal_dict: dict, **kwargs) -> Deal:
        return Deal.from_cards(**deal_dict)


class CommentarySchema(Schema):
    bid_index = fields.Int(missing=None)
    play_index = fields.Int(missing=None)
    comment = fields.Str()

    class Meta:
        ordered = True

    @post_load
    def load_commentary(self, commentary_dict: dict, **kwargs) -> Commentary:
        return Commentary(**commentary_dict)


class BidMetadataSchema(Schema):
    bid_index = fields.Int()
    bid = fields.Str()
    alerted = fields.Bool()
    explanation = fields.Str(missing=None)

    class Meta:
        ordered = True

    @post_load
    def load_bid_metadata(self, bid_metadata_dict: dict, **kwargs) -> BidMetadata:
        return BidMetadata(**bid_metadata_dict)


class BoardRecordSchema(Schema):
    bidding_record = fields.List(fields.Str)
    raw_bidding_record = fields.List(fields.Str)
    play_record = fields.List(CardField())
    declarer = DirectionField()
    contract = ContractField()
    tricks = fields.Int()
    score = fields.Int()
    scoring = fields.Str(missing=None)
    names = fields.Dict(
        keys=DirectionField(),
        values=fields.Str,
        missing={Direction.NORTH: "NORTH", Direction.SOUTH: "SOUTH", Direction.EAST: "EAST", Direction.WEST: "WEST"},
    )
    date = fields.Str(missing=None)  # TODO make this datetime?
    event = fields.Str(missing=None)
    bidding_metadata = fields.List(fields.Nested(BidMetadataSchema), missing=None)
    commentary = fields.List(fields.Nested(CommentarySchema), missing=None)

    class Meta:
        ordered = True

    @post_load
    def load_board_record(self, board_record_dict: dict, **kwargs) -> BoardRecord:
        return BoardRecord(**board_record_dict)


class DealRecordSchema(Schema):
    deal = fields.Nested(DealSchema)
    board_records = fields.List(fields.Nested(BoardRecordSchema))

    class Meta:
        ordered = True

    @post_load
    def load_deal_record(self, deal_record_dict: dict, **kwargs) -> DealRecord:
        return DealRecord(**deal_record_dict)
