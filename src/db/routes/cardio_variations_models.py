from flask import Blueprint, request, jsonify
from flask_cors import CORS
from models import db, CardioExercises, CardioExerciseVariations

cardio_variations_api = Blueprint('cardio_variations_api', __name__)

CORS(cardio_variations_api)

@cardio_variations_api.route('/exercises/calisthenic/<int:exercise_id>/variations',
                             methods=["GET"])
def get_all_cardio_variations(exercise_id):
    pass