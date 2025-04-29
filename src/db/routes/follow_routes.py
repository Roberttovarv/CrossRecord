from flask import Blueprint, request, jsonify
from src.db.models.user_models import Users
from src.db.models.user_follows_models import Follow
from flask_cors import CORS
from ...extensions import db, validate_existence

follow_api = Blueprint('follow_api', __name__)

CORS(follow_api)

@follow_api.route('/users/<int:user_id>/following', methods=["GET"])
def get_user_following(user_id):

    user = Users.query.get(user_id)
    validate_existence(user, "user")
    following = [follow.serialize() for follow in user.following]

    return jsonify(following), 200

@follow_api.route('/users/<int:user_id>/followers', methods=["GET"])
def get_user_followers(user_id):
    
    user = Users.query.get(user_id)
    validate_existence(user, "user")
    followers = [follower.serialize() for follower in user.followers]

    return jsonify(followers), 200

@follow_api.route('/users/<int:user_id>/following', methods=["POST"])
def add_new_follow(user_id):

    data = request.json
    validate_existence(data.get("user_to_follow"), "user_to_follow")
    user_to_follow = data["user_to_follow"]
 
    user = Users.query.get(user_id)
    validate_existence(user, "user")
    new_follow = Users.query.get(user_to_follow)
    validate_existence(new_follow, "new_follow")
    
    existing_follow = Follow.query.filter_by(user_id=user_id, following_id=user_to_follow).first()
    if existing_follow:
        return jsonify({'message':'Already following'}), 400
    if user_id == user_to_follow:
        return jsonify({'error': 'User ID is same than User to Follow'}), 400
    
    follow = Follow(
        user_id=user_id,
        following_id=user_to_follow
    )

    db.session.add(follow)
    db.session.commit()

    return jsonify(follow.serialize()), 201

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