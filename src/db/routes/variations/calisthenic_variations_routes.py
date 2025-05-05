from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.calisthenic_models import CalisthenicExercises, CalisthenicExerciseVariations
from src.extensions import db, validate_is_not_blank, validate_existence, validate_length, validate_variation_not_repeated


calisthenic_variations_api = Blueprint('calisthenic_variations_api', __name__)

CORS(calisthenic_variations_api)

@calisthenic_variations_api.route('/exercises/calisthenic/<int:exercise_id>/variations',
                                  methods=["GET"])
def get_all_calisthenic_variations(exercise_id):
    
    exercise = CalisthenicExercises.query.get(exercise_id)
    validate_existence(exercise, "exercise")

    return jsonify({
        'exercise': exercise.exercise_name,
        'variations': [variation.serialize() for variation in exercise.variations]
    }), 200

@calisthenic_variations_api.route('/exercises/calisthenic/<int:exercise_id>/variations',
                                  methods=["POST"])
def add_calisthenic_variation(exercise_id):

    data = request.json
    validate_existence(data.get("variation_name"), "variation_name")
    validate_is_not_blank(data["variation_name"])
    validate_length(data["variation_name"])
    
    exercise = CalisthenicExercises.query.get(exercise_id)
    validate_existence(exercise, "exercise")
    validate_variation_not_repeated(exercise, data["variation_name"])
       
    new_variation = CalisthenicExerciseVariations(
        variation_name = data["variation_name"].lower().strip(),
        exercise_id=exercise_id
    )

    db.session.add(new_variation)
    db.session.commit()

    return jsonify(new_variation.serialize()), 201

@calisthenic_variations_api.route('/exercises/calisthenic/<int:exercise_id>/variation/<int:variation_id>',
                                  methods=["GET"])
def get_single_calisthenic_variation(exercise_id, variation_id):
    
    variation_to_get = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation_to_get, "variation_to_get")
    
    return jsonify(variation_to_get.serialize())

@calisthenic_variations_api.route('/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>',
                                  methods=["PUT"])
def edit_calisthenic_variation(exercise_id, variation_id):

    variation_to_edit = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation_to_edit, "variation_to_edit")

    exercise = CalisthenicExercises.query.get(exercise_id)
    validate_existence(exercise, "exercise")
    data = request.json
    validate_existence(data.get("variation_name"))
    validate_is_not_blank(data["variation_name"])
    validate_length(data["variation_name"])
    validate_variation_not_repeated(exercise, data["variation_name"])
         
    variation_to_edit.variation_name = data.get('variation_name',
                                                variation_to_edit.variation_name).lower().strip()
    
    db.session.commit()
    return jsonify({
        'message': 'Variation edited successfully',
        'variation': variation_to_edit.serialize()
    }), 200

@calisthenic_variations_api.route('/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>',
                                  methods=["DELETE"])
def delete_calisthenic_variation(exercise_id, variation_id):
    
    variation_to_delete = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation_to_delete, "variation_to_delete")
    
    db.session.delete(variation_to_delete)
    db.session.commit()

    return jsonify({'message': 'Variation deleted successfully'}), 200
