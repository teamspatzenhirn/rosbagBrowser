import datetime
import json
import os
from typing import Optional, Generator

import rosbags.rosbag2 as rb
from django.contrib.staticfiles import finders
from django.utils.functional import cached_property
from jsonschema import validate

import rosbagsApp.settings

additional_metadata_file_name = "additional_metadata.json"

additional_metadata_schema_location = finders.find("rosbagsApp/additional_metadata_schema.json")

with open(additional_metadata_schema_location, 'r') as schema_file:
    additional_metadata_schema = json.load(schema_file)


def is_rosbag(path: str):
    if os.path.exists(os.path.join(path, "metadata.yaml")):
        return True
    return False


class ROSBag:
    """
    ROS bag, providing access to metadata (metadata.yaml) and additional metadata (additional_metadata.json).
    Metadata is loaded lazily and cached, additional metadata is loaded on construction.

    TODO: not lazily load stuff? We probably need most of the data most of the time?
     Would opening the reader only once be faster?
    """

    def __init__(self, base_path: str, dir_name: str):
        self.path = os.path.join(base_path, dir_name)
        assert (is_rosbag(self.path))
        self.base_path = base_path
        self.dir_name = dir_name

        metadata_path = os.path.join(self.path, additional_metadata_file_name)
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as metadata_file:
                self.metadata = json.load(metadata_file)
            validate(self.metadata, additional_metadata_schema)

    @property
    def name(self):
        """Bag name: name of directory"""
        return self.dir_name

    def __str__(self):
        return f"ROSBag{{{self.name}}}"

    def __repr__(self):
        return f"ROSBag{{{self.name} at {self.path}, recorded at {self.recording_date} for {self.duration}," \
               f" topics: {self.topics}}}"

    @cached_property
    def recording_date(self) -> datetime.datetime:
        """Date and time of recording start"""
        with rb.Reader(self.path) as reader:
            return datetime.datetime.fromtimestamp(reader.start_time // 1000000000)

    @cached_property
    def duration(self) -> datetime.timedelta:
        with rb.Reader(self.path) as reader:
            return datetime.timedelta(microseconds=reader.duration // 1000)

    @cached_property
    def topics(self) -> list[(str, str)]:
        """List (name, type) of topics in bag"""
        topics = []
        with rb.Reader(self.path) as reader:
            for connection in reader.connections:
                topics.append((connection.topic, connection.msgtype))
        return topics

    @property
    def description(self) -> str:
        """Description from external metadata"""
        if not hasattr(self, 'metadata'):
            return ""
        return self.metadata['description']

    @property
    def tags(self) -> list[str]:
        """List of tags in additional metadata file"""
        if not hasattr(self, 'metadata'):
            return []
        return self.metadata['tags']

    def thumbnails(self) -> list[str]:
        """Filenames of available thumbnails (in bag_name/thumbnails/ directory)"""
        res = []
        thumbnail_dir = os.path.join(self.path, "thumbnails")
        if os.path.exists(thumbnail_dir) and os.path.isdir(thumbnail_dir):
            for entry in os.scandir(thumbnail_dir):
                if entry.is_file():
                    res.append(entry.name)
        return res

    def json(self) -> dict:
        """Dict representation for serializing to json, intended for displaying in frontend -> used by JS"""
        # TODO: Move formatting etc. into the view (client side?)
        return {"name": self.name,
                "topics": [{"name": n, "type": t} for n, t in self.topics],
                "date": self.recording_date.strftime("%Y %b. %d, %H:%M"),
                "duration": str(self.duration),
                "tags": self.tags,
                "description": self.description}


class BagStorage:
    """
    Class representing a directory containing ROS bags, allowing iteration and lookup by name
    """

    def __init__(self, path: str = rosbagsApp.settings.ROSBAG_STORAGE_PATH):
        """
        :param path: Directory containing ROS bags. Defaults to configured path from ROSBAG_STORAGE_PATH setting
        """
        self.base_path = path

    def __iter__(self) -> Generator[ROSBag, None, None]:
        """
        Iterating over the BagStorage yields all bags in configured directory
        """
        for entry in os.scandir(self.base_path):
            if entry.is_dir() and is_rosbag(entry.path):
                yield ROSBag(self.base_path, entry.name)

    def find(self, name: str) -> Optional[ROSBag]:
        """
        Lookup ROS bag by name
        :param name: Name of the ROS bag (directory)
        :return: ROS bag with specified name, or None if not found
        """
        path = os.path.join(self.base_path, name)
        if not is_rosbag(path):
            return None
        return ROSBag(self.base_path, name)
