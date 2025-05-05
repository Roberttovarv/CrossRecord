from src.extensions import db

class Follow(db.Model):
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)
    following_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)

    user_that_follows = db.relationship('Users', foreign_keys=[user_id], backref='following')
    followed_user = db.relationship('Users', foreign_keys=[following_id], backref='followers')

    def serialize(self):
        return {
            'follower_user': self.user_that_follows.username,
            'following_user': self.followed_user.username
            }

