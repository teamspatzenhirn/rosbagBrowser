import os
from typing import Optional

import rosbags.rosbag2 as rb
import datetime

import json

from jsonschema import validate

from django.utils.functional import cached_property

# TODO: Configuration variable / Database setting
storage_path = "/home/jonas/Projects/Carolo/rosbags"

additional_metadata_file_name = "additional_metadata.json"

# TODO: Find out how to use project-relative paths
additional_metadata_schema_location = "/home/jonas/Projects/rosbagBrowser/additional_metadata_schema.json"

with open(additional_metadata_schema_location, 'r') as schema_file:
    additional_metadata_schema = json.load(schema_file)


def is_rosbag(path: str):
    if os.path.exists(os.path.join(path, "metadata.yaml")):
        return True
    return False


class ROSBag:
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
        return self.dir_name

    def __str__(self):
        return f"ROSBag{{{self.name}}}"

    def __repr__(self):
        return f"ROSBag{{{self.name} at {self.path}, recorded at {self.recording_date} for {self.duration}," \
               f" topics: {self.topics}}}"

    @cached_property
    def recording_date(self) -> datetime.datetime:
        with rb.Reader(self.path) as reader:
            return datetime.datetime.fromtimestamp(reader.start_time // 1000000000)

    @cached_property
    def duration(self) -> datetime.timedelta:
        with rb.Reader(self.path) as reader:
            return datetime.timedelta(microseconds=reader.duration // 1000)

    @cached_property
    def topics(self) -> list[(str, str)]:
        topics = []
        with rb.Reader(self.path) as reader:
            for connection in reader.connections:
                topics.append((connection.topic, connection.msgtype))
        return topics

    @property
    def tags(self) -> list[str]:
        if not hasattr(self, 'metadata'):
            return []
        return self.metadata['tags']

    def thumbnails(self) -> list[str]:
        res = []
        thumbnail_dir = os.path.join(self.path, "thumbnails")
        if os.path.exists(thumbnail_dir) and os.path.isdir(thumbnail_dir):
            for entry in os.scandir(thumbnail_dir):
                if entry.is_file():
                    res.append(entry.name)
        return res

    def json(self) -> dict:
        return {"name": self.name,
                "topics": [{"name": n, "type": t} for n, t in self.topics],
                "date": self.recording_date.isoformat(),
                "duration": int(self.duration.total_seconds() * 1000),
                "tags": self.tags}


class BagStorage:
    def __init__(self, path: str = storage_path):
        self.base_path = path

    def __iter__(self):
        for entry in os.scandir(self.base_path):
            if entry.is_dir() and is_rosbag(entry.path):
                yield ROSBag(self.base_path, entry.name)

    def find(self, name: str) -> Optional[ROSBag]:
        path = os.path.join(self.base_path, name)
        if not is_rosbag(path):
            return None
        return ROSBag(self.base_path, name)
