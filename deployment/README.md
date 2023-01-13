## Server

### Install nginx

### Install certbot
```
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot certonly --nginx
```

### Run ansible



* certbot -> run interactive?
* nginx
