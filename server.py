from flask import Flask, Response, request
from flask_cors import CORS
import json
import pymysql
from datetime import datetime

app = Flask(__name__)
CORS(app)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)
 
def get_cur():
    db_user = "root"
    db_pwd = "password"
    db_host = "localhost"

    conn = pymysql.connect(
        user = db_user,
        password = db_pwd,
        host = db_host,
        cursorclass = pymysql.cursors.DictCursor,
        autocommit = True
    )
    return conn.cursor()

@app.route("/")
def home():
    return "Expidite API"

# get all users
@app.route("/api/users", methods = ["GET"])
def get_users():
    cur = get_cur()
    cur.execute("SELECT DISTINCT * FROM expidite.users;")
    result = cur.fetchall()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# get specific user from username and password
@app.route("/api/users/login", methods = ["GET", "POST"])
def get_user():
    cur = get_cur()

    json_data = request.get_json()

    username  = json_data["username"]
    password = json_data["password"]

    cur.execute("SELECT * FROM expidite.users where username=%s and password=%s;", (username, password))

    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# add new user
@app.route("/api/users/add", methods = ["POST"])
def add_user():
    cur = get_cur()

    json_data = request.get_json()
    username  = json_data["username"]
    password = json_data["password"]
    email = json_data["email"]

    cur.execute("insert into expidite.users set username=%s, password=%s, email=%s;", (username, password, email))

    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# get all items from specified user
# user is determined by user_id in api request route
@app.route("/api/items/<user_id>", methods = ["GET"])
def get_items_by_user(user_id):
    cur = get_cur()
    cur.execute("SELECT DISTINCT * FROM expidite.items where user_id=%s;", user_id)
    result = cur.fetchall()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# add item for specified user
@app.route("/api/items/<user_id>/add", methods = ["POST"])
def add_item(user_id):
    cur = get_cur()

    json_data = request.get_json()
    name  = json_data["name"]
    expiration_date = json_data["expiration_date"]
    category = json_data["category"]
    location = json_data["location"]
    production_date = json_data["production_date"]
    alert_days = json_data["alert_days"]

    cur.execute("insert into expidite.items set user_id=%s, name=%s, expiration_date=%s, category=%s, location=%s, production_date=%s, alert_days=%s;", (user_id, name, expiration_date, category, location, production_date, alert_days))
    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

if __name__ == '__main__':
    app.run(host="localhost", port=8000, debug=True)