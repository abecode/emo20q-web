# web frontend for emo20q

## ACII Paper

The ACII paper that describes this system can be found at [https://arxiv.org/abs/2210.02400](https://arxiv.org/abs/2210.02400)

## Installation

- first, clone this repository (or fork then clone)
  ```
  git clone https://github.com/abecode/emo20q-web.git
  ```
- then cd into directory and clone the main emo20q repo
  ```
  cd emo20q-web
  git clone https://github.com/abecode/emo20q.git
  ```

- to run the flask app:
  ```
  python3 flask_socket_qa.py
  ```

## Deployment

for testing, just create ["self-signed"
certificates](https://www.howtogeek.com/devops/how-to-create-and-use-self-signed-ssl-on-nginx/)

for a more careful staging environment, set the staging subdomain in
route 53 and use the --staging flag on certbot.  This will raise
security flags in the browser. in Chrome, you can type in
["thisisunsafe"](https://stackoverflow.com/questions/7580508/getting-chrome-to-accept-self-signed-localhost-certificate)

for prod, use lets encrypt certbot

here's a page that might help for making the staging to production
switch without finagling the ssl certificates while the new server is
starting it's production role
https://devops4solutions.com/move-lets-encrypt-certs-to-another-server-and-renew-them/
basically copying /etc/letsencrypt

the actual command that is used to run the server in production is

```
 uwsgi --http :5000 --gevent 200 --wsgi-file flask_socket_qa.py --http-websockets --thunder-lock --callable app
 ```