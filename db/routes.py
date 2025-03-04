from flask import Blueprint, request, jsonify
from models import db, Users, WeightedExercises, WeightedExerciseVariations, WeightRecord, UserExercise
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

api = Blueprint('api', __name__)

@api.route('/register', methods=['POST'])
def signup():
    response_body = {}
    data = request.json

    email = data.get('email', None).lower()
    password = data.get('password', None)
    name = data.get('name', "")
    name = name.tolower() if name else ""
    last_name = data.get('last_name', "")
    last_name = last_name.tolower() if last_name else ""
    username = data.get('username', None)

    existing_email = Users.query.filter_by(email=email).firts()
    existing_username = Users.query.filter_by(username=username).firts()

    if existing_email or existing_username:
        if existing_email:
            response_body['error'] = f'An account is already using {email}'
        elif existing_username:
            response_body['error'] = f'An account is already using {username}'
        return jsonify(response_body), 400

    new_user = Users(
        email = email,
        password = password,
        is_premium = False,
        name =  name,
        last_name = last_name,
        username = username
    )

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity={'user_id': new_user.id})
    response_body['message'] = 'User created'
    response_body['token'] = access_token

    return jsonify(response_body)

@api.route('/login', methods=['POST'])
def login():
    response_body = {}
    data = request.json
    email = data.get('email', None)
    password = data.get('password', None)
    user = Users.query.filter_by(email=email, password=password).first()

    if user:
        access_token = create_access_token(identity={'user_id': user.id})
        response_body['message'] = 'User logged in'
        response_body['access_token'] = access_token
        response_body['user_data'] = user.serialize()
        return jsonify(response_body), 200
    else:
        response_body['message'] = 'User or password invalid'
        return jsonify(response_body), 401

