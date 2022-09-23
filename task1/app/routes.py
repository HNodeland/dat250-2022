from flask import render_template, flash, redirect, url_for, abort
from app import app, query_db, verify_login, register_account
from app.forms import IndexForm, PostForm, FriendsForm, ProfileForm, CommentsForm
from datetime import datetime
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash

# this file contains all the different routes, and the logic for communicating with the database

# home page/login/registration
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = IndexForm()
    if form.login.is_submitted() and form.login.submit.data:
        print("logging in -- ", file=sys.stderr)
        
        # Bruker user fra databasen til å hente ut hasha passord -> passord-input og hasha passord blir sammenliknet
        user = query_db('SELECT * FROM Users WHERE username="{}";'.format(form.login.username.data), one=True)
        verifyPassword = check_password_hash(user['password'], form.login.password.data)

        username = form.login.username.data
        #Valid_user returnerer en tuple, der index 1 representerer
        #om valideringen ble godkjent eller ikke
        #valid_user[1] = True => Godkjent
        #valid_user[1] = False => Ikke godkjent
        #For å hente ut et dictionary med brukernavn og passord:
        #valid_user[0] => {'username': 'test', 'password': 'test'}
        valid_user = verify_login(username)
        if valid_user[1] == 1 and verifyPassword:
            return redirect(url_for('stream', username=username))
        else:
            flash('Sorry, wrong username or password!')
    
    elif form.register.is_submitted() and form.register.submit.data:
        print("registering account -- ", file=sys.stderr)
        new_username = form.register.username.data
        first_name = form.register.first_name.data
        last_name = form.register.last_name.data

        # creates hash from user input and 
        password = generate_password_hash(form.register.password.data)
        confirm_password = check_password_hash(password, form.register.confirm_password.data) 
       
        # confirm_password returns True if the two passwords match
        if confirm_password == True:
            register_account(new_username, first_name, last_name, password)
            flash('Hello ' + new_username + ', your account has succesfully been created!')
        else:
            flash('You have different passwords!')
        
        #query_db('INSERT INTO Users (username, first_name, last_name, password) VALUES("{}", "{}", "{}", "{}");'.format(registerform.username.data, registerform.first_name.data,
         #registerform.last_name.data, registerform.password.data))

        return redirect(url_for('index'))
    return render_template('index.html', title='Welcome', form = form)
# content stream page
@app.route('/stream/<username>', methods=['GET','POST'])
def stream(username):
    form = PostForm()
    user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    if form.is_submitted():
        if form.image.data:
            path = os.path.join(app.config['UPLOAD_PATH'], form.image.data.filename)
            form.image.data.save(path)


        query_db('INSERT INTO Posts (u_id, content, image, creation_time) VALUES({}, "{}", "{}", \'{}\');'.format(user['id'], form.content.data, form.image.data.filename, datetime.now()))
        return redirect(url_for('stream', username=username))

    posts = query_db('SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id={0}) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id={0}) OR p.u_id={0} ORDER BY p.creation_time DESC;'.format(user['id']))
    return render_template('stream.html', title='Stream', username=username, form=form, posts=posts)

# comment page for a given post and user.
@app.route('/comments/<username>/<int:p_id>', methods=['GET', 'POST'])
def comments(username, p_id):
    form = CommentsForm()
    if form.is_submitted():
        user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
        query_db('INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES({}, {}, "{}", \'{}\');'.format(p_id, user['id'], form.comment.data, datetime.now()))

    post = query_db('SELECT * FROM Posts WHERE id={};'.format(p_id), one=True)
    all_comments = query_db('SELECT DISTINCT * FROM Comments AS c JOIN Users AS u ON c.u_id=u.id WHERE c.p_id={} ORDER BY c.creation_time DESC;'.format(p_id))
    try:
        return render_template('comments.html', title='Comments', username=username, form=form, post=post, comments=all_comments)
    except:
        abort(403)

# page for seeing and adding friends
@app.route('/friends/<username>', methods=['GET', 'POST'])
def friends(username):
    form = FriendsForm()
    user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    if form.is_submitted():
        friend = query_db('SELECT * FROM Users WHERE username="{}";'.format(form.username.data), one=True)
        if friend is None:
            flash('User does not exist')
        else:
            query_db('INSERT INTO Friends (u_id, f_id) VALUES({}, {});'.format(user['id'], friend['id']))
    
    all_friends = query_db('SELECT * FROM Friends AS f JOIN Users as u ON f.f_id=u.id WHERE f.u_id={} AND f.f_id!={} ;'.format(user['id'], user['id']))
    try:
        return render_template('friends.html', title='Friends', username=username, friends=all_friends, form=form)
    except:
        abort(403)

# see and edit detailed profile information of a user
@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    form = ProfileForm()
    if form.is_submitted():
        query_db('UPDATE Users SET education="{}", employment="{}", music="{}", movie="{}", nationality="{}", birthday=\'{}\' WHERE username="{}" ;'.format(
            form.education.data, form.employment.data, form.music.data, form.movie.data, form.nationality.data, form.birthday.data, username
        ))
        return redirect(url_for('profile', username=username))
    
    user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    try:
        return render_template('profile.html', title='profile', username=username, user=user, form=form)
    except:
        abort(403)

@app.errorhandler(403)
def forbidden(e):
    return render_template('403_error.html')

@app.errorhandler(404)
def notfound(e):
    print(e)
    return render_template('404_error.html')    

@app.errorhandler(500)
def server_fault(e):
    return render_template('500_error.html')

