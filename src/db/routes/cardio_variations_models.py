from flask import Blueprint, request, jsonify
from flask_cors import CORS
from models import db, CardioExercises, CardioExerciseVariations

cardio_variations_api = Blueprint('cardio_variations_api', __name__)

CORS(cardio_variations_api)

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations',
                             methods=["GET"])
def get_all_cardio_variations(exercise_id):
    
    exercise = CardioExercises.query.get(exercise_id)
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404

    return jsonify({
        'exercise': exercise.exercise_name,
        'variations': [variation.serialize() for variation in exercise.variations]
    }), 200

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations',
                             methods=["POST"])
def add_cardio_variation(exercise_id):
    
    data = request.json
    if not data:
        return jsonify({'error': 'Data must not be empty'})

    if ('variation_name' in data and
        not data['variation_name'].strip() or
        not isinstance(data["variation_name"], str)
    ):
        return jsonify({'error': 'Variation name cannot be empty or just spaces'}), 400
    
    if len(data["variation_name"]) < 5 or len(data["variation_name"]) > 40:
        return jsonify({'error': 'variation_name must be from 5 to 40 characters'})
    
    exercise = CardioExercises.query.get(exercise_id)
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404
    if any(variation.variation_name.lower() == data["variation_name"].strip().lower()
           for variation in exercise.variations):
        return jsonify({'error': 'Variation with this name already exists'})
    
    new_variation = CardioExerciseVariations(
        variation_name=data["variation_name"],
        exercise_id=exercise_id
    )

    db.session.add(new_variation)
    db.session.commit()

    return jsonify(new_variation.serialize()), 201
