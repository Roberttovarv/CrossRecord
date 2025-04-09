from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
 
class CardioExercises(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('CardioExerciseVariation', backref='cardio_exercise', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'variations': [variation.serialize() for variation in self.variations]
        }

class CardioExerciseVariations(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_name = db.Column(db.String(50), nullable=False)
    exercise_id = db.Column(db.Integer(), db.ForeignKey('cardio_exercises.id'), nullable=False)

    cardio_records = db.relationship('CardioRecord', backref='variation')

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id
        }

class CardioRecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    calories = db.Column(db.Numeric(3, 1), nullable=False)
    time = db.Column(db.String(), nullable=False)
    date = db.Column(db.Date(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('cardio_exercise_variation.id'), nullable=False)

    user = db.relationship('Users', backref= db.backref('cardio_records', lazy=True))
    bodyweight = db.Column(db.Numeric(5, 2), nullable=True)

    def serialize(self):
        user_weight = float(self.user.weight)  
        return {
            'id': self.id,
            'time': self.time,
            'calorioes': float(self.calories),
            'date': self.date.strftime('%d/%m/%Y'),
            'user_weight': float(self.bodyweight)
        }    