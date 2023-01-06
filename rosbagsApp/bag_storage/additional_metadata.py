import datetime
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

    def __init__(self, description: str | None = None, hardware: str | None = None, location: str | None = None,
                 thumbnails: dict[str, set[str]] = None,
                 tags: list[str] = None, recording_time: datetime.datetime | None = None):
        self.description = description
        self.hardware = hardware
        self.location = location
        # In json we do not distinguish between empty or missing thumbnails/tags (we require >0 entries)
        self.thumbnails = thumbnails
        if thumbnails is None:
            self.thumbnails = {}
        self.tags = tags
        if tags is None:
            self.tags = []
        else:
            if len(tags) != len(set(tags)):
                raise RuntimeError(f"Tags in AdditionalMetadata must be unique. Tags given: {tags}")
        self.recording_time = recording_time

    def to_json(self) -> str:
        self_dict = {}

        if self.description is not None:
            self_dict["description"] = self.description

        if self.hardware is not None:
            self_dict["hardware"] = self.hardware

        if self.location is not None:
            self_dict["location"] = self.location

        if self.thumbnails is not None and len(self.thumbnails) > 0:
            self_dict["thumbnails"] = thumbnails_to_lists(self.thumbnails)

        if len(self.tags) > 0:
            self_dict["tags"] = self.tags

        if self.recording_time is not None:
            self_dict["recording_time"] = self.recording_time.isoformat()

        validate(self_dict, additional_metadata_schema)
        return json.dumps(self_dict, indent=2)

    @staticmethod
    def from_file(path: Path) -> 'AdditionalMetadata':
        with open(path, 'r') as metadata_file:
            metadata = json.load(metadata_file)
        validate(metadata, additional_metadata_schema)
        return AdditionalMetadata(metadata.get("description"), metadata.get("hardware"), metadata.get("location"),
                                  thumbnails_to_sets(metadata.get("thumbnails")), metadata.get("tags", []),
                                  datetime.datetime.fromisoformat(
                                      metadata["recording_time"]) if "recording_time" in metadata else None
                                  )

    @staticmethod
    def default() -> 'AdditionalMetadata':
        # TODO: Make more (all) fields optional, to enable creating thumbnails without setting empty values for other
        #  metadata (https://github.com/teamspatzenhirn/rosbagBrowser/issues/3)
        return AdditionalMetadata("", "", "", None, ["no_metadata"])
