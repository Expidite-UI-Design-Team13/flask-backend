# flask-backend

### `. .venv/bin/activate`

Activates virtual environment


### `pip install Flask`

Installs Flask


### `pip install pymysql`

Installs python MySQL package

### `pip install flask_cors`

Installs python Flask CORS package


### `flask --app server run`

Runs file names server.py. Open the local host address in the console output and you should see "Hello, World!"


### use ReqBin[https://reqbin.com/] (install extension) to test api routes that require json data
Example adding new item:
route: http://127.0.0.1:5000/api/items/1/add
method: POST
json:
{
  "name": "Tylenol",
  "expiration_date": "2026-06-09",
  "category": "medicine",
  "location": "medicine cabinet",
  "production_date": "2022-08-04",
  "alert_days": 30
}

Example adding new user:
route: http://127.0.0.1:5000/api/users/add
method: POST
json:
{
  "username": "jenny",
  "password": "password123",
  "email": "jenny@jenny.com"
}