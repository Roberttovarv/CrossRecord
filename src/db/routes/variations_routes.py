from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_cors import CORS
from models import (db, WeightedExercises, WeightedExerciseVariations)

variations_api = Blueprint('variations_api', __name__)

CORS(variations_api)

@variations_api.route('/exercises/weighted/<int:exercise_id>/variations', methods=["GET"])
def get_all_weighted_variations(exercise_id):
    
    exercise = WeightedExercises.query.get(exercise_id)
    
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404
    
    return jsonify({
        'exercise': exercise.exercise_name,
        'variations': [variation.serialize() for variation in exercise.variations]
    }), 200

@variations_api.route('/exercises/weighted/<int:exercise_id>/variations', methods=["POST"])
def add_weighted_variation(exercise_id):
    
    data = request.json

    exercise = WeightedExercises.query.get(exercise_id)
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404

    new_variation = WeightedExerciseVariations(
        variation_name=data["variation_name"],
        exercise_id= exercise_id 
    )

    db.session.add(new_variation)
    db.session.commit()

    return jsonify({new_variation.serialize()})

@variations_api.route('/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>',
                      methods=["GET"])
def get_single_weighted_variation(exercise_id, variation_id):

    exercise = WeightedExercises.query.get(exercise_id)
    
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404
    
    variation_to_get = next((variation for variation in exercise.variations if variation.id == variation_id), None)
    
    if not variation_to_get:
        return jsonify({'error': 'No variation was found with that ID'}), 404

    return jsonify(variation_to_get.serialize()), 200

@variations_api.route('/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>',
                      methods=["DELETE"])
def delete_weighted_variation(exercise_id, variation_id):

    exercise = WeightedExercises.query.get(exercise_id)

    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404

    variation_to_delete = next((variation for variation in exercise.variations if variation.id == variation_id))

    if not variation_to_delete:
        return jsonify({'error': 'No variation was found with that ID'}), 404
    
    db.session.delete(variation_to_delete)
    db.session.commit()

    return jsonify({'message': 'Variation deleted successfully'}), 200


