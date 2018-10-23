
from flask import render_template, request, redirect, session, url_for
from flask import send_from_directory, abort, flash
from flask import Flask

from functools import wraps

from app import app
import pymysql.cursors
import hashlib
import os, sys, stat
from werkzeug.utils import secure_filename
import uuid
import time
import pyrebase

config = {
    "apiKey": "AIzaSyB4F-ap3T8z1xdRmwWSvMXYBqrBfdh8_BQ",
    "authDomain": "unibid-fba8a.firebaseapp.com",
    "databaseURL": "https://unibid-fba8a.firebaseio.com/",
    "storageBucket": "unibid-fba8a.appspot.com"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not 'username' in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

def authenticated():
    return "username" in session

def get_fname():
    if not authenticated():
        return ""
    if 'first_name' in session:
        return session['first_name']
    email = session['username']

    user = db.child("users").child(make_unique_id(email)).get().val()
    session['first_name'] = user["name"].split()[0]
    return session['first_name']


#Routes Index Page
@app.route('/')
def index():
    return render_template("index.html", title='Unibid', isAuthenticated=authenticated(), fname=get_fname())

#Routes About Page
@app.route('/about/')
def about():
    return render_template("about.html", title='About', isAuthenticated=authenticated(), fname=get_fname())

#Routes Login Page
@app.route('/login')
@app.route('/login/')
def login():
    return render_template("login.html", title='Login')

#Routes Register Page
@app.route('/register')
@app.route('/register/')
def register():
    return render_template("register.html", title='Register')

#Routes Settings Page
@app.route('/settings')
@app.route('/settings/')
def settings():
    return render_template("settings.html", title='Settings', fname=get_fname())

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    hash = hashlib.md5(password.encode('utf-8')).hexdigest()
    user = db.child("users").child(make_unique_id(username)).get().val()

    if( user is None ):
        error = 'Invalid username.'
        return render_template('login.html', error=error)
    
    if( hash == user["hash"] and username == user["email"]):
        session['username'] = username
        session['first_name'] = user['name'].split()[0]
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid username or password.'
        return render_template('login.html', error=error)

def make_unique_id(email):
    email = email.replace('@', '')
    email = email.replace('.', '')
    return email

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    passconf = request.form['pass-conf']

    if password != passconf:
        error = "Passwords do not match."
        return render_template('register.html', error=error)
    if email[-3:] != "edu":
        error = "Email is not .edu."
        return render_template('register.html', error=error)
    fname = request.form['fname']
    lname = request.form['lname']
    hash = hashlib.md5(password.encode('utf-8')).hexdigest()

    school = request.form['school']

    user = {
        'name': fname + ' ' + lname,
        'email': email.lower(),
        'hash': hash,
        'school': school,
        'rating':"5",
    }
    try:
        user_id = make_unique_id(email)
        db.child("users").child(user_id).set(user)
        db.child("favorites").child(user_id).set({"placeholder":1})
        db.child("messages").child(user_id).set({"placeholder":"placeholder"})
    except Exception as err:
        return render_template('register.html', error=err)
    session['username'] = email
    return redirect(url_for('home'))


@app.route('/changeAccountInfo', methods=['GET', 'POST'])
def changeAccountInfo():
    uname = session['username']
    #grabs information from the forms
    fname = request.form['fname']
    lname = request.form['lname']
    password = request.form['password']
    passconf = request.form['pass-conf']
    school = request.form['school']

    if password != passconf:
        error = "Passwords do not match."
        return render_template('settings.html', error=error)

    hash = hashlib.md5(password.encode('utf-8')).hexdigest()
    user = db.child("users").child(make_unique_id(uname)).get().val()

    user["name"] = fname + ' ' + lname
    user["hash"] = hash
    user["school"] = school

    db.child("users").child(make_unique_id(uname)).update(user)

    return redirect(url_for('home'))

@app.route('/home')
@login_required
def home():
    uname = session['username']
    searchQuery = request.args.get('q')
    if searchQuery:
        results = db.child("ads").get().val()
        posts=[]
        for key,value in results.items():
            if(key != "placeholder" and searchQuery.lower() in value["title"].lower()):
                value["id"]=key
                del value["comments"]["placeholder"]
                posts.append(value)
        return render_template('home.html', username=uname, posts=posts, fname=get_fname())
    else:
        results = db.child("ads").get().val()
        posts=[]
        for key,value in results.items():
            if(key != "placeholder"):
                value["id"]=key
                del value["comments"]["placeholder"]
                posts.append(value)
        return render_template('home.html', username=uname, posts=posts, fname=get_fname())


#Logging out
@app.route('/logout')
def logout():
    session.pop('first_name')
    session.pop('username')
    return redirect('/')

#Posting
@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    uname = session['username']

    title = request.form['title']
    description = request.form['description']
    photo = request.files['file']
    date = time.strftime("%m-%d-%y %H:%M")
    starting_price = request.form["starting_price"]

    if photo:
        filename = secure_filename(photo.filename)
        os.chmod(app.config["PHOTO_DIRECTORY"], 0o775)
        newfilename = uuid.uuid4().hex
        photo.save(os.path.join(app.config["PHOTO_DIRECTORY"], newfilename))

    
    user = db.child("users").child(make_unique_id(uname)).get().val()
    ad = { "title": title, "description": description, "photo": newfilename, "date": date, "name":user["name"], "username": uname, "current_price":starting_price, "current_bidder": "None", "comments": {"placeholder":{"username":"placeholder", "text":"placeholder", "time": "placeholder", "name": "placeholder"} } }
    db.child("ads").push(ad)
    
    return redirect(url_for('home'))

@app.route('/chat')
@login_required
def chat():
    uname = session['username']
    data = db.child("users").get().val()
    my_profile = data[make_unique_id(uname)]
    del data[make_unique_id(uname)]
    all_profiles = []
    for key, value in data.items():
        if(key!="placeholder"):
            value["id"]=key
            all_profiles.append(value)
    
    messages = db.child("messages").child(make_unique_id(uname)).get().val()
    all_chats=[]
    for key, value in messages.items():
        if(key!="placeholder"):
            all_chats.append(value)


    return render_template('chat.html', userid = make_unique_id(uname), users=all_profiles, fname=get_fname(), chats = all_chats)

@app.route('/startChat', methods=['POST'])
@login_required
def addChat():
    uname = session['username']
    uname = make_unique_id(uname)
    userSelected = request.form['user']
    
    text = request.form['message']
    
    openChats = db.child("messages").child(uname).get().val()
    for key, usersMessaged in openChats.items():
        if usersMessaged == userSelected:
            flash("Conversation with user already started!", "warning")
            return redirect(url_for('chat'))

    user_temp = db.child("users").child(userSelected).get().val()
    user_name = user_temp["name"]
    db.child("messages").child(uname).child(userSelected).child("name").set(user_name)

    userSelected_temp = db.child("users").child(uname).get().val()
    userSelected_name = userSelected_temp["name"]
    db.child("messages").child(userSelected).child(uname).child("name").set(userSelected_name)

    message = { "sender":userSelected, "sendername": userSelected_name, "receiver":uname, "receivername": user_name,  "message": text, "time": time.strftime("%m-%d-%y %H:%M")}

    db.child("messages").child(uname).child(userSelected).push(message)
    db.child("messages").child(userSelected).child(uname).push(message)

    return redirect(url_for('chat'))

@app.route('/postdel', methods=['GET'])
@login_required
def postdel():
    uname = session['username']

    #extract params
    id = request.args.get('id')
    ad = db.child("ads").child(id).get().val()
    if uname != ad["username"]:
        abort(403)
    else:
        db.child("ads").child(id).remove()
    return redirect(url_for('home'))


# Retrieve user photos only if logged in
@app.route('/content/<path:filename>')
def retrieve_file(filename):
    if not authenticated():
        abort(404)

    uname = session['username']
    return send_from_directory(app.config['PHOTO_DIRECTORY'], filename)


@app.route('/comment', methods=['POST'])
@login_required
def comment():
    uname = session['username']
    id = request.form['id']
    comment_text = request.form['comment']
    user = db.child("users").child(make_unique_id(uname)).get().val()
    full_name = user["name"]
    
    if comment_text == '':
        return redirect(url_for('home'))
    db.child("ads").child(id).child("comments").push({"username":uname, "text":comment_text, "time": time.strftime("%m-%d-%y %H:%M"), "name": full_name})
    return redirect(url_for('home'))

@app.route('/commentdel', methods=['GET'])
@login_required
def commentdel():
    uname = session['username']

    #extract params
    cid = request.args.get('cid')
    id = request.args.get('id')
    commenter = request.args.get('username')
    time = request.args.get('ts')
    
    comments = db.child("ads").child(id).child("comments").get().val()
    del comments[cid]
    db.child("ads").child(id).child("comments").set(comments)
    return redirect(url_for('home'))

@app.route('/profiles', methods=['GET'])
@login_required
def profiles():
    uname = session['username']
    data = db.child("users").get().val()
    my_profile = data[make_unique_id(uname)]
    del data[make_unique_id(uname)]
    all_profiles = []
    for key, value in data.items():
        if(key!="placeholder"):
            value["id"]=key
            all_profiles.append(value)

    return render_template('profiles.html', username=uname, profiles=all_profiles, me = my_profile, fname=get_fname())

@app.route('/rateUser', methods= ['POST'])
@login_required
def rateUser():
    rating = request.form['rating']
    user_id = request.form['id']
    db.child("users").child(user_id).update({"rating":rating})
    return redirect(url_for('profiles'))


@app.route('/bid', methods=['POST'])
@login_required
def bid():
    uname = session['username']
    id = request.form['id']
    ad = db.child("ads").child(id).get().val()
    bid = int(request.form['bid'])
    if (uname == ad["username"]):
        error = "Can't bid on your own item."
        flash(error, "warning")
        return redirect(url_for('home'))
    if (bid <= int(ad["current_price"])):
        error = "Bid too low."
        flash(error, "warning")
        return redirect(url_for('home'))
    user = db.child("users").child(make_unique_id(uname)).get().val()
    name = get_fname()
    db.child("ads").child(id).update({"current_price": bid, "current_bidder": name})
    return redirect(url_for('home'))


@app.route('/favoriteAdd', methods=['POST'])
@login_required
def addFavorite():
    uname = session['username']
    id = request.form['id']
    ad = db.child("ads").child(id).get().val()
    db.child("favorites").child(make_unique_id(uname)).update({id:1})
    return redirect(url_for('favorites'))

@app.route('/favoriteDel', methods=['POST'])
@login_required
def deleteFavorite():
    username = session['username']
    uname = make_unique_id(username)
    id = request.form['id']
    favs = db.child("favorites").child(uname).get().val()
    del favs[id]
    db.child("favorites").child(uname).set(favs)
    return redirect(url_for('home'))

#Favorites
@app.route('/favorites')
@login_required
def favorites():
    username = session['username']
    uname = make_unique_id(username)
    favorites = db.child("favorites").child(uname).get().val()
    ads = db.child("ads").get().val()
    data = []
    user_favorites = []
    for key,value in favorites.items():
        if key != "placeholder":
            user_favorites.append(key)
    for key, value in ads.items():
        if key in user_favorites:
            value["id"]=key
            del value["comments"]["placeholder"]
            data.append(value)
    if len(data) == 0:
        flash("You have not saved any posts yet!", "warning")
    return render_template("favorites.html", username=username, posts=data, fname=get_fname())


