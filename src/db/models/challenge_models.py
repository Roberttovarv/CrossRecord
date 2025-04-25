from ...extensions import db

class CardioChallenge(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_id = db.Column(db.Integer, db.ForeignKey('cardio_exercise_variations.id'), nullable=False)
    challenger_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    challenged_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    record_to_complete = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.String(50), nullable=True)
    date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean(), nullable=False)

    challenger = db.relationship('Users', foreign_keys=[challenger_id], backref='sent_challenges')
    challenged = db.relationship('Users', foreign_keys=[challenged_id], backref='received_challenges')
    cardio_variation = db.relationship('CardioExerciseVariations')
    
    def serialize(self):
        return {
            'id': self.id,
            'exercise': self.cardio_variation.variation_name,
            'challenger': self.challenger.username,
            'challenged': self.challenged.username,
            'record_to_complete': self.record_to_complete,
            'message': self.message,
            'date': self.date.strftime("%d/%m/%Y"),
            'is_completed': self.is_completed
        }

class CalisthenicChallenge(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_id = db.Column(db.Integer(), db.ForeignKey('calisthenic_exercise_variations.id'), nullable=False)
    challenger_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    challenged_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    record_to_complete = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean(), nullable=False)

    challenger = db.relationship('Users', foreign_keys=[challenger_id], backref='sent_challenges')
    challenged = db.relationship('Users', foreign_keys=[challenged_id], backref='receivde_challenges')
    calisthenic_variation = db.relationship('CalisthenicExerciseVariations')

    def serialize(self):
        return {
            'id': self.id,
            'exercise': self.calisthenic_variation.variation_name,
            'challenger': self.challenger.username,
            'challenged': self.challenged.username,
            'record_to_complete': self.record_to_complete,
            'message': self.message,
            'date': self.date.strftime("%d/%m/%Y"),
            'is_completed': self.is_completed
        }
    
class WeightedChallenge(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variation_id = db.Column(db.Integer(), db.ForeignKey('weighted_exercise_variations.id'), nullable=False)
    challenger_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    challenged_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    record_to_complete = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean(), nullable=False)

    challenger = db.relationship('Users', foreign_keys=[challenger_id], backref='sent_challenges')
    challenged = db.relationship('Users', foreign_keys=[challenged_id], backref='receivde_challenges')
    weighted_variation = db.relationship('WeightedExerciseVariations')

    def serialize(self):
        return {
            'id': self.id,
            'exercise': self.weighted_variation.variation_name,
            'challenger': self.challenger.username,
            'challenged': self.challenged.username,
            'record_to_complete': self.record_to_complete,
            'message': self.message,
            'date': self.date.strftime("%d/%m/%Y"),
            'is_completed': self.is_completed
        }