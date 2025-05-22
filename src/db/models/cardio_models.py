from src.extensions import db
 
class CardioExercise(db.Model):
    __tablename__ = 'cardio_exercises'

    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('CardioExerciseVariations', backref='cardio_exercise', lazy=True, cascade="all, delete-orphan")

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

    cardio_records = db.relationship('CardioRecord', backref='cardio_variation', cascade="all, delete-orphan")

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id,
            'cardio_records': [record.serialize() for record in self.cardio_records]
        }

class CardioRecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    calories = db.Column(db.Numeric(3, 1), nullable=False)
    time = db.Column(db.Integer(), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    is_a_challenge = db.Column(db.Boolean(), nullable=False)
    is_private = db.Column(db.Boolean(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('cardio_exercise_variations.id'), nullable=False)

    user = db.relationship('Users', backref= db.backref('cardio_records', lazy=True))
    variation = db.relationship('CardioExerciseVariations', backref='cardio_variation_records')

    bodyweight = db.Column(db.Numeric(5, 2), nullable=True)

    def serialize(self):
        user_weight = float(self.user.weight) 
        return {
            'id': self.id,
            'calories': float(self.calories),
            'time': self.time,
            'date': self.date.strftime('%d/%m/%Y'),
            'bodyweight': float(user_weight),
            'exercise': self.variation.variation_name,
            'is_a_challenge': self.is_a_challenge,
            'user': self.user.id
        }  