from flask import Blueprint, request, jsonify
from src.db.models.user_models import Users
from src.db.models.user_follows_models import Follow
from flask_cors import CORS
from ...extensions import db
from flask_jwt_extended import jwt_required


user_api = Blueprint('user_api', __name__)

CORS(user_api)

@user_api.route('/users', methods=['GET'])
def get_users():
    response_body = {}
    users = Users.query.all()
    results = [user.serialize() for user in users]
    response_body['message'] = "List of users"
    response_body['results'] = results
    return jsonify(response_body), 200

@user_api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    response_body= {}
    user = Users.query.get(user_id)

    if not user:
        return jsonify({'message': 'Invalid user'}), 404
    
    response_body['message'] = 'User found'
    response_body['results'] = user.serialize()
    return jsonify(response_body), 200

@user_api.route('/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    response_body = {}
    user = Users.query.get(user_id)
    data = request.json 
    
    if not user:
        return jsonify({'message': 'Invalid user'}), 404
    
    fields = ['email', 'password', 'name', 'last_name', 'username', 'weight']
    changed_fields = []

    for field in fields:
        if data[field] and data[field] != getattr(user, field):
            setattr(user, field, data[field])
            changed_fields.append(field)            

    db.session.commit()
    response_body['message'] = "Data updated"
    response_body['results'] = user.serialize()
    response_body['changed_fields'] = changed_fields
    return jsonify(response_body), 200

@user_api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = Users.query.get(user_id)
    response_body = {}

    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    Follow.query.filter_by(user_id=user_id).delete()
    Follow.query.filter_by(following_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    response_body['message'] = f"The user {user.name} has been deleted"
    return jsonify(response_body), 200

