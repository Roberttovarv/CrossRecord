from ...extensions import db

class WeightedExercise(db.Model):
    __tablename__ = 'weighted_exercises'

    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('WeightedExerciseVariations', backref='weight_exercise', lazy=True, cascade="all, delete-orphan")

    def serialize(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'variations': [variation.serialize() for variation in self.variations]
        }

class WeightedExerciseVariations(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_name = db.Column(db.String(50), nullable=False)
    exercise_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercises.id'), nullable=False)

    weight_records = db.relationship('WeightRecord', backref='weighted_variation', cascade="all, delete-orphan")

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id,
            'weight_records': [record.serialize() for record in self.weight_records] 
        }

class WeightRecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lifted_weight = db.Column(db.Numeric(5, 2), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    is_a_challenge = db.Column(db.Boolean(), nullable=False)


    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise_variations.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('weight_records', lazy=True))
    variation = db.relationship('WeightedExerciseVariations', backref='weight_variation_records')

    bodyweight = db.Column(db.Numeric(5, 2), nullable=True)

    def serialize(self):
        user_weight = float(self.user.weight) 
        return {
            'id': self.id,
            'lifted_weight': float(self.lifted_weight),
            'date': self.date.strftime('%d/%m/%Y'),
            'bodyweight': float(user_weight),
            'exercise': self.variation.variation_name,
            'is_a_challenge': self.is_a_challenge,
            'user': self.user.id
        }