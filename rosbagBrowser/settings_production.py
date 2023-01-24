from .settings import *

"""
Settings overrides for staging environment
"""

ALLOWED_HOSTS = ["rosbag.spatz.wtf"]
DEBUG = False
STATIC_ROOT = "/django_static/static"
ROSBAG_STORAGE_PATH = "/opt/aufnahmen/2023/rosbags"
ROSBAG_MOUNT_PATH = "/opt/aufnahmen/2023/rosbags"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SILENCED_SYSTEM_CHECKS = [
    "security.W004"  # We don't want to use HSTS for any server because it literally only ever causes problems
]
