from flask import Blueprint, request, jsonify
from src.db.models.calisthenic_models import CalisthenicExercises
from src.db.models.weighted_models import WeightedExercise
from src.db.models.cardio_models import CardioExercise
from flask_jwt_extended import create_access_token
from flask_cors import CORS
from ...extensions import db


exercises_api = Blueprint('exercises_api', __name__)

CORS(exercises_api)

@exercises_api.route('/exercises', methods=["GET"])
def get_all_exercises():

    weighted_exercises = WeightedExercise.query.all()
    calisthenic_exercises = CalisthenicExercises.query.all()
    cardio_exercises = CardioExercise.query.all()

    exercises = {
        'weighted': [exercise.serialize() for exercise in weighted_exercises],
        'calisthenic': [exercise.serialize() for exercise in calisthenic_exercises],
        'cardio': [exercise.serialize() for exercise in cardio_exercises]
    }

    return jsonify(exercises)

@exercises_api.route('/exercises/weighted', methods=["POST"])
def add_weighted_exercise():

    data = request.json

    new_exercise = WeightedExercise(exercise_name=data["exercise_name"])

    db.session.add(new_exercise)
    db.session.commit()
    return jsonify(new_exercise.serialize()), 201

@exercises_api.route('/exercises/calisthenic', methods=["POST"])
def add_calisthenic_exercise():

    data = request.json

    new_exercise = CalisthenicExercises(exercise_name=data["exercise_name"])

    db.session.add(new_exercise)
    db.session.commit()
    return jsonify(new_exercise.serialize()), 201

@exercises_api.route('/exercises/cardio', methods=["POST"])
def add_cardio_exercise():

    data = request.json

    new_exercise = CardioExercise(exercise_name=data["exercise_name"])

    db.session.add(new_exercise)
    db.session.commit()
    return jsonify(new_exercise.serialize()), 201