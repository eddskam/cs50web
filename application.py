import os
import requests
import sys
import json
from flask import Flask, session, render_template, request, url_for,logging, redirect, flash
from flask_jsonpify import jsonify
from flask_session import Session
from sqlalchemy import create_engine, Column, Integer, String, or_, and_
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
from urllib.request import urlopen
from passlib.hash import pbkdf2_sha256
from models import *

app = Flask(__name__)
#key = os.getenv("key") # API KEY
key = "RIAGGrhWLz4rcHLxgQvmXg"
# Check for environment variable
#if not os.getenv("DATABASE_URL"):
    #raise RuntimeError("DATABASE_URL is not set")
DATABASE_URL="postgres://emtsccdibxvgxf:2d333c7d3fd7068beddc067a7bc1dbe6e081439374fee7abc83fa7aa124fd5d9@ec2-174-129-33-181.compute-1.amazonaws.com:5432/d1mt9tes3rdeu0"

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
#engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
   

@app.route("/")
def index():
    """Welcome to rateworthy booksite"""
    return render_template("index.html")

@app.route("/registration", methods=["GET", "POST"])
def registration():
    """Registration Page"""
    if request.method == "POST":
        name  = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        hash = pbkdf2_sha256.hash(password)

        # insert form information into user table
        if db.execute("SELECT username from users WHERE username = :username", {"username" : username}).fetchone() is None:
            if password==confirm:
                db.execute("INSERT INTO users (name, username, password) VALUES(:name,:username,:hash)", {"name" :name, "username" :username, "hash" :hash})
                db.commit()
                flash("You are registered. Login to preceed", "success")
                return redirect(url_for('login'))
            else:
                flash("password does not match", "danger")
                return render_template("registration.html")
        else:
            flash("user already exists. Please login", "danger")
            return redirect(url_for('login'))
    return render_template("registration.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login Page"""

    session.clear()
    # get form information
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        userr = db.execute("SELECT * FROM users WHERE username= :username", {"username": username}).fetchone()
        if userr is None:
            return render_template("login.html", error = "This user does not exist. Please re-enter credentials.")
        db_hash = userr.password
        
        if pbkdf2_sha256.verify(password, db_hash):

            session['logged_in'] = True
            session["username"] = userr.username
            session["user_id"] = userr.id
            flash("You are now logged in", "success")
            return redirect(url_for('search'))

        else:
            return render_template("login.html", error = "Incorrect password or password field left blank. Renter with correct password!")
    return render_template("login.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    """Search Page"""
    #message =  "Please enter either the isbn, author or title of the book you want"
    if request.method == "POST":
        if session.get("user_id") is None:
            render_template("search.html", logout=True)
        query = request.form.get("search")
        query_like = '%' + query + '%'
        books = db.execute("SELECT * FROM books WHERE isbn LIKE :query_like OR title LIKE :query_like OR author LIKE :query_like",
        {"query_like": query_like}).fetchall()

        return render_template("search.html", username=session["username"], books=books, no_books = (len(books)==0))
    if session.get("user_id") is None:
        render_template("search.html", logout=True)
    return render_template("search.html", logout=False, username = session["username"])

@app.route("/logout")
def logout():
    """Log out of current user's session"""
    session.clear()
    return redirect(url_for('index'))

@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    if session.get("user_id") is None:
        #return redirect(url_for('login'))
        return render_template("book.html", logout=True)

    # make sure the book exists
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    if book is None:
        return render_template("book.html", no_book = True)
    
    # select all reviews for this book
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

    # call for Goodreads api for additional reviews
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params ={"key": key, "isbns": book.isbn})

    if res.status_code != 200:
        raise Exception("Error: API request unsuccessful.")

    # extract api json data
    data = res.json()
    rating_num = data["books"][0]["work_ratings_count"]
    api_avg_rating = data["books"][0]["average_rating"]

    # if a user submitted a review
    if request.method == "POST":
        text_review = request.form.get("text_review")
        avg_rating = request.form.get("avg_rating")

        # check if user submitted any reviews before
        user = db.execute("SELECT user_username FROM reviews WHERE user_id = :id AND book_id = :book_id", {"id": session['user_id'], "book_id": book_id}).fetchone()

        # if not - Add this user and their reviews for this book
        if user is None:
            db.execute("INSERT INTO reviews (text_review, rating, book_id, user_id, user_username) VALUES (:text_review, :avg_rating, :book_id, :user_id, :username)",
            {"text_review": text_review, "avg_rating": avg_rating, "book_id": book_id,
            "user_id": session['user_id'], "username": session["username"]})

            # save changes
            db.commit()
        else:
            return render_template("book.html", error = "Error: You have already submitted a review for this book", book=book, reviews=reviews, rating_num=rating_num, api_avg_rating=api_avg_rating, username=session["username"])
    
        # display all reviews after ensuring that the user has not yet submitted a review
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
        return render_template("book.html", reviews=reviews, book=book, rating_num=rating_num, api_avg_rating=api_avg_rating, username=session.get("username"))


    # when the user visits the page via a GET request, render all information on the book, its reviews and its reviews on Goodreads
    return render_template("book.html", book=book, reviews=reviews, rating_num=rating_num, api_avg_rating=api_avg_rating, username=session["username"])
        
@app.route("/api/<isbn>")
def api(isbn):
    if session.get("user_id") is None:
        return redirect(url_for('login'))
    book = db.execute("SELECT id, title, author, year, isbn FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        render_template("error.html", message='book not found')

    # call for Goodreads api
    results = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})

    if results.status_code != 200:
        raise Exception("Error: The API request was unsuccessful!")

    # extract the API data

    api_data = results.json()
    work_ratings_count = api_data['books'][0]['work_ratings_count']
    api_avg_rating = api_data['books'][0]['average_rating']
    return jsonify({"title": book.title, "author": book.author, "year": book.year, "isbn": book.isbn, "review_count": work_ratings_count, "avg_score": float(api_avg_rating)})





    
