from django.conf import settings

ROSBAG_STORAGE_PATH = getattr(settings, 'ROSBAG_STORAGE_PATH', "/opt/aufnahmen/2023/rosbags/")
