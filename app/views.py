
from flask import render_template, request, redirect, session, url_for
from flask import send_from_directory, abort, flash
from flask import Flask

from functools import wraps

from app import app
from datetime import datetime
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

    fname = request.form['fname']
    lname = request.form['lname']
    hash = hashlib.md5(password.encode('utf-8')).hexdigest()

    school = request.form['school']

    user = {
        'name': fname + ' ' + lname,
        'email': email,
        'hash': hash,
        'school': school
    }

    try:
        user_id = make_unique_id(email)
        db.child("users").child(user_id).set(user)
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
    results = db.child("ads").get().val()
    posts=[]
    for key,value in results.items():
        value["id"]=key
        posts.append(value)
    
    '''
    searchQuery = request.args.get('q')

    with conn.cursor() as cursor:
        if not searchQuery:
            q =  """
                SELECT id, file_path, content_name, timest,
                    username, first_name, last_name, public
                FROM Content NATURAL JOIN Person
                WHERE username = %s
                OR public
                OR id in (
                    SELECT id
                    FROM Share JOIN Member ON
                    Share.username = Member.username_creator
                        AND Share.group_name = Member.group_name
                    WHERE Member.username = %s
                    )
                ORDER BY timest DESC
                """
            cursor.execute(q, (uname, uname))
        else:
            modifiedSearchQuery = '%' + searchQuery + '%'
            q = """
                SELECT id, file_path, content_name, timest,
                    username, first_name, last_name
                FROM Content NATURAL JOIN Person
                WHERE (
                    username = %s
                    OR public
                    OR id in (
                        SELECT id
                        FROM Share JOIN Member ON
                        Share.username = Member.username_creator
                            AND Share.group_name = Member.group_name
                        WHERE Member.username = %s
                        )
                    )
                AND (
                    content_name like %s
                    OR username like %s
                    )
                ORDER BY timest DESC
                """
            cursor.execute(q, (uname, uname, modifiedSearchQuery, modifiedSearchQuery))

        posts = cursor.fetchall()

        if searchQuery and len(posts) == 0:
            e = "No results found!"
            flash(e, "danger")

        q1 = """
                SELECT id FROM Favorite
                WHERE username = %s
                """

        cursor.execute(q1, (uname))
        favorites = cursor.fetchall()
        favoriteIDs = []
        for favorite in favorites:
            favoriteIDs.append(favorite['id'])

        q1 = """
            SELECT username, first_name, last_name, timest, comment_text
            FROM Comment NATURAL JOIN Person
            WHERE id = %s
            ORDER BY timest DESC
            """

        q2 = """
            SELECT first_name, last_name
            FROM Tag JOIN Person ON
                Tag.username_taggee = Person.username
            WHERE id = %s AND status = true
            ORDER BY timest DESC
            """

        q3 = """
            SELECT group_name
            FROM Share
            WHERE id = %s
            """

        for p in posts:
            cursor.execute(q1, (p['id']))
            p['comments'] = cursor.fetchall()

            cursor.execute(q2, (p['id']))
            p['tags'] = cursor.fetchall()

            cursor.execute(q3, (p['id']))
            p['groups'] = cursor.fetchall()

        q = """
            SELECT username_creator, group_name
            FROM Member
            WHERE username = %s
            """
        cursor.execute(q, (uname))
        groups = cursor.fetchall()
    '''
    return render_template('home.html',
                           #search=searchQuery,
        username=uname,
        posts=posts,
                           #favorites=favoriteIDs,
        fname=get_fname(),
                           #groups=groups
        )


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
    date = datetime.now().strftime('%m-%d-%y %H:%m')

    if photo:
        filename = secure_filename(photo.filename)
        os.chmod(app.config["PHOTO_DIRECTORY"], 0o775)
        newfilename = uuid.uuid4().hex
        photo.save(os.path.join(app.config["PHOTO_DIRECTORY"], newfilename))
    user = db.child("users").child(make_unique_id(uname)).get().val()
    ad = { "title": title, "description": description, "photo": filename, "date": date, "name":user["name"], "username": uname }
    db.child("ads").push(ad)
    
    return redirect(url_for('home'))


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

#     if res:
#         return send_from_directory(app.config['PHOTO_DIRECTORY'], filename)
#     else:
#         abort(404)

# @app.route('/comment', methods=['POST'])
# @login_required
# def comment():
#     uname = session['username']
#     id = request.form['id']
#     comment_text = request.form['comment']

#     if comment_text == '':
#         return redirect(url_for('home'))

#     q = """
#         INSERT INTO Comment(id, username, comment_text)
#         VALUES (%s, %s, %s)
#         """

#     with conn.cursor() as cursor:
#         cursor.execute(q, (id, uname, comment_text))

#     conn.commit()
#     return redirect(url_for('home'))

# @app.route('/commentdel', methods=['GET'])
# @login_required
# def commentdel():
#     uname = session['username']

#     #extract params
#     id = request.args.get('id')
#     commenter = request.args.get('username')
#     ts = request.args.get('ts')

#     # get content owner
#     q = 'SELECT username\
#          FROM Content\
#          WHERE id = %s'
#     cursor = conn.cursor()
#     cursor.execute(q, (id))
#     item_owner = cursor.fetchone()['username']

#     if uname != item_owner and uname != commenter:
#         return redirect(url_for('home'))

#     q = 'DELETE FROM Comment\
#          WHERE id = %s\
#          AND username = %s\
#          AND timest = %s'

#     cursor.execute(q, (id, commenter, ts))
#     conn.commit()
#     cursor.close()
#     return redirect(url_for('home'))

# def fetch_friend_data(uname):
#     with conn.cursor() as cursor:
#         cursor = conn.cursor()
#         q = """
#             SELECT first_name,
#                 last_name, id,
#                 Tag.timest, content_name,
#                 username_tagger,
#                 username_taggee
#             FROM Person JOIN Tag
#                 ON Person.username = Tag.username_tagger
#                 JOIN Content USING(id) 
#             WHERE not status
#             AND username_taggee = %s
#             ORDER BY timest DESC
#             """

#         cursor.execute(q, (uname))
#         tags_pending = cursor.fetchall()

#         q = """
#             SELECT first_name,
#                 last_name, id,
#                 Tag.timest, content_name,
#                 username_tagger,
#                 username_taggee
#             FROM Person JOIN Tag
#                 ON Person.username = Tag.username_taggee
#                 JOIN Content USING(id) 
#             WHERE not status
#             AND username_tagger = %s
#             ORDER BY timest DESC
#             """

#         cursor.execute(q, (uname))
#         tags_proposed = cursor.fetchall()


#         q = """
#             SELECT group_name, description
#             FROM FriendGroup
#             WHERE username = %s
#             """

#         cursor.execute(q, (uname))
#         groups = cursor.fetchall()

#         q = """
#             SELECT username, first_name, last_name
#             FROM Person NATURAL JOIN Member
#             WHERE group_name = %s
#             AND username_creator = %s
#             """

#         for g in groups:
#             cursor.execute(q, (g['group_name'], uname))
#             g['members'] = cursor.fetchall()

#     return {
#         'tags_pending': tags_pending,
#         'tags_proposed': tags_proposed,
#         'groups': groups
#     }


# @app.route('/friends')
# @login_required
# def friends():
#     d = fetch_friend_data(session['username'])
#     return render_template(
#         'friends.html',
#         tags_pending=d['tags_pending'],
#         tags_proposed=d['tags_proposed'],
#         groups=d['groups'],
#         fname=get_fname()
#         )

# @app.route('/tag', methods=['POST'])
# @login_required
# def tag():
#     uname = session['username']

#     taggee = request.form['taggee']
#     id = request.form['id']


#     q = """
#         INSERT INTO Tag(username_tagger, username_taggee, id, status)
#         VALUES (%s, %s, %s, %s)
#         """

#     if uname == taggee:
#         with conn.cursor() as cursor:
#             cursor.execute(q, (uname, uname, id, 1))
#         conn.commit()
#     else:
#         #verify the taggee is valid
#         v = """
#             SELECT id
#             FROM Content
#             WHERE id = %s
#             AND (
#                 public
#                 OR id IN (
#                     SELECT id
#                     FROM Share JOIN Member ON
#                     Share.username = Member.username_creator
#                     AND Share.group_name = Member.group_name
#                     Where Member.username = %s
#                 )
#             )
#             """
#         with conn.cursor() as cursor:
#             cursor.execute(v, (id, taggee))
#             res = cursor.fetchone()

#         if res:
#             try:
#                 with conn.cursor() as cursor:
#                     cursor.execute(q, (uname, taggee, id, 0))
#                 conn.commit()
#             except pymysql.err.IntegrityError:
#                 e = """
#                 {} is already tagged.
#                 """.format(taggee)
#                 flash(e, "danger")
#         else:
#             e = """
#                 Not a valid tag. {} cannot view that item.
#                 """.format(taggee)
#             flash(e, "danger")


#     return redirect(url_for('home'))


# @app.route('/tagaccept')
# @login_required
# def tagaccept():
#     uname = session['username']

#     tagger = request.args.get('tagger')
#     taggee = request.args.get('taggee')
#     id = request.args.get('id')

#     if uname != taggee:
#         return redirect(url_for('friends'))

#     q = """
#         UPDATE Tag
#         SET status = true
#         WHERE id = %s
#         AND username_tagger = %s
#         AND username_taggee = %s
#         """
#     with conn.cursor() as cursor:
#         cursor.execute(q, (id, tagger, taggee))
#     conn.commit()
#     return redirect(url_for('friends'))

# @app.route('/tagdecline')
# @login_required
# def tagdecline():
#     uname = session['username']

#     tagger = request.args.get('tagger')
#     taggee = request.args.get('taggee')
#     id = request.args.get('id')

#     if uname != taggee:
#         return redirect(url_for('friends'))

#     q = """
#         DELETE FROM Tag
#         WHERE id = %s
#         AND username_tagger = %s
#         AND username_taggee = %s
#         """
#     with conn.cursor() as cursor:
#         cursor.execute(q, (id, tagger, taggee))
#     conn.commit()
#     return redirect(url_for('friends'))

# @app.route('/groupadd', methods=['POST'])
# @login_required
# def groupadd():
#     uname = session['username']

#     group_name = request.form['group_name']
#     desc = request.form['description']

#     q1 = """
#         INSERT INTO FriendGroup(group_name, username, description)
#         VALUES (%s, %s, %s)
#         """

#     q2 = """
#         INSERT INTO Member(username, group_name, username_creator)
#         VALUES (%s, %s, %s)
#         """

#     try:
#         with conn.cursor() as cursor:
#             cursor.execute(q1, (group_name, uname, desc))
#             cursor.execute(q2, (uname, group_name, uname))
#         conn.commit()
#     except pymysql.err.IntegrityError:
#         m = """
#             You already have a group named {}.
#             """.format(group_name)
#         flash(m, "danger")

#     return redirect(url_for('friends'))

# @app.route('/memberadd', methods=['POST'])
# @login_required
# def memberadd():
#     uname = session['username']
#     group_name = request.form['group_name']
#     fname = request.form['fname']
#     lname = request.form['lname']
    
#     q = """
#         SELECT username
#         FROM Person
#         WHERE first_name = %s
#         AND last_name = %s
#         """

#     with conn.cursor() as cursor:
#         cursor.execute(q, (fname, lname))
#         res = cursor.fetchall()
    
#     if len(res) == 0:
#         m = """
#             There is no user {} {}.
#             """.format(fname, lname)
#         flash(m, "warning")
#     elif len(res) > 1:
#         #need to implement better solution
#         e = "Multiple users have that name. Select the username you wish to add."
#         d = fetch_friend_data(session['username'])
#         return render_template(
#             'friends.html',
#             tags_pending=d['tags_pending'],
#             tags_proposed=d['tags_proposed'],
#             groups=d['groups'],
#             duplicate_name_error=True,
#             usernames=res,
#             fname=get_fname()
#             )
#     else:
#         member = res[0]['username']
#         q = """
#             INSERT INTO Member(username, group_name, username_creator)
#             VALUES (%s, %s, %s)
#             """
#         try:
#             with conn.cursor() as cursor:
#                 cursor.execute(q, (member, group_name, uname))
#             conn.commit()
#             m = "{} successfully add to {}".format(member, group_name)
#             flash(m, "success")
#         except pymysql.err.IntegrityError as e:
#             m = "{} is already in {}.".format(member, group_name)
#             flash(m, "warning")
        
#     return redirect(url_for('friends'))

# @app.route('/memberaddu', methods=['POST'])
# @login_required
# def memberaddu():
#     uname = session['username']
#     member = request.form['username']
#     group_name = request.form['group_name']

#     q = """
#         INSERT INTO Member(username, group_name, username_creator)
#         VALUES (%s, %s, %s)
#         """

#     with conn.cursor() as cursor:
#         try:
#             cursor.execute(q, (member, group_name, uname))
#             conn.commit()
#             m = "{} successfully add to {}".format(member, group_name)
#             flash(m, "success")
#         except pymysql.err.IntegrityError as e:
#             m = "{} is already in {}.".format(member, group_name)
#             flash(m, "warning")
        
#     return redirect(url_for('friends'))

# @app.route('/memberdel')
# @login_required
# def memberdel():
#     uname = session['username']
#     member = request.args.get('member')
#     group = request.args.get('group')

#     if not member or not group:
#         abort(403)

#     if member == uname:
#         m = "You cannot delete yourself from your own group."
#         flash(m, "danger")
#         return redirect(url_for('friends'))

#     # check which tags need to be deleted

#     # Get all Tags that are on items shared by this group
#     # that are not public or shared by another group
#     q1 = """
#         SELECT id, username_tagger, username_taggee
#         FROM Tag AS t
#         WHERE username_taggee = %s
#         AND id in (
#             SELECT id
#             FROM Content
#             WHERE NOT public
#         )
#         AND id in (
#             SELECT id
#             FROM Share
#             WHERE id = t.id
#             AND group_name = %s
#             AND username = %s
#         )
#         AND id not in (
#             SELECT id
#             FROM Share JOIN Member ON
#             Share.username = Member.username_creator
#                 AND Share.group_name = Member.group_name
#             WHERE Member.username = %s
#             AND (
#                 Member.group_name != %s
#                 OR Member.username_creator != %s
#             )
#         )
#         """

#     q2 = """
#         DELETE FROM Tag
#         WHERE id = %s
#         AND username_taggee = %s
#         AND username_tagger = %s
#         """

#     q3 = """
#         DELETE FROM Member
#         WHERE username = %s
#         AND group_name = %s
#         AND username_creator = %s
#         """

#     try:
#         with conn.cursor() as cursor:
#             cursor.execute(q1, (member, group, uname, member, group, uname))
#             tagsdel = cursor.fetchall()

#             for t in tagsdel:
#                 cursor.execute(q2, (t['id'], t['username_taggee'], t['username_tagger']))

#             cursor.execute(q3, (member, group, uname))

#         conn.commit()
#         m = """
#             You have defriended {}
#             """.format(member)
#         flash(m, "success")
#     except Exception as e:
#         conn.rollback()
#         flash(str(e), "danger")

#     return redirect(url_for('friends'))

# @app.route('/share', methods=['POST'])
# @login_required
# def share():
#     uname = session['username']
#     groupinfo = request.form['group_info']
#     group, creator = groupinfo.split("^^^")
#     id = request.form['id']

#     q = """
#         SELECT username
#         FROM Content
#         WHERE id = %s
#         """

#     with conn.cursor() as cursor:
#         cursor.execute(q, (id))
#         data = cursor.fetchone()

#     if not data:
#         abort(403)
#     elif data['username'] != uname:
#         flash("You cannot share other users content.", "danger")
#         return redirect(url_for('home'))

#     q = """
#         INSERT INTO Share(id, group_name, username)
#         VALUES (%s, %s, %s)
#         """

#     try:
#         with conn.cursor() as cursor:
#             cursor.execute(q, (id, group, creator))
#         conn.commit()
#         m = """
#             Item successfully shared.
#             """
#         flash(m, 'success')
#     except pymysql.err.IntegrityError:
#         m = """
#             The item is already shared with that group.
#             """
#         flash(m, "warning")

#     return redirect(url_for('home'))

# @app.route('/favoriteAdd', methods=['POST'])
# @login_required
# def addFavorite():
#     uname = session['username']
#     id = request.form['id']

#     q = """
#         INSERT INTO Favorite(id, username)
#         VALUES (%s, %s)
#         """

#     with conn.cursor() as cursor:
#         cursor.execute(q, (id, uname))

#     conn.commit()
#     return redirect(url_for('home'))


# @app.route('/favoriteDel', methods=['POST'])
# @login_required
# def deleteFavorite():
#     uname = session['username']
#     id = request.form['id']

#     q = """
#         DELETE FROM Favorite
#         WHERE id = %s
#         AND username = %s
#         """
    
#     with conn.cursor() as cursor:
#         cursor.execute(q, (id, uname))
    
#     conn.commit()
#     return redirect(url_for('home'))

# #Favorites
# @app.route('/favorites')
# @login_required
# def favorites():
#     username = session['username']
#     q = """ 
#             SELECT Content.id, file_path, content_name, timest,\
#             Content.username, first_name, last_name\
#             FROM Person NATURAL JOIN Content JOIN Favorite ON (Content.id = Favorite.id) \
#             WHERE Favorite.username = %s\
#            ORDER BY timest DESC\
#         """
#     with conn.cursor() as cursor:
#         cursor.execute(q, (username))
#         data = cursor.fetchall()
    
#     q2 = 'SELECT username, first_name, last_name, timest, comment_text\
#     FROM Comment NATURAL JOIN Person\
#     WHERE id = %s\
#     ORDER BY timest DESC'
    
#     q3 = 'SELECT first_name, last_name\
#     FROM Tag JOIN Person ON\
#     Tag.username_taggee = Person.username\
#     WHERE id = %s AND status = true\
#     ORDER BY timest DESC'

#     q = """
#             SELECT group_name
#             FROM FriendGroup
#             WHERE username = %s
#             """

#     groups = None
#     with conn.cursor() as cursor:
#         cursor.execute(q, (username))
#         groups = cursor.fetchall()

#     if len(data) == 0:
#         flash("You have not saved any posts yet!", "warning")
    
#     for d in data:
#         with conn.cursor() as cursor:
#             cursor.execute(q2, (d["id"]))
#             d['comments'] = cursor.fetchall()
#         with conn.cursor() as cursor:
#             cursor.execute(q3, (d["id"]))
#             d['tags'] = cursor.fetchall()
#     return render_template("favorites.html", username=username, posts=data, fname=get_fname(), groups=groups)

