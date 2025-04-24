from ...extensions import db

class Follow(db.Model):
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)
    following_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)

    follower = db.relationship('Users', foreign_keys=[user_id], backref='following')
    followed = db.relationship('Users', foreign_keys=[following_id], backref='followers')

    def serialize(self):
        return {
            'user_id': self.user_id,
            'following_id': self.following_id
        }

