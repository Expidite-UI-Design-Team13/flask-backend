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

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)

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

    if result:
        access_token = create_access_token(identity = username)
        result.update({"access_token": access_token})
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        return {"msg": "Incorrrect username or password"}, 401

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

    cur.execute("select count(*) from expidite.users where email=%s", email)
    result = cur.fetchone()

    if (result['count(*)'] > 0):
        return {"msg": "Email is already in use. Please login or use a different email."}, 401
    
    cur.execute("select count(*) from expidite.users where username=%s", username)
    result = cur.fetchone()

    if (result['count(*)'] > 0):
        return {"msg": "Username is taken. Please choose a different one."}, 500
    
    cur.execute("select count(*) from expidite.users where email=%s", email)
    result = cur.fetchone()

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
    image = json_data["image"]

    cur.execute("insert into expidite.items set user_id=%s, name=%s, expiration_date=%s, category=%s, location=%s, production_date=%s, alert_days=%s, image=%s;", (user_id, name, expiration_date, category, location, production_date, alert_days, image))
    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

@app.route("/api/items/delete", methods = ["POST"])
@jwt_required()
def delete_item():
    cur = get_cur()

    json_data = request.get_json()
    item_id  = json_data["item_id"]

    try: 
        cur.execute("delete from expidite.items where id=%s", (item_id))
    except pymysql.err.IntegrityError as err:
        return Response("There was a problem deleting the item", status=404, content_type="text/plain")

    return Response("Deleted successfully", status=200, content_type="application.json")

@app.route("/api/items/update", methods = ["POST"])
@jwt_required()
def update_item():
    cur = get_cur()

    json_data = request.get_json()
    item_id  = json_data["item_id"]
    user_id  = json_data["user_id"]
    name  = json_data["name"]
    expiration_date = json_data["expiration_date"]
    category = json_data["category"]
    location = json_data["location"]
    production_date = json_data["production_date"]
    alert_days = json_data["alert_days"]
    image = json_data["image"]

    try: 
        cur.execute("update expidite.items set name=%s, expiration_date=%s, category=%s, location=%s, production_date=%s, alert_days=%s, image=%s where id=%s and user_id=%s;", (name, expiration_date, category, location, production_date, alert_days, image, item_id, user_id))
    except pymysql.err.IntegrityError as err:
        return Response("There was a problem deleting the item", status=404, content_type="text/plain")

    return Response("updated successfully", status=200, content_type="application.json")

# get categories for specified user
@app.route("/api/categories", methods = ["GET", "POST"])
@jwt_required()
def get_categories():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]

    cur.execute("SELECT DISTINCT * FROM expidite.categories where user_id=%s;", user_id)
    result = cur.fetchall()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# add category for specified user
@app.route("/api/categories/add", methods = ["POST"])
@jwt_required()
def add_category():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]
    category = json_data["category"]

    cur.execute("select count(*) from expidite.categories where user_id=%s and category=%s", (user_id, category))
    result = cur.fetchone()

    if (result['count(*)'] > 0):
        return {"msg": "This catgeory already exists."}, 500

    cur.execute("insert into expidite.categories set user_id=%s, category=%s;", (user_id, category))
    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# update category for specified user
@app.route("/api/categories/update", methods = ["POST"])
@jwt_required()
def update_category():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]
    updated_category = json_data["updated_category"]
    current_category = json_data["current_category"]

    cur.execute("select count(*) from expidite.categories where user_id=%s and category=%s", (user_id, updated_category))
    result = cur.fetchone()

    if (result['count(*)'] > 0):
        return {"msg": "This catgeory already exists."}, 500

    cur.execute("update expidite.categories set category=%s where user_id=%s and category=%s;", (updated_category, user_id, current_category))
    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# delete category for specified user
@app.route("/api/categories/delete", methods = ["POST"])
@jwt_required()
def delete_category():
    cur = get_cur()

    json_data = request.get_json()
    user_id = json_data["user_id"]
    category  = json_data["category"]

    try: 
        cur.execute("delete from expidite.categories where category=%s and user_id=%s", (category, user_id))
    except pymysql.err.IntegrityError as err:
        return Response("There was a problem deleting the category", status=404, content_type="text/plain")

    return Response("Deleted successfully", status=200, content_type="application.json")

# get locations for specified user
@app.route("/api/locations", methods = ["GET", "POST"])
@jwt_required()
def get_locations():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]

    cur.execute("SELECT DISTINCT * FROM expidite.locations where user_id=%s;", user_id)
    result = cur.fetchall()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# add location for specified user
@app.route("/api/locations/add", methods = ["POST"])
@jwt_required()
def add_location():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]
    location = json_data["location"]

    cur.execute("insert into expidite.locations set user_id=%s, location=%s;", (user_id, location))
    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# update location for specified user
@app.route("/api/locations/update", methods = ["POST"])
@jwt_required()
def update_location():
    cur = get_cur()

    json_data = request.get_json()
    user_id  = json_data["user_id"]
    updated_location = json_data["updated_location"]
    current_location = json_data["current_location"]

    cur.execute("select count(*) from expidite.locations where user_id=%s and location=%s", (user_id, updated_location))
    result = cur.fetchone()

    if (result['count(*)'] > 0):
        return {"msg": "This location already exists."}, 500

    cur.execute("update expidite.locations set location=%s where user_id=%s and location=%s;", ( updated_location, user_id, current_location))
    result = cur.fetchone()

    if result:
        rsp = Response(json.dumps(result, indent=4), status=200, content_type="application.json")
    else:
        rsp = Response(json.dumps([]), status=200, content_type="text/plain")

    return rsp

# delete location for specified user
@app.route("/api/locations/delete", methods = ["POST"])
@jwt_required()
def delete_location():
    cur = get_cur()

    json_data = request.get_json()
    user_id = json_data["user_id"]
    location  = json_data["location"]

    try: 
        cur.execute("delete from expidite.locations where location=%s and user_id=%s", (location, user_id))
    except pymysql.err.IntegrityError as err:
        return Response("There was a problem deleting the location", status=404, content_type="text/plain")

    return Response("Location deleted successfully", status=200, content_type="application.json")

if __name__ == '__main__':
    app.run(host="localhost", port=8000, debug=True)
