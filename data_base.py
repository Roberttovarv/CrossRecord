from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm import validates, backref
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

db = SQLAlchemy()

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password = db.Column(db.String(25), nullable=False)
    is_premium = db.Column(db.Boolean(), nullable=True)
    name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<User: {self.username}>'

    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'last_name': self.last_name,
            'username': self.username,
            'is_premium': self.is_premium
        }

    @validates('password')
    def validate_password(self, key, password):
        if len(password) < 8:
            raise ValueError('Password must contain at least 8 characters')
        elif not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one character')
        elif not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        elif not any(char.islower() for char in password):
            raise ValueError('Password must contain at least one lowercase letter')
        elif not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/~`" for char in password):
            raise ValueError('Password must contain at least one special character')
        return password

class Cleans(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    last_pr = db.Column(db.Numeric(3, 3), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    user_to = db.relationship('Users', backref=db.backref('cleans', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'last_pr': self.last_pr,
            'date': self.date.strftime('%d/%m/%Y'), 
            'user_id': self.user_id
        }
