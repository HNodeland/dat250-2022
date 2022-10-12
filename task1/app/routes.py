from flask import render_template, flash, redirect, url_for, abort
from app import app, query_db, verify_login, register_account, create_post, create_comment, get_user, add_friend, update_user, recaptcha
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

    if form.login.validate_on_submit():
        print("logging in -- ", file=sys.stderr)
        # Bruker user fra databasen til å hente ut hasha passord -> passord-input og hasha passord blir sammenliknet
        username = form.login.username.data
        #Sjekker om brukernavnet gikk i inputten er i databasen
        if get_user(username) != False:
            #trust me, det funker
            user = get_user(username)
            if user == False:
                abort(404)
            verifyPassword = check_password_hash(user['password'], form.login.password.data)
        valid_user = verify_login(username)
        if valid_user[1] == 1 and verifyPassword:
            return redirect(url_for('stream', username=username))
        else:
            flash('Sorry, wrong username or password!')

    elif form.register.validate_on_submit():
        print("registering account -- ", file=sys.stderr)
        new_username = form.register.username.data
        first_name = form.register.first_name.data
        last_name = form.register.last_name.data

        # creates hash from user input and 
        password = generate_password_hash(form.register.password.data)
        confirm_password = check_password_hash(password, form.register.confirm_password.data) 
       
        # confirm_password returns True if the two passwords match
        if confirm_password == True and recaptcha.verify():
            register_account(new_username, first_name, last_name, password)
            flash('Hello ' + new_username + ', your account has succesfully been created!')
        elif recaptcha.verify() == False:
            flash('Please fill out the reCAPTCHA form!')
        else:
            flash('You have different passwords!')
        return redirect(url_for('index'))
    return render_template('index.html', title='Welcome', form = form)

# content stream page
@app.route('/stream/<username>', methods=['GET','POST'])
def stream(username):
    form = PostForm()
    user = get_user(username)
    #If the username given in the URL doesn't expict, abort with 404
    if user == False:
            abort(404)
    if form.validate_on_submit():
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
        #Get the user from the database based on the URL
        user = get_user(username)
        if user == False:
            abort(404)
        #Get variables
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
    #Gets the user from the database based on the username given in the URL
    user = get_user(username)
    #If we change the URL to something illegal/a username that isn't doens't exists, go to error page
    if user == False:
        abort(404)
    if form.is_submitted():
        #Searches the database for the given username, returns it to the friend variable
        friend = get_user(form.username.data)
        #get_user returns False if it cant find the given username
        if friend == False:
            flash('User does not exist')
        else:
            add_friend(user['id'], friend['id'])
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
        #Get all variabnles
        education = form.education.data
        employment = form.employment.data
        music = form.music.data
        movie = form.movie.data
        nationality = form.nationality.data
        birthday = form.birthday.data
        #Send variables to the database
        update_user(education, employment, music, movie, nationality, birthday, username)
        return redirect(url_for('profile', username=username))
    user = get_user(username)
    if user == False:
        abort(404)
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

