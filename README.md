# web frontend for emo20q

## installation

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
  python3 flask_basic.py
  ```

## deployment

for testing, just create ["self-signed"
certificates](https://www.howtogeek.com/devops/how-to-create-and-use-self-signed-ssl-on-nginx/)

for a more careful staging environment, set the staging subdomain in
route 53 and use the --staging flag on certbot.  This will raise
security flags in the browser. in Chrome, you can type in
["thisisunsafe"](https://stackoverflow.com/questions/7580508/getting-chrome-to-accept-self-signed-localhost-certificate)

for prod, use lets encrypt certbot