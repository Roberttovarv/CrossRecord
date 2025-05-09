from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.cardio_models import CardioExercise, CardioExerciseVariations
from src.extensions import db, validate_existence, validate_is_not_blank, validate_length, validate_variation_not_repeated


cardio_variations_api = Blueprint('cardio_variations_api', __name__)

CORS(cardio_variations_api)

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations',
                             methods=["GET"])
def get_all_cardio_variations(exercise_id):
    
    exercise = CardioExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")

    return jsonify({
        'exercise': exercise.exercise_name,
        'variations': [variation.serialize() for variation in exercise.variations]
    }), 200

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations',
                             methods=["POST"])
def add_cardio_variation(exercise_id):
    
    data = request.json
    validate_existence(data.get("variation_name"), "variation_name")
    validate_is_not_blank(data["variation_name"])
    validate_length(data["variation_name"])
    
    exercise = CardioExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")
    validate_variation_not_repeated(exercise, data["variation_name"])
    
    new_variation = CardioExerciseVariations(
        variation_name=data["variation_name"],
        exercise_id=exercise_id
    )

    db.session.add(new_variation)
    db.session.commit()

    return jsonify(new_variation.serialize()), 201

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations/<int:variation_id>',
                             methods=["GET"])
def get_single_cardio_variation(exercise_id, variation_id):

    variation_to_get = CardioExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation_to_get, "variation_to_get")
    
    return jsonify(variation_to_get.serialize()), 200

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations/<int:variation_id>',
                             methods=["PUT"])
def edit_cardio_variation(exercise_id, variation_id):

    variation_to_edit = CardioExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation_to_edit, "variation_to_edit")

    exercise = CardioExercise.query.get(exercise_id)
    validate_existence(exercise, "exercise")
    data = request.json
    validate_existence(data.get("variation_name"), "variation_name")
    validate_is_not_blank(data["variation_name"])
    validate_length(data["variation_name"])
    validate_variation_not_repeated(exercise, data["variation_name"])
    
    variation_to_edit.variation_name = data.get('variation_name',
                                                variation_to_edit.variation_name).strip().lower()

    db.session.commit()
    return jsonify({
        'message': 'Variation edited successfully',
        'variation': variation_to_edit.serialize()
    }), 200    

@cardio_variations_api.route('/exercises/cardio/<int:exercise_id>/variations/<int:variation_id>',
                             methods=["DELETE"])
def delete_cardio_variation(exercise_id, variation_id):

    variation_to_delete = CardioExerciseVariations.query.filter_by(
        variation_id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation_to_delete, "variation_to_delete")
    
    db.session.delete(variation_to_delete)
    db.session.commit()

    return jsonify({'message': 'Variation deleted successfully'}), 200  