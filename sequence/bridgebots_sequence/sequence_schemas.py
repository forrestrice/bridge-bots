import importlib
import typing
from pathlib import Path

from marshmallow import Schema, fields, post_load

from bridgebots_sequence.bidding_context_features import ContextFeature
from bridgebots_sequence.bidding_sequence_features import CategoricalSequenceFeature, SequenceFeature
from bridgebots_sequence.interpreter import ModelInterpreter
from bridgebots_sequence.model_metadata import ModelMetadata


class PathField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return Path(value)


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


class TargetField(fields.Field):
    def _serialize(
        self, value: typing.Union[ContextFeature, CategoricalSequenceFeature], attr: str, obj: typing.Any, **kwargs
    ) -> str:
        return value.__class__.__name__

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> ContextFeature:
        try:
            module = importlib.import_module("bridgebots_sequence.bidding_context_features")
            return getattr(module, value)()
        except AttributeError:
            module = importlib.import_module("bridgebots_sequence.bidding_sequence_features")
            return getattr(module, value)()


class ModelInterpreterField(fields.Field):
    def _serialize(self, value: ModelInterpreter, attr: str, obj: typing.Any, **kwargs) -> str:
        return value.__class__.__name__

    def _deserialize(
        self, value: str, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs
    ) -> ModelInterpreter:
        module = importlib.import_module("bridgebots_sequence.interpreter")
        return getattr(module, value)()


class ModelMetadataSchema(Schema):
    training_data = PathField()
    validation_data = PathField()
    context_features = fields.List(ContextFeatureField)
    sequence_features = fields.List(SequenceFeatureField)
    target = TargetField()
    model_interpreter = ModelInterpreterField()
    description = fields.Str(missing=None)
    training_metrics = fields.Dict()

    @post_load
    def load_model_metadata(self, model_metadata_dict: dict, **kwargs) -> ModelMetadata:
        return ModelMetadata(**model_metadata_dict)
