from flask import Blueprint, request, jsonify
from src.db.models.calisthenic_models import CalisthenicExercises 
from src.db.models.weighted_models import WeightedExercise 
from src.db.models.cardio_models import CardioExercise 
from flask_cors import CORS
from src.extensions import db, validate_existence, validate_is_not_blank, validate_length 


exercises_api = Blueprint('exercises_api', __name__)

CORS(exercises_api)

@exercises_api.route('/exercises', methods=["GET"])
def get_all_exercises():

    weighted_exercises = WeightedExercise.query.all()
    calisthenic_exercises = CalisthenicExercises.query.all()
    cardio_exercises = CardioExercise.query.all()
    validate_existence(weighted_exercises, "weighted_exercises")
    validate_existence(calisthenic_exercises, "calisthenic_exercises")
    validate_existence(cardio_exercises, "cardio_exercises")

    exercises = {
        'weighted': [exercise.serialize() for exercise in weighted_exercises],
        'calisthenic': [exercise.serialize() for exercise in calisthenic_exercises],
        'cardio': [exercise.serialize() for exercise in cardio_exercises]
    }

    return jsonify(exercises)

@exercises_api.route('/exercises/weighted', methods=["GET"])
def get_all_weighted_exercises():
    exercises = WeightedExercise.query.all()
    validate_existence(exercises, "exercise")

    return jsonify(exercises.serialize()), 200

@exercises_api.route('/exercises/weighted', methods=["POST"])
def add_weighted_exercise():

    data = request.json
    validate_existence(data.get("exercise_name"))
    validate_length(data["exercise_name"])
    validate_is_not_blank(data["exercise_name"])

    new_exercise = WeightedExercise(exercise_name=data["exercise_name"])

    db.session.add(new_exercise)
    db.session.commit()
    return jsonify(new_exercise.serialize()), 201

@exercises_api.route('/exercises/weighted/<int:exercise_id>', methods=["GET"])
def get_weighted_exercise(exercise_id):
    exercise = WeightedExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")

    return jsonify(exercise.serialize()), 200

@exercises_api.route('/exercises/weighted/<int:exercise_id>', methods=["DELETE"])
def delete_weighted_exercise(exercise_id):
    exercise_to_delete = WeightedExercise.query.get(exercise_id)
    validate_existence(exercise_to_delete, "exercise_to_delete")

    db.session.delete(exercise_to_delete)
    db.session.commit()

    return jsonify('message: exercise deleted successfully')

@exercises_api.route('/exercises/calisthenic', methods=["GET"])
def get_all_calisthenic_exercises():
    exercises = CalisthenicExercises.query.all()
    validate_existence(exercises, "exercise")

    return jsonify(exercises.serialize()), 200

@exercises_api.route('/exercises/calisthenic', methods=["POST"])
def add_calisthenic_exercise():

    data = request.json
    validate_existence(data.get("exercise_name"))
    validate_length(data["exercise_name"])
    validate_is_not_blank(data["exercise_name"])

    new_exercise = CalisthenicExercises(exercise_name=data["exercise_name"])

    db.session.add(new_exercise)
    db.session.commit()
    return jsonify(new_exercise.serialize()), 201

@exercises_api.route('/exercises/calisthenic/<int:exercise_id>', methods=["GET"])
def get_calisthenic_exercise(exercise_id):
    exercise = CalisthenicExercises.query.get(exercise_id)
    validate_existence(exercise, "exercise")

    return jsonify(exercise.serialize()), 200

@exercises_api.route('/exercises/calisthenic/<int:exercise_id>', methods=["DELETE"])
def delete_calisthenic_exercise(exercise_id):
    exercise_to_delete = CalisthenicExercises.query.get(exercise_id)
    validate_existence(exercise_to_delete, "exercise_to_delete")

    db.session.delete(exercise_to_delete)
    db.session.commit()

    return jsonify('message: exercise deleted successfully')

@exercises_api.route('/exercises/cardio', methods=["GET"])
def get_all_cardio_exercises():
    exercises = CardioExercise.query.all()
    validate_existence(exercises, "exercise")

    return jsonify(exercises.serialize()), 200

@exercises_api.route('/exercises/cardio', methods=["POST"])
def add_cardio_exercise():

    data = request.json
    validate_existence(data.get("exercise_name"))
    validate_length(data["exercise_name"])
    validate_is_not_blank(data["exercise_name"])

    new_exercise = CardioExercise(exercise_name=data["exercise_name"])

    db.session.add(new_exercise)
    db.session.commit()
    return jsonify(new_exercise.serialize()), 201

@exercises_api.route('/exercises/cardio/<int:exercise_id>', methods=["GET"])
def get_cardio_exercise(exercise_id):
    exercise = CardioExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")

    return jsonify(exercise.serialize()), 200

@exercises_api.route('/exercises/cardio/<int:exercise_id>', methods=["DELETE"])
def delete_cardio_exercise(exercise_id):
    exercise_to_delete = CardioExercise.query.get(exercise_id)
    validate_existence(exercise_to_delete, "exercise_to_delete")

    db.session.delete(exercise_to_delete)
    db.session.commit()

    return jsonify('message: exercise deleted successfully')