
import pyrebase

config = {
	"apiKey": "AIzaSyB4F-ap3T8z1xdRmwWSvMXYBqrBfdh8_BQ",
        "authDomain": "unibid-fba8a.firebaseapp.com",
        "databaseURL": "https://unibid-fba8a.firebaseio.com/",
        "storageBucket": "unibid-fba8a.appspot.com"
    }

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
user = auth.sign_in_with_email_and_password("so1068@nyu.edu", "password")

db = firebase.database()

jake = {"name": "Jake Goldstein", "email": "jake@unibid.com", "hash": "afhifh4233214f", "school": "New York Univesity"}
db.child("users").push(jake, user['idToken'])


# db.child("users").child(email_address).set(shlomi)
# or
# db.child("users").child(shlomi[email]).set(shlomi)