from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, abort

db = SQLAlchemy()

def validate_existence(param, name: str="property"):
    if not param:
        response = jsonify({'error':f'{name} is required to proceed'})
        response.status_code = 400
        abort(response)

def validate_is_not_blank(param: str):
    if not param or not isinstance(param, str) or not param.strip():
        response = jsonify({'error':'variation_name cannot be empty, null or just spaces'})
        response.status_code = 400
        abort(response)

def validate_length(param: str):
    if len(param) < 5 or len(param) > 40:
        return jsonify({'error': 'variation_name must be from 5 to 40 characters'})

def validate_variation_not_repeated(exercise, variation_name: str):
    if any(variation.variation_name.lower() == variation_name.strip().lower()
           for variation in exercise.variations):
        response = jsonify({'error': 'Variation with this name already exists'})
        response.status_code = 400
        abort(response)