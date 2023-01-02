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
It is not required to back up the database, and I have not found a use to even persist it across server restarts.
All data relevant to the ROS bags is stored in the bag directory.
To initially create the database, run the migrations:

```console
foo@bar:~$ ./manage.py migrate
```

## Deployment

### Server setup

I deployed the staging site at [rosbag-browser-staging.jonasotto.com](https://rosbag-browser-staging.jonasotto.com)
using gunicorn and nginx, mainly following the
[tutorial for django deployment](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04)
and the
[tutorial for nginx+letsencrypt](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04)
from DigitalOcean.

My nginx config (at `/etc/nginx/sites-available/rosbagBrowser`) ended up looking like this:

```
server {
    server_name rosbag-browser-staging.jonasotto.com;

    location /static/ {
        # Ensure nginx has permissions to read this directory!
        root /var/www/rosbagBrowser;
    }
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    listen 443 ssl; # managed by Certbot
    listen [::]:443 ssl;
    ssl_certificate /etc/letsencrypt/live/rosbag-browser-staging.jonasotto.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/rosbag-browser-staging.jonasotto.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    # Redirect https://www.r -> https://r
    server_name www.rosbag-browser-staging.jonasotto.com;
    listen 443 ssl;
    listen [::]:443 ssl;
    ssl_certificate /etc/letsencrypt/live/rosbag-browser-staging.jonasotto.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/rosbag-browser-staging.jonasotto.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    return 301 https://rosbag-browser-staging.jonasotto.com$request_uri;
}

server {
    # Redirect https?://(www.)?r -> https://r
    if ($host = www.rosbag-browser-staging.jonasotto.com) {
        return 301 https://rosbag-browser-staging.jonasotto.com$request_uri;
    }

    if ($host = rosbag-browser-staging.jonasotto.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    listen [::]:80;
    server_name rosbag-browser-staging.jonasotto.com www.rosbag-browser-staging.jonasotto.com;
    return 404; # managed by Certbot
}
```

Gunicorn is run using the systemd config files from the DigitalOcean tutorial.

`/etc/systemd/system/gunicorn.socket`:

```ini
[Unit]
Description = gunicorn socket

[Socket]
ListenStream = /run/gunicorn.sock

[Install]
WantedBy = sockets.target
```

`/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description = gunicorn daemon
Requires = gunicorn.socket
After = network.target

[Service]
User = ubuntu
Group = www-data
WorkingDirectory = /home/ubuntu/rosbagBrowser
Environment = DJANGO_SETTINGS_MODULE=rosbagBrowser.settings_staging
ExecStart = /home/ubuntu/rosbagBrowser/.venv/bin/gunicorn \
            --access-logfile - \
            --bind unix:/run/gunicorn.sock \
            rosbagBrowser.wsgi:application

[Install]
WantedBy = multi-user.target
```

### Venv

All python dependencies and `gunicorn` were installed in a venv:

```console
foo@bar:rosbagBrowser$ python3 -m venv .venv
foo@bar:rosbagBrowser$ source .venv/bin/activate
foo@bar:rosbagBrowser$ pip install requirements.txt
```

### Static files

At time of writing the rosbag application does not require any static files, but the admin panel for example requires
them. Nginx serves them directly, and django can automatically collect all static files in a specified location.
The location is specified by the django setting `STATIC_ROOT = "/var/www/rosbagBrowser/static"`, and files are collected
using `collectstatic`:

```console
foo@bar:rosbagBrowser$ ./manage.py collectstatic
```

### HTTPS

Configuring HTTPS was straightforward using certbot and the
[digitalocean tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-049).
The automatic configuration got me most of the way there, I only added the WWW redirect to end up with the nginx config
above.

```console
foo@bar:~$ sudo certbot --nginx -d rosbag-browser-staging.jonasotto.com -d www.rosbag-browser-staging.jonasotto.com
```

### Database

I skipped the postgresql steps in the tutorial and used the default sqlite config.
