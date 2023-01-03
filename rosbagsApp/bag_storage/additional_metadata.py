import json
from pathlib import Path

from django.contrib.staticfiles import finders
from jsonschema.validators import validate

additional_metadata_file_name = "additional_metadata.json"

additional_metadata_schema_location = finders.find("rosbagsApp/additional_metadata_schema.json")

with open(additional_metadata_schema_location, 'r') as schema_file:
    additional_metadata_schema = json.load(schema_file)


def thumbnails_to_sets(from_json: dict[str, list[str]] | None) -> dict[str, set[str]] | None:
    """
    The list of thumbnails for a topic must contain unique items. In json, this is a list (schema ensures unique),
    in python it is a set. This converts from json-form to python-form.
    """
    if from_json is None:
        return None
    res = {}
    for topic, thumbs in from_json.items():
        res[topic] = set(thumbs)
    return res


def thumbnails_to_lists(from_python: dict[str, set[str]] | None) -> dict[str, list[str]] | None:
    """
    The list of thumbnails for a topic must contain unique items. In json, this is a list (schema ensures unique),
    in python it is a set. This converts from python-form to json-form.
    """
    if from_python is None:
        return None
    res = {}
    for topic, thumbs in from_python.items():
        res[topic] = list(thumbs)
    return res


class AdditionalMetadata:
    """
    Python class representing additional_metadata.json
    """

    def __init__(self, description: str, hardware: str, location: str, thumbnails: dict[str, set[str]] | None,
                 tags: list[str]):
        self.description = description
        self.hardware = hardware
        self.location = location
        self.__thumbnails = thumbnails
        self.tags = tags

        if len(tags) != len(set(tags)):
            raise RuntimeError(f"Tags in AdditionalMetadata must be unique. Tags given: {tags}")

    @property
    def thumbnails(self) -> dict[str, set[str]]:
        # For convenience, this property returns empty list, even if thumbnails are explicitly not set.
        # Internally, the state is preserved.
        return self.__thumbnails or {}

    @thumbnails.setter
    def thumbnails(self, new_thumbnails: dict[str, set[str]] | None):
        self.__thumbnails = new_thumbnails

    def to_json(self) -> str:
        self_dict = {
            "description": self.description,
            "hardware": self.hardware,
            "location": self.location
        }

        # Thumbnails are optional, and we want to preserve the empty vs not-set state
        if self.__thumbnails is not None:
            self_dict["thumbnails"] = thumbnails_to_lists(self.__thumbnails)
        # Do not encode empty tag list
        if len(self.tags) > 0:
            self_dict["tags"] = self.tags

        validate(self_dict, additional_metadata_schema)
        return json.dumps(self_dict, indent=2)

    @staticmethod
    def from_file(path: Path) -> 'AdditionalMetadata':
        with open(path, 'r') as metadata_file:
            metadata = json.load(metadata_file)
        validate(metadata, additional_metadata_schema)
        return AdditionalMetadata(metadata["description"], metadata["hardware"], metadata["location"],
                                  thumbnails_to_sets(metadata.get("thumbnails", None)), metadata.get("tags", []))

    @staticmethod
    def default() -> 'AdditionalMetadata':
        # TODO: Make more (all) fields optional, to enable creating thumbnails without setting empty values for other
        #  metadata
        return AdditionalMetadata("", "", "", None, ["no_metadata"])
