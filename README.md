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

for prod, use lets encrypt certbot