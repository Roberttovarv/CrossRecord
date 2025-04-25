from ...extensions import db

class CalisthenicExercises(db.Model):
    __tablename__ = 'calisthenic_exercises'
    
    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('CalisthenicExerciseVariations', backref='calisthenic_exercise', lazy=True)

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
    repetitions = db.Column(db.Integer(), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    is_a_challenge = db.Column(db.Boolean(), nullalble=False)


    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercise_variations.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('calisthenic_records', lazy=True))
    variation = db.relationship('CalisthenicExerciseVariations', backref='calisthenic_records')

    bodyweight = db.Column(db.Numeric(5, 2), nullable=True)

    def serialize(self):
        user_weight = float(self.user.weight) 
        return {
            'id': self.id,
            'lifted_weight': float(self.lifted_weight),
            'date': self.date.strftime('%d/%m/%Y'),
            'bodyweight': float(user_weight),
            'exercise': self.variation.variation_name,
            'is_a_challenge': self.is_a_challenge
        }  