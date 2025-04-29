from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.weighted_models import WeightRecord, WeightedExerciseVariations
from ...extensions import db
from datetime import datetime

weighted_records_api = Blueprint('weighted_records_api', __name__)

CORS(weighted_records_api)

@weighted_records_api.route('/users/<int:user_id>/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>/records',
                            methods=["GET"])
def get_weighted_variation_records(user_id, exercise_id, variation_id):
    variation = WeightedExerciseVariations.query.filter_by(id=variation_id, exercise_id=exercise_id).first()
    if not variation:
        return jsonify({'error': 'Variation does not belong to this exercise'}), 404    
    
    records = WeightRecord.query.filter_by(
        user_id=user_id,
        variation_id=variation_id
    ).all()

    all_records = [record.serialize() for record in records]

    return jsonify(all_records), 200

@weighted_records_api.route('/users/<int:user_id>/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>/records',
                            methods=["POST"])
def add_weighted_variation_record(user_id, exercise_id, variation_id):
    data = request.json
    if not data:
        return jsonify({'error':'request body is empty'}), 400
    if 'lifted_weight' not in data:
        return jsonify({'error': 'lifted_weight is required'}), 400
    
    variation = WeightedExerciseVariations.query.filter_by(id=variation_id, exercise_id=exercise_id).first()
    if not variation:
        return jsonify({'error': 'Variation does not belong to this exercise'}), 404
    
    new_record = WeightRecord(
        lifted_weight=data["lifted_weight"],
        date=datetime.utcnow().date(),
        is_a_challenge=data.get("is_a_challenge", False),
        user_id=user_id,
        variation_id=variation_id
    )

    db.session.add(new_record)
    db.session.commit()

    return jsonify(new_record.serialize()), 201


@weighted_records_api.route('/users/<int:user_id>/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>/records/<int:record_id>',
                            methods=["GET"])
def get_single_weighted_variation_record(user_id, exercise_id, variation_id, record_id):
    variation = WeightedExerciseVariations.query.filter_by(id=variation_id, exercise_id=exercise_id).first()
    if not variation:
        return jsonify({'error': 'Variation does not belong to this exercise'}), 404
   
    record = WeightRecord.query.filter_by(id=record_id, user_id=user_id, variation_id=variation_id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    return jsonify(record.serialize()), 200

@weighted_records_api.route('/users/<int:user_id>/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>/records/<int:record_id>',
                            methods=["PUT"])
def edit_single_weighted_variation_record(user_id, exercise_id, variation_id, record_id):
    variation = WeightedExerciseVariations.query.filter_by(id=variation_id, exercise_id=exercise_id).first()
    if not variation:
        return jsonify({'error': 'Variation does not belong to this exercise'}), 404
    record = WeightRecord.query.filter_by(id=record_id, user_id=user_id, variation_id=variation_id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'Request body is empty'}), 400
    
    record.lifted_weight = data.get('lifted_weight', record.lifted_weight)
    if 'date' in data:
        record.date = datetime.strptime(data["date"], "%d/%m/%Y").date()
    record.is_a_challenge = record.is_a_challenge

    db.session.commit()

    return jsonify({'message': 'The record has been edited correctly', 'record': record.serialize()}), 200

@weighted_records_api.route('/users/<int:user_id>/exercises/weighted/<int:exercise_id>/variations/<int:variation_id>/records/<int:record_id>',
                            methods=["DELETE"])
def delete_single_weighted_variation_record(user_id, exercise_id, variation_id, record_id):
    variation = WeightedExerciseVariations.query.filter_by(id=variation_id, exercise_id=exercise_id).first()
    if not variation:
        return jsonify({'error': 'Variation does not belong to this exercise'}), 404
    record = WeightRecord.query.filter_by(id=record_id, user_id=user_id, variation_id=variation_id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    db.session.delete(record)
    db.session.commit()

    return jsonify({'message':'The record has been deleted successfully'}), 200