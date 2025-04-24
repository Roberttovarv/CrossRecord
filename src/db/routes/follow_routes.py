from flask import Blueprint, request, jsonify
from src.db.models.user_models import Users
from src.db.models.user_follows_models import Follow
from flask_cors import CORS
from ...extensions import db

follow_api = Blueprint('follow_api', __name__)

CORS(follow_api)

@follow_api.route('/users/<int:user_id>/following', methods=["GET"])
def get_user_following(user_id):

    user = Users.query.get(user_id)
    following = user.following

    return jsonify(following), 200

@follow_api.route('/users/<int:user_id>/followers', methods=["GET"])
def get_user_followers(user_id):
    
    user = Users.query.get(user_id)
    followers = user.followers

    return jsonify(followers), 200

@follow_api.route('/users/<int:user_id>/following', methods=["POST"])
def add_new_follow(user_id):

    data = request.json
    user_to_follow = data.get("user_to_follow")

    if user_to_follow is None:
        return jsonify({'error': 'Missing user_to_follow'}), 400
    
    user = Users.query.get(user_id)
    new_follow = Users.query.get(user_to_follow)

    if not user or not new_follow:
        return jsonify({'error':'User not found'}), 404
    
    existing_follow = Follow.query.filter_by(user_id=user_id, following_id=user_to_follow).first()
    if existing_follow:
        return jsonify({'message':'Already following'}), 400
    if user_id == user_to_follow:
        return jsonify("'error': 'User ID is same than User to Follow'")
    
    follow = Follow(
        user_id=user_id,
        following_id=user_to_follow
    )

    db.session.add(follow)
    db.session.commit()

    return jsonify(follow.serialize())

@follow_api.route('/users/<int:user_id>/following/<int:following_id>', methods=["DELETE"])
def remove_follow(user_id, following_id):
    
    follow = Follow.query.filter_by(user_id=user_id, following_id=following_id).first()

    if follow:
        db.session.delete(follow),
        db.session.commit()

        return jsonify({'message':'Follow deleted'}), 200

    return jsonify({'Error':'Follow not found'}), 404

@follow_api.route('/users/<int:user_id>/followers/<int:follower_id>', methods=["DELETE"])
def remove_follower(user_id, follower_id):

    follow = Follow.query.filter_by(user_id=follower_id, following_id=user_id).first()

    if follow:
        db.session.delete(follow)
        db.session.commit()

        return jsonify({'message':'Follower deleted'})
    
    return jsonify({'error':'Follower not found'}), 404 