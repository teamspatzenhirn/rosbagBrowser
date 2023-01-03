from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rosbagsApp.bag_storage.storage import BagStorage, TopicRecordingInfo


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
        response = self.client.get(reverse("rosbags:detail", args=["unit_test_bag"]))
        self.assertEqual(response.status_code, 200)

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
        bs = BagStorage()
        bag = bs.find("unit_test_bag")
        self.assertEqual(bag.topics, [
            TopicRecordingInfo('/spatz11/sensor_data',
                               'spatz_interfaces/msg/Spatz11SensorData',
                               [Path("_spatz11_sensor_data.png")],
                               123)])
