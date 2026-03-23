from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, abort
from flask_jwt_extended import get_jwt_identity

db = SQLAlchemy()

def validate_existence(param, name: str="property"):
    if not param:
        response = jsonify({'error':f'{name} not found.'})
        response.status_code = 400
        abort(response)

def validate_is_not_blank(param: str):
    if not param or not isinstance(param, str) or not param.strip():
        response = jsonify({'error':'variation_name cannot be empty, null or just spaces'})
        response.status_code = 400
        abort(response)

def validate_length(param: str):
    if len(param) < 5 or len(param) > 40:
        response = jsonify({'error': 'value must be from 5 to 40 characters'})
        response.status_code = 400
        abort(response)

def validate_variation_not_repeated(exercise, variation_name: str):
    if any(variation.variation_name.lower() == variation_name.strip().lower()
           for variation in exercise.variations):
        response = jsonify({'error': 'Variation with this name already exists'})
        response.status_code = 400
        abort(response)

def validate_user_access(user_id: int):
    identity = get_jwt_identity()
    token_user_id = identity.get("user_id") if isinstance(identity, dict) else identity

    if token_user_id != user_id:
        response = jsonify({'error': 'You are not authorized to access this resource'})
        response.status_code = 403
        abort(response)
