from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Challenge(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    challenger_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    challenged_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)

    challenger = db.relationship('Users', foreign_keys=[challenger_id], backref='challenger_challenges')
    challenged = db.relationship('Users', foreign_keys=[challenged_id], backref='challenged_challenges')

    exercise_id = db.Column(db.Integer(), db.ForeignKey('user.exercises.id'), nullable=False)

    exercise = db.relationship('UserExercise', backref='challenges')

    new_record = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.String(50), nullable=True)

    