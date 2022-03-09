import importlib
import typing

from marshmallow import Schema, fields, post_load

from bridgebots_sequence.bidding_context_features import ContextFeature
from bridgebots_sequence.bidding_sequence_features import SequenceFeature
from bridgebots_sequence.model_metadata import ModelMetadata


class SequenceFeatureField(fields.Field):
    def _serialize(self, value: SequenceFeature, attr: str, obj: typing.Any, **kwargs) -> str:
        return value.__class__.__name__

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> SequenceFeature:
        module = importlib.import_module("bridgebots_sequence.bidding_sequence_features")
        return getattr(module, value)()


class ContextFeatureField(fields.Field):
    def _serialize(self, value: ContextFeature, attr: str, obj: typing.Any, **kwargs) -> str:
        return value.__class__.__name__

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> ContextFeature:
        module = importlib.import_module("bridgebots_sequence.bidding_context_features")
        return getattr(module, value)()


class ModelMetadataSchema(Schema):
    context_features = fields.List(ContextFeatureField)
    sequence_features = fields.List(SequenceFeatureField)
    description = fields.Str(missing=None)


    @post_load
    def load_model_metadata(self, model_metadata_dict: dict, **kwargs) -> ModelMetadata:
        return ModelMetadata(**model_metadata_dict)
