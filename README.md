# ROSBag Browser

Web page for browsing ROS bags.

## Additional Metadata

While the browser works without it, the real value lies in providing additional metadata about the ROS bags.
This metadata is stored in a file called `additional_metadata.json` next to `metadata.yaml` in the bag directory:

```json
{
  "description": "This rosbag was recorded sept. 8 and contains IMU and camera data.",
  "hardware": "Spatz11_1",
  "tags": [
    "odometry",
    "test"
  ],
  "location": "testtrack_workshop"
}
```

The JSON schema is provided in
[`rosbagsApp/static/rosbagsApp/additional_metadata_schema.json`](rosbagsApp/static/rosbagsApp/additional_metadata_schema.json),
and each `additional_metadata.json` must conform to the schema (this is automatically validated when reading the file).

## Previews

Previews of contained data helps in finding a usable ROS bag.
We want to show preview images of video-topics, but generation of these is currently not implemented.
For now, all files in the `thumbnails` subdirectory of each ROS bag are displayed as images.

## Dev Setup

### Dependencies

All dependencies are specified in `requirements.txt`.

### Configuration

Login is only supported through GitLab. To configure, create a app with `read_user` scope
(gitlab.example.com/-/profile/applications) and provide the credentials via environment variables or `.env` file in the
project root:

```dotenv
GITLAB_KEY=abc...
GITLAB_SECRET=def...
```

Configure your gitlab url in [`rosbagBrowser/settings.py`](rosbagBrowser/settings.py):

```python
SOCIAL_AUTH_GITLAB_API_URL = "https://git.spatz.wtf"
```

For more details, see the
[`python-social-auth` documentation](https://python-social-auth.readthedocs.io/en/latest/backends/gitlab.html).

ROS bags are stored in a directory on disk. The path must be configured
in [`rosbagBrowser/settings.py`](rosbagBrowser/settings.py).
Additionally, the path under which a user can access the ROS bags can be modified using `ROSBAG_MOUNT_PATH`.
The `ROSBAG_MOUNT_PATH` is only displayed to the user and never accessed by the server, and defaults to the
`ROSBAG_STORAGE_PATH`.

```python
ROSBAG_STORAGE_PATH = "/home/jonas/Projects/Carolo/rosbags"  # Path at which the server accesses ROS bags
ROSBAG_MOUNT_PATH = "/mnt/rosbags"  # Path at which a user accesses ROS bags
```

### Database

The site is currently configured to use sqlite. The database does not store any data related to the ROS bags, but only
temporary information such as user-sessions and local user accounts (only used for initial admin access, all other users
login via GitLab).
It is not required to back up the database, and i have not found a use to even persist it across server restarts.
All data relevant to the ROS bags is stored in the bag directory.
To initially create the database, run the migrations:

```console
foo@bar:~$ ./manage.py migrate
```

## Deployment

(TODO)
