from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.weighted_models import WeightedExercise, WeightedExerciseVariations
from ...extensions import db, validate_existence, validate_is_not_blank, validate_length, validate_variation_not_repeated

weighted_variations_api = Blueprint('weighted_variations_api', __name__)

CORS(weighted_variations_api)

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations',
                               methods=["GET"])
def get_all_weighted_variations(exercise_id):
    
    exercise = WeightedExercise.query.get(exercise_id)    
    validate_existence(exercise, "exercise")
    
    return jsonify({
        'exercise': exercise.exercise_name,
        'variations': [variation.serialize() for variation in exercise.variations]
    }), 200

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations',
                               methods=["POST"])
def add_weighted_variation(exercise_id):
    
    data = request.json
    validate_existence(data, "data")
    validate_is_not_blank(data.get('variation_name'))
    validate_length(data.get('variation_name'))
    
    exercise = WeightedExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")
    validate_variation_not_repeated(exercise, data.get('variation_name'))
    
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
    validate_existence(variation_to_get, "variation_to_get")

    return jsonify(variation_to_get.serialize()), 200

@weighted_variations_api.route('/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>',
                               methods=["PUT"])
def edit_weighted_variation(exercise_id, variation_id):

    variation_to_edit = WeightedExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first() 
    validate_existence(variation_to_edit, "variation_to_edit")
    
    exercise = WeightedExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")
    data = request.json
    validate_existence(data, "data")
    validate_is_not_blank(data.get('variation_name'))
    validate_length(data.get('variation_name'))
    validate_variation_not_repeated(exercise, data.get('variation_name'))
    
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
    validate_existence(variation_to_delete, "variation_to_delete")
    
    db.session.delete(variation_to_delete)
    db.session.commit()

    return jsonify({'message': 'Variation deleted successfully'}), 200