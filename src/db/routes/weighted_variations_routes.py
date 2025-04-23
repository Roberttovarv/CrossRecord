from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.weighted_models import WeightedExercise, WeightedExerciseVariations
from ...extensions import db


weighted_variations_api = Blueprint('weighted_variations_api', __name__)

CORS(weighted_variations_api)

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations',
                               methods=["GET"])
def get_all_weighted_variations(exercise_id):
    
    exercise = WeightedExercise.query.get(exercise_id)    
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404
    
    return jsonify({
        'exercise': exercise.exercise_name,
        'variations': [variation.serialize() for variation in exercise.variations]
    }), 200

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations',
                               methods=["POST"])
def add_weighted_variation(exercise_id):
    
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
    
    exercise = WeightedExercise.query.get(exercise_id)
    if not exercise:
        return jsonify({'error': 'No exercise was found with that ID'}), 404
    if any(variation.variation_name.lower() == data["variation_name"].strip().lower()
           for variation in exercise.variations):
        return jsonify({'error': 'Variation with this name already exists'})
    
    new_variation = WeightedExerciseVariations(
        variation_name=data["variation_name"],
        exercise_id=exercise_id 
    )

    db.session.add(new_variation)
    db.session.commit()

    return jsonify(new_variation.serialize()), 201

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>',
                      methods=["GET"])
def get_single_weighted_variation(exercise_id, variation_id):
    
    variation_to_get = WeightedExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first() 
    if not variation_to_get:
        return jsonify({'error': 'No variation was found with that ID'}), 404

    return jsonify(variation_to_get.serialize()), 200

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations/<int:varition_id>',
                               methods=["PUT"])
def edit_weighted_variation(exercise_id, variation_id):

    variation_to_edit = WeightedExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first() 
    if not variation_to_edit:
       return jsonify({'error': 'No variation was found with that ID'}), 404
    
    exercise = WeightedExercise.query.get(exercise_id)
    data = request.json
    if not data:
        jsonify({'error': 'Data must not be empty'})
    
    if ('variation_name' in data and
        not data['variation_name'].strip() or
        not isinstance(data["variation_name"], str)
    ):
        return jsonify({'error': 'Variation name cannot be empty or just spaces'}), 400
    
    if len(data["variation_name"]) < 5 or len(data["variation_name"]) > 40:
        return jsonify({'error': 'variation_name must be from 5 to 40 characters'})
    
    if any(variation.variation_name.lower() == data["variation_name"].strip().lower()
           for variation in exercise.variations):
        return jsonify({'error': 'Variation with this name already exists'})
    
    variation_to_edit.variation_name = data.get('variation_name',
                                                variation_to_edit.variation_name).strip().lower()

    db.session.commit()
    return jsonify({
        'message': 'Variation edited successfully',
        'variation': variation_to_edit.serialize()
    }), 200

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>',
                      methods=["DELETE"])
def delete_weighted_variation(exercise_id, variation_id):

    variation_to_delete = WeightedExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first() 
    if not variation_to_delete:
        return jsonify({'error': 'No variation was found with that ID'}), 404
    
    db.session.delete(variation_to_delete)
    db.session.commit()

    return jsonify({'message': 'Variation deleted successfully'}), 200