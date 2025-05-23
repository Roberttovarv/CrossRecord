from src.extensions import db, validate_is_not_blank, validate_existence, validate_length, validate_variation_not_repeated

class CalisthenicExercises(db.Model):
    __tablename__ = 'calisthenic_exercises'
    
    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('CalisthenicExerciseVariations', backref='calisthenic_exercise', lazy=True, cascade="all, delete-orphan")

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

    calisthenic_records = db.relationship('CalisthenicRecord', backref='calisthenic_variation', cascade="all, delete-orphan")

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id,
            'calisthenic_records': [record.serialize() for record in self.calisthenic_records]
        }

class CalisthenicRecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    repetitions = db.Column(db.Integer(), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    is_a_challenge = db.Column(db.Boolean(), nullable=False)
    is_private = db.Column(db.Boolean(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercise_variations.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('calisthenic_records', lazy=True))
    variation = db.relationship('CalisthenicExerciseVariations', backref='calisthenic_variation_records')

    bodyweight = db.Column(db.Numeric(5, 2), nullable=True)

    def serialize(self):
        user_weight = float(self.user.weight) 
        return {
            'id': self.id,
            'repetitions': float(self.repetitions),
            'date': self.date.strftime('%d/%m/%Y'),
            'bodyweight': float(user_weight),
            'exercise': self.variation.variation_name,
            'is_a_challenge': self.is_a_challenge,
            'user': self.user.id
        }