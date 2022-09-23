from flask import render_template, flash, redirect, url_for, abort
from app import app, query_db, verify_login, register_account, create_post, create_comment
from app.forms import IndexForm, PostForm, FriendsForm, ProfileForm, CommentsForm
from datetime import datetime
import os
import sys

# this file contains all the different routes, and the logic for communicating with the database

# home page/login/registration
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = IndexForm()
    if form.login.is_submitted() and form.login.submit.data:
        print("logging in -- ", file=sys.stderr)
        #Henter ut brukernavn og passord fra formen
        username = form.login.username.data
        
        #burde kanskje skje noe kryptering rundt denne
        password = form.login.password.data
        
        #Valid_user returnerer en tuple, der index 1 representerer
        #om valideringen ble godkjent eller ikke
        #valid_user[1] = True => Godkjent
        #valid_user[1] = False => Ikke godkjent
        #For å hente ut et dictionary med brukernavn og passord:
        #valid_user[0] => {'username': 'test', 'password': 'test'}
       
        valid_user = verify_login(username, password)
        if valid_user[1] == 1:
            return redirect(url_for('stream', username=username))
        else:
            flash('Sorry, wrong username or password!')
    
    elif form.register.is_submitted() and form.register.submit.data:
        print("registering account -- ", file=sys.stderr)
        new_username = form.register.username.data
        first_name = form.register.first_name.data
        last_name = form.register.last_name.data
        password = form.register.password.data
        confirm_password = form.register.confirm_password.data
       
        if password == confirm_password:
            
            register_account(new_username, first_name, last_name, password)
            flash('Hello ' + new_username + ', your account has succesfully been created!')
        else:
            flash('You have different passwords!')
        return redirect(url_for('index'))
    return render_template('index.html', title='Welcome', form = form)

# content stream page
@app.route('/stream/<username>', methods=['GET','POST'])
def stream(username):
    form = PostForm()
    user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    if form.is_submitted():
        #Checks if an image has been uploaded
        if form.image.data:
            path = os.path.join(app.config['UPLOAD_PATH'], form.image.data.filename)
            form.image.data.save(path)
  
        #Create post variables
        user_id = user['id']
        content = form.content.data
        image = form.image.data.filename
        time = datetime.now()

        #Send variables to the database
        create_post(user_id, content, image, time)
        
        return redirect(url_for('stream', username=username))

    posts = query_db('SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id={0}) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id={0}) OR p.u_id={0} ORDER BY p.creation_time DESC;'.format(user['id']))
    return render_template('stream.html', title='Stream', username=username, form=form, posts=posts)

# comment page for a given post and user.
@app.route('/comments/<username>/<int:p_id>', methods=['GET', 'POST'])
def comments(username, p_id):
    form = CommentsForm()
    if form.is_submitted():
        #Get variables
        user = query_db('SELECT id FROM Users WHERE username="{}";'.format(username), one=True)
        comment = form.comment.data
        time = datetime.now()
        #Send variables to the databse
        create_comment(p_id, user['id'], comment, time)

       
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

