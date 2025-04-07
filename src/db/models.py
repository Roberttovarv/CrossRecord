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
    is_premium = db.Column(db.Boolean(), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Numeric(3, 2), nullable=True)
    profile_picture = db.Column(db.String(), nullable=True)

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

class WeightedExercises(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('WeightedExerciseVariation', backref='exercise', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'variations': [variation.serialize() for variation in self.variations]
        }

class WeightedExerciseVariations(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_name = db.Column(db.String(50), nullable=False)
    exercise_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise.id'), nullable=False)

    weight_records = db.relationship('WeightRecord', backref='variation')

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id
        }

class WeightRecord(db.Model):
    id = db.Model(db.Integer(), primary_key=True)
    weight = db.Column(db.Numeric(3, 3), nullable=False)
    date = db.Model(db.Date(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise_variation.id'), nullable=False)

    user = db.relationship('Users', backref= db.backref('weight_records', lazy=True))

    def serialize(self):
        user_weight = float(self.user.weight)  
        return {
            'id': self.id,
            'weight': self.weight,
            'date': self.date.strftime('%d/%m/%Y'),
            'user_weight': user_weight
        }

class UserExercise(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    weighted_exercise_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('user_exercises', lazy=True))
    exercise = db.relationship('WeightedExercise', backref=db.backref('user_exercises', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'exercise_id': self.weighted_exercise_id
        }

class CalisthenicExercises(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('CalisthenicExerciseVariation', backref='exercise', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'variations': [variation.serialize() for variation in self.variations]
        }

class CalisthenicExerciseVariations(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_name = db.Column(db.String(50), nullable=False)
    exercise_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercise.id'), nullable=False)

    repetitions_records = db.relationship('CalisthenicRecord', backref='variation')

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id
        }

class CalisthenicRecord(db.Model):
    id = db.Model(db.Integer(), primary_key=True)
    repetitions = db.Column(db.Numeric(3, 3), nullable=False)
    date = db.Model(db.Date(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise_variation.id'), nullable=False)

    user = db.relationship('Users', backref= db.backref('repetitions_records', lazy=True))

    def serialize(self):
        user_weight = float(self.user.weight)  
        return {
            'id': self.id,
            'repetitions': self.repetitions,
            'date': self.date.strftime('%d/%m/%Y'),
            'user_weight': user_weight
        }    