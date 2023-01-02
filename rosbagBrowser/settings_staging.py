from .settings import *

"""
Settings overrides for staging environment
"""

ALLOWED_HOSTS = ["rosbag-browser-staging.jonasotto.com"]
DEBUG = False
STATIC_ROOT = "/var/www/rosbagBrowser/django_static"
ROSBAG_STORAGE_PATH = "/home/ubuntu/rosbagBrowser/testdata"
ROSBAG_MOUNT_PATH = "/opt/aufnahmen"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SILENCED_SYSTEM_CHECKS = [
    "security.W004"  # We don't want to use HSTS for staging server
]
