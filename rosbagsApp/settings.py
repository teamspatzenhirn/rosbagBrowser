from django.conf import settings

ROSBAG_STORAGE_PATH = getattr(settings, 'ROSBAG_STORAGE_PATH', "/opt/aufnahmen/2023/rosbags/")
ROSBAG_MOUNT_PATH = getattr(settings, 'ROSBAG_MOUNT_PATH', ROSBAG_STORAGE_PATH)
