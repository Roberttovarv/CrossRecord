from flask import Blueprint, request, jsonify
from src.db.models.user_models import Users
from flask_jwt_extended import create_access_token
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

auth_api = Blueprint('auth_api', __name__)

CORS(auth_api)

@auth_api.route('/register', methods=['POST'])
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

@auth_api.route('/login', methods=['POST'])
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