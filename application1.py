import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import hashlib
import passlib
#from passlib.hash import pbkdf2_sha256
from passlib.hash import sha256_crypt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.route("/")
def index():
    """Welcome to the rateworthy booksite"""
    return render_template("index.html")
    #return "Project 1: TODO"


@app.route("/registration", methods=["POST", "GET"])
def registration():
    """Registration page"""

    # get the form information
    if request.method=="GET":
        return render_template("registration.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        #hashh = generate_password_hash('password', method='pbkdf2:sha1', salt_length=8)
        hashh = pbkdf2_sha256.hash(password)
        if username is "" or username is " ":
            return render_template("error.html", message="Invalid username")
    
    # insert form information into user table
        if db.execute("SELECT * from users WHERE username = :username", {"username" : username}).fetchone() is not None:
            return render_template("error.html", message="User already exists")
        else:
            db.execute("INSERT into users (username, password) VALUES (:username, :password)",
            {'username': username, 'password': hashh})
        
            db.commit()
        return render_template("login.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    """Login page"""

    session.clear()
    # get form information
    if request.method=="GET":
        return render_template("login.html")
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        #hashh = generate_password_hash('password', method='pbkdf2:sha1', salt_length=8)
        
        userr = db.execute("SELECT * FROM users WHERE username= :username", {"username": username}).fetchone()
        #u = User(username=username, password=password)
    
        if userr is None:
            return render_template("error.html", message="User not found")
        db.commit()
        return render_template("search.html")
            
        
            
        
        
        #db.commit()
        #else:
        #return render_template("error.html", message="User not found in database")
            #return render_template("search.html")
            #session['logged_in'] = True
            #session['username'] = userr.username
            #session["user_id"] = userr['user_id']

@app.route("/logout")
def logout():
    """You have successfully logged out"""
    return render_template("logout.html")

@app.route("/search", methods=["POST", "GET"])
def search():
    """Search Page"""
    if request.method == "GET":
        return render_template("search.html")
    title = request.form.get("title")
    author = request.form.get("author")
    year = request.form.get("year")
    text1 = f"%{title}%".lower()
    text2 = f"%{author}%".lower()
    text3 = f"%{year}%"
    display = db.execute("SELECT * from book WHERE LOWER(title) LIKE :title OR LOWER(author) LIKE :author OR year LIKE :year ORDER BY id LIMIT 10",
    {"title": text1, "author": text2, "year": text3 }).fetchall()
    return render_template("search.html", display=display)

if __name__ == "__main__":
    main()

