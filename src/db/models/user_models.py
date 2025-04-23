from sqlalchemy.orm import validates
from ...extensions import db


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password = db.Column(db.String(25), nullable=False)
    is_premium = db.Column(db.Boolean(), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Numeric(5, 2), nullable=True)
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
            'weight': self.weight,
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