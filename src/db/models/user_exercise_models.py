from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserExercise(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    weighted_exercise_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercises.id'), nullable=False)
    calisthenic_exercise_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercises.id'), nullable=False)
    cardio_exercise_id = db.Column(db.Integer(), db.ForeignKey('cardio_exercises.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('user_exercises', lazy=True))
    weight_exercise = db.relationship('WeightedExercise', backref=db.backref('user_exercises', lazy=True))
    calisthenic_exercise = db.relationship('CalisthenicExercise', backref=db.backref('user_exercises', lazy=True))
    cardio_exercise = db.relationship('CardioExercise', backref=db.backref('user_exercises', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'weighted_exercise_id': self.weighted_exercise_id,
            'calisthenic_exercise_id': self.calisthenic_exercise_id,
            'cardio_exercise_id': self.cardio_exercise_id
        }
