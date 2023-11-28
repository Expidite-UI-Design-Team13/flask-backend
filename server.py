from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import json
import pymysql
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
jwt = JWTManager(app)

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

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

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token 
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response

# create access token on login
@app.route("/api/users/login", methods = ["GET", "POST"])
def create_token():
    cur = get_cur()

    json_data = request.get_json()

    username  = json_data["username"]
    password = json_data["password"]

    cur.execute("SELECT * FROM expidite.users where username=%s and password=%s;", (username, password))

    result = cur.fetchone()
    access_token = create_access_token(identity = username)
    result.update({"access_token": access_token})

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        return {"msg": "Wrong email or password"}, 401

    return rsp

# get specific user from username and password
@app.route('/api/users/user', methods = ["GET", "POST"])
@jwt_required()
def get_user():
    cur = get_cur()

    json_data = request.get_json()

    id  = json_data["id"]

    cur.execute("SELECT * FROM expidite.users where id=%s;", id)

    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        return {"msg": "User not found"}, 401
    
    return rsp

@app.route("/api/users/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response

# add new user
@app.route("/api/users/signup", methods = ["POST"])
def add_user():
    cur = get_cur()

    json_data = request.get_json()
    username  = json_data["username"]
    password = json_data["password"]
    email = json_data["email"]

    cur.execute("insert into expidite.users set username=%s, password=%s, email=%s;", (username, password, email))

    cur.execute("SELECT * FROM expidite.users where username=%s and password=%s;", (username, password))

    result = cur.fetchone()
    access_token = create_access_token(identity = username)
    result.update({"access_token": access_token})

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# get all items from specified user
# user is determined by user_id in api request route
@app.route("/api/items", methods = ["GET", "POST"])
@jwt_required()
def get_items_by_user():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]

    cur.execute("SELECT DISTINCT * FROM expidite.items where user_id=%s;", user_id)
    result = cur.fetchall()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# add item for specified user
@app.route("/api/items/add", methods = ["POST"])
@jwt_required()
def add_item():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]
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