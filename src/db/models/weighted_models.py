from ...extensions import db

class WeightedExercise(db.Model):
    __tablename__ = 'weighted_exercises'

    id = db.Column(db.Integer(), primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    variations = db.relationship('WeightedExerciseVariations', backref='weight_exercise', lazy=True)

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

    weight_records = db.relationship('WeightRecord', backref='variation')

    def serialize(self):
        return {
            'id': self.id,
            'variation_name': self.variation_name,
            'exercise_id': self.exercise_id
        }

class WeightRecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lifted_weight = db.Column(db.Numeric(5, 2), nullable=False)
    date = db.Column(db.Date(), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    variation_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise_variations.id'), nullable=False)

    user = db.relationship('Users', backref=db.backref('weight_records', lazy=True))
    bodyweight = db.Column(db.Numeric(5, 2), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'weight': self.lifted_weight,
            'date': self.date.strftime('%d/%m/%Y'),
            'user_weight': float(self.bodyweight)
        }