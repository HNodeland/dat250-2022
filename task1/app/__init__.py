from logging import error
from flask import Flask, g
from config import Config
from flask_bootstrap import Bootstrap
#from flask_login import LoginManager
import sqlite3
import os
from sqlite3 import Error
import sys

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

#GET USERNAME QUERY FOR LOGGING IN
def verify_login(username):
    try:
        print(username, file=sys.stderr)
        sql = "SELECT * FROM Users WHERE username = :username"
        db = get_db()
        cursor = db.execute(sql, {'username': username})

        #add all users found in the databse to a list
        valid_user = []
        for Users in cursor:
            valid_user.append({
                "username": username
                })

        #if the list of user is empty, return false, else return the user and true
        if len(valid_user) == 0:
            return (0, False)
        return (valid_user[0], True)
    except Error as e:
        print(e)
    
def get_user(username):
    try:
        print(username, file=sys.stderr)
        sql = "SELECT * FROM Users WHERE username = :username"
        db = get_db()
        cursor = db.execute(sql, {'username': username})
        user = cursor.fetchone()

        #if a user is found, return the user, else return false
        if user != None:
            return user
        else:
            return False    
    except Error as e:
        print(e)

#ADD A FRIEND QUERY
def add_friend(user_id, friend_id):
    try:
        sql = "INSERT INTO Friends (u_id, f_id) VALUES (?,?)"
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, (user_id, friend_id))
        conn.commit()
    except Error as e:
        print(e)

#REGISTER ACCOUNT QUERY
def register_account(username, first_name, last_name, password):
    #PRINTS VARIABLES TO TERMINAL
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

#CREATE POST QUERY
def create_post(user_id, content, image, time):
    sql = """INSERT INTO Posts (u_id, content, image, creation_time) VALUES(?,?,?,?)"""
    print(user_id, file=sys.stderr)
    print(content, file=sys.stderr)
    print(image, file=sys.stderr)
    print(time, file=sys.stderr)
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, (user_id, content, image, time))
        conn.commit()
    except Error as e:
        print(e)

#CREATE COMMENT QUERY
def create_comment(p_id, user_id, comment, time):
    print(p_id, file=sys.stderr)
    print(user_id, file=sys.stderr)
    print(comment, file=sys.stderr)
    print(time, file=sys.stderr)
    sql = """INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES (?,?,?,?)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, (p_id, user_id, comment, time))
        conn.commit()
    except Error as e:
        print(e)

#UPDATE USER QUERY
def update_user(education, employment, music, movie, nationality, birthday, username):
    try:
        sql = "UPDATE Users SET education = :education , employment = :employment,  music = :music, movie = :movie, nationality = :nationality, birthday = :birthday WHERE username= :username"
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, {'education': education, 'employment': employment, 'music': music, 'movie': movie, 'nationality': nationality, 'birthday': birthday, 'username': username})
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