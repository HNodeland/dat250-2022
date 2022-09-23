from logging import error
from flask import Flask, g
from config import Config
from flask_bootstrap import Bootstrap
#from flask_login import LoginManager
import sqlite3
import os
from sqlite3 import Error
import sys
from werkzeug.security import generate_password_hash, check_password_hash

#this is a test comment for discord bot
# create and configure app
app = Flask(__name__)
Bootstrap(app)
app.config.from_object(Config)

# TODO: Handle login management better, maybe with flask_login?
#login = LoginManager(app)

# get an instance of the db
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

# initialize db for the first time
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# perform generic query, not very secure yet
def query_db(query, one=False):
    db = get_db()
    cursor = db.execute(query)
    rv = cursor.fetchall()
    cursor.close()
    db.commit()
    return (rv[0] if rv else None) if one else rv

# TODO: Add more specific queries to simplify code

#TEMP TEST QUERY AV HÅKON, IKKE RØR
def verify_login(username):
    try:
        print(username, file=sys.stderr)
        sql = "SELECT * FROM Users WHERE username = :username"
        db = get_db()
        cursor = db.execute(sql, {'username': username})

        valid_user = []
        for Users in cursor:
            valid_user.append({
                "username": username
                })

        if len(valid_user) == 0:
            return (0, False)
        return (valid_user[0], True)
    except Error as e:
        print(e)

def register_account(username, first_name, last_name, password):
    print(username, file=sys.stderr)
    print(first_name, file=sys.stderr)
    print(last_name, file=sys.stderr)
    print(password, file=sys.stderr)
    sql ="""INSERT INTO Users (username, first_name, last_name, password) VALUES (?,?,?,?) """
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, (username, first_name, last_name, password))
        conn.commit()
        
    except Error as e:
        print(e)

# automatically called when application is closed, and closes db connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# initialize db if it does not exist
if not os.path.exists(app.config['DATABASE']):
    init_db()

if not os.path.exists(app.config['UPLOAD_PATH']):
    os.mkdir(app.config['UPLOAD_PATH'])

from app import routes