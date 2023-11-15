from flask import Flask
from flask_cors import CORS
import json
import pymysql

app = Flask(__name__)
CORS(app)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'expidite'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
 
@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/api")
def health():
    return "Expidite API running!"