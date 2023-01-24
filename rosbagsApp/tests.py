import datetime
import json
import os.path
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rosbagsApp.bag_storage.additional_metadata import AdditionalMetadata, additional_metadata_file_name
from rosbagsApp.bag_storage.storage import BagStorage, TopicRecordingInfo

TEST_DATA_PATH = "rosbagsApp/testdata"


class ListViewTests(TestCase):
    def setUp(self):
        self.test_user = get_user_model().objects.create_user("temporary")

    def test_list_no_error(self):
        self.client.force_login(self.test_user)
        response = self.client.get(reverse("rosbags:list"))
        self.assertEqual(response.status_code, 200)

    def test_list_needs_authentication(self):
        response = self.client.get(reverse("rosbags:list"))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("rosbags:list"))


class DetailViewTests(TestCase):
    def setUp(self):
        self.test_user = get_user_model().objects.create_user("temporary")

    def test_detail_no_error(self):
        self.client.force_login(self.test_user)
        test_bag_list = ["bag_without_metadata", "test_state_only", "test_state_only", "test_state_only_with_thumbs",
                         "unit_test_bag", "unit_test_bag_minimal_metadata", "unit_test_bag_recording_time",
                         "unit_test_bag_recording_time_with_tz"]
        for bag in test_bag_list:
            response = self.client.get(reverse("rosbags:detail", args=[bag]))
            self.assertEqual(response.status_code, 200, msg=f"bag name: {bag}")

    def test_detail_no_error_without_metadata(self):
        self.client.force_login(self.test_user)
        response = self.client.get(reverse("rosbags:detail", args=["bag_without_metadata"]))
        self.assertEqual(response.status_code, 200)

    def test_detail_needs_authentication(self):
        url = reverse("rosbags:detail", args=["unit_test_bag"])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("login") + "?next=" + url)


class MetadataStorageTests(TestCase):
    def test_topic_metadata(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("unit_test_bag")
        self.assertEqual(bag.topics, [
            TopicRecordingInfo('/spatz11/sensor_data',
                               'spatz_interfaces/msg/Spatz11SensorData',
                               set(),
                               123)])

    def test_bag_without_additional_metadata_topics(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("bag_without_metadata")
        self.assertEqual(bag.topics, [
            TopicRecordingInfo('/spatz11/sensor_data',
                               'spatz_interfaces/msg/Spatz11SensorData',
                               set(),
                               123)])


class AdditionalMetadataTests(TestCase):
    def test_optional_items(self):
        md = AdditionalMetadata("desc", "hw", "loc", None, [])
        self.assertEqual(md.thumbnails, {})
        self.assertEqual(md.tags, [])
        json_dump = md.to_json()
        decoded = json.loads(json_dump)
        self.assertFalse("thumbnails" in decoded)
        self.assertFalse("tags" in decoded)

        # Explicitly set empty thumbnails dict
        md.thumbnails = {}
        json_dump = md.to_json()
        decoded = json.loads(json_dump)
        # Empty thumbnail list should not be encoded
        self.assertFalse("thumbnails" in decoded)

    def test_recording_time(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("unit_test_bag_recording_time")
        self.assertEqual(bag.recording_date, datetime.datetime(2023, 1, 6, 18, 41, 1, tzinfo=datetime.timezone.utc))

    def test_recording_time_with_tz(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("unit_test_bag_recording_time_with_tz")
        self.assertEqual(bag.recording_date, datetime.datetime(2023, 1, 6, 18, 41, 1, tzinfo=datetime.timezone.utc))
        self.assertEqual(bag.recording_date,
                         datetime.datetime(2023, 1, 6, 19, 41, 1,
                                           tzinfo=datetime.timezone(datetime.timedelta(hours=1))))
        self.assertEqual(bag.recording_date.tzinfo, datetime.timezone(datetime.timedelta(hours=1)))


class ThumbnailGeneration(TestCase):
    def test_create_thumbnail_states(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("test_state_only")
        expected_thumb_path = bag.path / "thumbnails" / "spatz.png"
        if os.path.exists(expected_thumb_path):
            os.remove(expected_thumb_path)

        amd_path = bag.path / additional_metadata_file_name

        bag.generate_thumbnails()
        self.assertEqual(bag.metadata.thumbnails, {"/spatz": {"spatz.png"}})
        self.assertTrue(os.path.exists(expected_thumb_path))
        # Verify metadata written to file
        new_amd = AdditionalMetadata.from_file(amd_path)
        self.assertEqual(new_amd.thumbnails, {"/spatz": {"spatz.png"}})

        # Cleanup: restore metadata, delete thumbnail
        if os.path.exists(expected_thumb_path):
            os.remove(expected_thumb_path)
        new_amd.thumbnails = None
        amd_path.write_text(new_amd.to_json())


class SimulationTimeTests(TestCase):
    def test_identify_simulation_time(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("test_state_only")
        self.assertTrue(bag.is_simulation_time)
        bag = bs.find_by_name("unit_test_bag")
        self.assertFalse(bag.is_simulation_time)


class BagStorageStest(TestCase):
    def test_list_subdirs(self):
        bs = BagStorage(TEST_DATA_PATH)
        bags = list(bs.__iter__())
        bag_names = [b.name for b in bags]
        bag_names.sort()

        expected_bags = ['unit_test_bag',
                         'bag_without_metadata',
                         'unit_test_bag_recording_time_with_tz',
                         'unit_test_bag_recording_time',
                         'unit_test_bag_minimal_metadata',
                         'test_state_only_with_thumbs',
                         'test_state_only',
                         'testbag_in_subdir',
                         'testbag_in_subdir2']
        expected_bags.sort()

        self.assertListEqual(expected_bags, bag_names)

    def test_find_in_subdir_by_name(self):
        bs = BagStorage(TEST_DATA_PATH)
        self.assertIsNotNone(bs.find_by_name("testbag_in_subdir2"))

    def test_find_in_subdir_by_path(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_path(Path("subdir/subdir2/testbag_in_subdir2"))
        self.assertIsNotNone(bag)

    def test_subdir_bag_path(self):
        bs = BagStorage(TEST_DATA_PATH)
        bag = bs.find_by_name("testbag_in_subdir2")
        rel_path = str(bag.rel_path).rstrip("/")
        self.assertTrue(str(rel_path).endswith("subdir/subdir2/testbag_in_subdir2"))
        self.assertEqual(bag.rel_path, Path("subdir/subdir2/testbag_in_subdir2"))

        path = str(bag.path).rstrip("/")
        self.assertTrue(str(path).endswith("subdir/subdir2/testbag_in_subdir2"))
