import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    books =  db.relationship("Book", backref="users", lazy=True)

    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password

    

    def __repr__(self):
        return '<User %r>' % (self.name)


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    reviews = db.relationship("Review", backref="books", lazy=True)

    def add_review(self, user_id, user_username, book_isbn, book_title, rating, text_review):
        r = Review(user_username=user_username, user_id=user_id, book_isbn=self.isbn, rating=rating, text_review=text_review)
        db.session.add(r)
        db.session.commit()
    

    def add_user(self, name, username):
        u = User(name=name, username=username)
        db.session.add(u)
        db.session.commit()


class Review(db.Model):
    __tablename__ = "reviews"
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_username = db.Column(db.String, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text_review = db.Column(db.String, nullable=False)

    
