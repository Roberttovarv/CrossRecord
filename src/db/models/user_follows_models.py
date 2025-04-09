from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Follow(db.Model):
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)
    following_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)

    user_from = db.relationship('Users', foreign_keys=[user_id], backref='following_relations')
    user_to = db.relationship('Users', foreign_keys=[following_id], backref='follower_relations')

    def serialize(self):
        return {
            'user_id': self.user_id,
            'following_id': self.following_id
        }

