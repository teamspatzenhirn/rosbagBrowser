import datetime
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Generator

import rosbags.rosbag2 as rb
from django.utils.functional import cached_property

import rosbagsApp.settings
from rosbagsApp.bag_storage.additional_metadata import AdditionalMetadata, additional_metadata_file_name
from rosbagsApp.bag_storage.thumbnails import create_thumbnail_spatz, create_thumbnail_image


def is_rosbag(path: Path):
    if (path / "metadata.yaml").exists():
        return True
    return False


@dataclass(frozen=True)
class TopicRecordingInfo:
    """
    Metadata about a topic which has been recorded in a ROS bag
    """
    name: str
    type: str
    thumbnails: set[str]
    nr_of_messages: int


class ROSBag:
    """
    ROS bag, providing access to metadata (metadata.yaml) and additional metadata (additional_metadata.json).
    Metadata is loaded lazily and cached, additional metadata is loaded on construction.

    TODO: not lazily load stuff? We probably need most of the data most of the time?
     Would opening the reader only once be faster?
    """

    def __init__(self, base_path: Path, rel_path: Path):
        self._base_path = base_path
        self._rel_path = rel_path

        assert (is_rosbag(self.path))
        # Bag name: last part of path (dir name)
        self._name: str = str(rel_path.name)

        metadata_path = os.path.join(self.path, additional_metadata_file_name)
        if os.path.exists(metadata_path):
            self.metadata = AdditionalMetadata.from_file(Path(metadata_path))
        else:
            self.metadata = AdditionalMetadata.default()

    @property
    def name(self):
        """Bag name: name of directory"""
        return self._name

    @property
    def rel_path(self) -> Path:
        """Path relative to bag storage"""
        return self._rel_path

    @property
    def path(self) -> Path:
        return self._base_path / self._rel_path

    def __str__(self):
        return f"ROSBag{{{self.name}}}"

    def __repr__(self):
        return f"ROSBag{{{self.name} at {self.path}, recorded at {self.recording_date} for {self.duration}," \
               f" topics: {self.topics}}}"

    @cached_property
    def recording_date(self) -> datetime.datetime:
        """Date and time of recording start"""
        # TODO: Timezones... Files all contain *seconds since epoch, which are referring to UTC.
        #  It would probably be a fair to assume the locale of recording is the same as the one when viewing, so we
        #  should adjust timezone accordingly for display. (https://github.com/teamspatzenhirn/rosbagBrowser/issues/4)
        #  The timestamp in additional metadata contains timezone info, this could be used to store recording timezone
        #  and reproduce exactly in gui

        if self.metadata.recording_time is not None:
            return self.metadata.recording_time

        with rb.Reader(self.path) as reader:
            return datetime.datetime.fromtimestamp(reader.start_time // 1000000000, tz=datetime.timezone.utc)

    @cached_property
    def is_simulation_time(self) -> bool:
        """
        Tries to determine if the timestamps in the ros bag are using simulation time, which usually starts at 0, and
        does not make sense when interpreted as time since epoch
        """
        if self.recording_date.year < 2000:
            return True
        return False

    @cached_property
    def duration(self) -> datetime.timedelta:
        with rb.Reader(self.path) as reader:
            return datetime.timedelta(microseconds=reader.duration // 1000)

    @cached_property
    def topics(self) -> list[TopicRecordingInfo]:
        """List (name, type) of topics in bag"""
        topics = []
        with rb.Reader(self.path) as reader:
            for connection in reader.connections:
                thumbs = self.metadata.thumbnails.get(connection.topic, set())
                topics.append(TopicRecordingInfo(connection.topic, connection.msgtype, thumbs, connection.msgcount))
        return topics

    @property
    def description(self) -> str:
        """Description from external metadata"""
        return self.metadata.description

    @property
    def tags(self) -> list[str]:
        """List of tags in additional metadata file"""
        return self.metadata.tags

    def thumbnails(self) -> dict[str, set[str]]:
        """Available thumbnails as specified in metadata"""
        return self.metadata.thumbnails

    def generate_thumbnails(self):
        thumbnails = {}
        with rb.Reader(self.path) as reader:
            for connection in reader.connections:
                if connection.msgtype == "spatz_interfaces/msg/Spatz":
                    thumbnails[connection.topic] = create_thumbnail_spatz(self.path, reader, connection)
                elif connection.msgtype == "sensor_msgs/msg/Image":
                    thumbnails[connection.topic] = create_thumbnail_image(self.path, reader, connection)

        for topic, thumbs in thumbnails.items():
            if len(self.metadata.thumbnails) == 0:
                self.metadata.thumbnails = {topic: thumbs}
            else:
                md_thumbs = self.metadata.thumbnails.get(topic, set())
                md_thumbs.update(thumbs)
                self.metadata.thumbnails[topic] = md_thumbs

        json_dump = self.metadata.to_json()
        with open(os.path.join(self.path, additional_metadata_file_name), 'w') as file:
            file.write(json_dump)

    def json(self) -> dict:
        """Dict representation for serializing to json, intended for displaying in frontend -> used by JS"""
        # TODO: Move formatting etc. into the view (client side?)
        return {"name": self.name,
                "topics": [{"name": t.name, "type": t.type} for t in self.topics],
                "date": self.recording_date.strftime("%Y %b. %d, %H:%M"),
                "duration": str(self.duration),
                "tags": self.tags,
                "path": str(self.rel_path),
                "description": self.description}


def rosbag_iter_impl(base_path: Path, current_subdir: Path) -> Generator[ROSBag, None, None]:
    for entry in os.scandir(base_path / current_subdir):
        if entry.is_dir():
            if is_rosbag(Path(entry.path)):
                yield ROSBag(base_path, current_subdir / entry.name)
            else:
                for b in rosbag_iter_impl(base_path, current_subdir / Path(entry.name)):
                    yield b


class BagStorage:
    """
    Class representing a directory containing ROS bags, allowing iteration and lookup by name
    """

    def __init__(self, path: str = rosbagsApp.settings.ROSBAG_STORAGE_PATH):
        """
        :param path: Directory containing ROS bags. Defaults to configured path from ROSBAG_STORAGE_PATH setting
        """
        self.base_path: Path = Path(path).resolve()

    def __iter__(self) -> Generator[ROSBag, None, None]:
        """
        Iterating over the BagStorage yields all bags in configured directory
        """
        for b in rosbag_iter_impl(self.base_path, Path(".")):
            yield b

    def find_by_path(self, path: Path) -> Optional[ROSBag]:
        """
        Lookup bag by path
        :param path: relative to BagStorage
        :return:
        """
        abs_path = (self.base_path / path).resolve()
        if Path(os.path.commonpath([abs_path, self.base_path])) != self.base_path:
            # Path must be below the base path, to prevent accessing outside directories
            return None

        if not is_rosbag(abs_path):
            return None
        return ROSBag(self.base_path, path)

    def find_by_name(self, name: str) -> Optional[ROSBag]:
        """
        Lookup ROS bag by name
        :param name: Name of the ROS bag (directory)
        :return: ROS bag with specified name, or None if not found
        """

        for b in self.__iter__():
            if b.name == name:
                return b
        return None
