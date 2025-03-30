#ref : https://www.youtube.com/watch?v=z3YMz-Gocmw
# pip install flask, flask_sqlalchemy
# test api using postpam - tool to interact with web api

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, fields, marshal_with, abort

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)

class UserModel(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.String(80), unique=True, nullable=False)
    email =  db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"User(name = {self.name}, id = {self.id}, email = {self.email})"

user_args = reqparse.RequestParser()


@app.route('/')
def home():
    return '<h1>Flask Rest API</h1>'

if __name__ == '__main__':
    app.run(debug=True)
