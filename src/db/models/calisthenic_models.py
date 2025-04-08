from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CalisthenicExercises(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('CalisthenicExerciseVariation', backref='calisthenic_exercise', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'variations': [variation.serialize() for variation in self.variations]
        }

class CalisthenicExerciseVariations(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_name = db.Column(db.String(50), nullable=False)
    exercise_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercises.id'), nullable=False)

    calisthenic_records = db.relationship('CalisthenicRecord', backref='variation')

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id
        }

class CalisthenicRecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    repetitions = db.Column(db.Int(), nullable=False)
    date = db.Column(db.Date(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercise_variation.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('calisthenic_records', lazy=True))

    def serialize(self):
        user_weight = float(self.user.weight)  
        return {
            'id': self.id,
            'repetitions': self.repetitions,
            'date': self.date.strftime('%d/%m/%Y'),
            'user_weight': user_weight
        }    