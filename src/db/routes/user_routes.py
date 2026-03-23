from flask import Blueprint, request, jsonify
from src.db.models.user_models import Users
from src.db.models.user_follows_models import Follow
from flask_cors import CORS
from src.extensions import db, validate_existence, validate_user_access
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash

user_api = Blueprint('user_api', __name__)

CORS(user_api)

@user_api.route('/users', methods=['GET'])
def get_users():
    response_body = {}
    users = Users.query.all()
    results = [user.serialize() for user in users]
    response_body["message"] = "List of users"
    response_body["results"] = results
    return jsonify(response_body), 200

@user_api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    response_body= {}
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")
    
    response_body["message"] = 'User found'
    response_body["results"] = user.serialize()
    return jsonify(response_body), 200

@user_api.route('/users/<int:user_id>', methods=["PUT"])
@jwt_required()
def edit_user(user_id):
    validate_user_access(user_id)
    response_body = {}
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")
    data = request.json 
    validate_existence(data, "data")

    
    fields = ['email', 'password', 'name', 'last_name', 'username', 'weight']
    changed_fields = []

    for field in fields:
        new_value = data.get(field)
        if new_value is not None and new_value != getattr(user, field):
            if field == "password":
                new_value = generate_password_hash(new_value)
            setattr(user, field, new_value)
            changed_fields.append(field)            

    db.session.commit()
    response_body["message"] = "Data updated"
    response_body["results"] = user.serialize()
    response_body["changed_fields"] = changed_fields
    return jsonify(response_body), 200

@user_api.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    validate_user_access(user_id)
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")
    response_body = {}
  
    Follow.query.filter_by(user_id=user_id).delete()
    Follow.query.filter_by(following_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    response_body['message'] = f"The user {user.name} has been deleted"
    return jsonify(response_body), 200

