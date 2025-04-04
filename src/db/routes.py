from flask import Blueprint, request, jsonify
from models import db, Users, WeightedExercises, WeightedExerciseVariations, WeightRecord, UserExercise
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_cors import CORS

api = Blueprint('api', __name__)

CORS(api)

@api.route('/register', methods=['POST'])
def signup():
    response_body = {}
    data = request.json

    required_fields = ['email', 'password', 'name', 'last_name', 'username']

    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"the field '{field}' is required"}), 400

    email = data["email"].lower()
    password = data["password"]
    name = data["name"].lower()
    last_name = data["last_name"].lower()
    username = data["username"].lower()
    weight = data["weight"]

    existing_email = Users.query.filter_by(email=email).first()
    existing_username = Users.query.filter_by(username=username).first()

    if existing_email or existing_username:
        if existing_email:
            response_body['error'] = f"An account is already using {email}"
        elif existing_username:
            response_body['error'] = f"An account is already using {username}"
        return jsonify(response_body), 400

    new_user = Users(
        email = email,
        password = password, # Hashear password
        is_premium = False,
        name =  name,
        last_name = last_name,
        username = username,
        weight = weight

    )

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity={'user_id': new_user.id})
    response_body['message'] = 'User created'
    response_body['token'] = access_token

    return jsonify(response_body), 201

@api.route('/login', methods=['POST'])
def login():
    response_body = {}
    data = request.json
    email = data["email"]
    password = data["password"]
    user = Users.query.filter_by(email=email, password=password).first()

    if user:
        access_token = create_access_token(identity={'user_id': user.id})
        response_body['message'] = 'User logged in'
        response_body['access_token'] = access_token
        response_body['user_data'] = user.serialize()
        return jsonify(response_body), 200
    else:
        response_body['message'] = 'Invalid user or password'
        return jsonify(response_body), 401

@api.route('/users', methods=['GET'])
def get_users():
    response_body = {}
    users = Users.query.all()
    results = [user.serialize() for user in users]
    response_body['message'] = "List of users"
    response_body['results'] = results
    return jsonify(response_body), 200

@api.route('users/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    response_body= {}
    user = Users.query.get(user_id)

    if not user:
        return jsonify({'message': 'Invalid user'}), 404
    
    response_body['message'] = 'User found'
    response_body['results'] = user.serialize()
    return jsonify(response_body), 200

@api.route('users/user/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    response_body = {}
    user = Users.query.get(user_id)
    data = request.json 
    
    if not user:
        return jsonify({'message': 'Invalid user'}), 404
    
    fields = ['email', 'password', 'name', 'last_name', 'username', 'weight']

    for field in fields:
        if data[field]:
            user.field = data[field]

    db.session.commit()
    response_body['message'] = "Data updated"
    response_body['results'] = user.serialize()
    return jsonify(response_body), 200

@api.route('users/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = Users.query.get(user_id)
    response_body = {}

    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    response_body['message'] = f"The user {user.name} has been deleted"
    return jsonify(response_body), 200