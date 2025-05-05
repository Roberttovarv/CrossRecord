from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.calisthenic_models import CalisthenicRecord, CalisthenicExerciseVariations
from ....extensions import db, validate_existence
from datetime import datetime

calisthenic_records_api = Blueprint("calisthenic_records_api", __name__)

CORS(calisthenic_records_api)

@calisthenic_records_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/records',
                               methods=["GET"])
def get_calisthenic_variation_records(user_id, exercise_id, variation_id):
    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")
    
    records = CalisthenicRecord.query.filter_by(
        user_id=user_id,
        variation_id=variation_id
    ).all()
    # validate_existence(records, "records")

    all_records = [record.serialize() for record in records]

    return jsonify(all_records), 200

@calisthenic_records_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/records',
                               methods=["POST"])
def add_calisthenic_variation_record(user_id, exercise_id, variation_id):
    data = request.json
    validate_existence(data.get("repetitions"), "repetitions")

    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    new_record = CalisthenicRecord(
        repetitions=data["repetitions"],
        date = datetime.utcnow().date,
        is_a_challenge=data.get("is_a_challenge", False),
        is_private=data.get("is_private", False),
        user_id=user_id,
        variation_id=variation_id
    )

    db.session.add(new_record)
    db.session.commit()

    return jsonify(new_record.serialize()), 201

@calisthenic_records_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/records/<int:record_id>',
                               methods=["GET"])
def get_single_calisthenic_variation_record(user_id, exercise_id, variation_id, record_id):
    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id 
    ).first()
    validate_existence(variation, "variation")

    record = CalisthenicRecord.query.filter_by(
        id=record_id,
        user_id=user_id,
        variation_id=variation_id
    ).first()
    validate_existence(record, "record")

    return jsonify(record.serialize()), 200

@calisthenic_records_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/records/<int:record_id>',
                               methods=["PUT"])
def edit_single_calisthenic_variation_record(user_id, exercise_id, variation_id, record_id):
    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    record = CalisthenicRecord.query.filter_by(
        id=record_id,
        user_id=user_id,
        variation_id=variation_id
    ).first()
    validate_existence(record, "record")

    data = request.json
    validate_existence(data, "data")

    record.repetitions = data["repetitions"]
    if "date" in data:
        record.date = datetime.strptime(data["date"], "%d/%m/%Y").date()
    if "is_private" in data:
        record.is_private=data["is_private"]

    db.session.commit()

    return jsonify({'message': 'The record has been edited correctly', 'record': record.serialize()}), 200

@calisthenic_records_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/records/<int:record_id>',
                               methods=["DELETE"])
def delete_single_calisthenic_variation_record(user_id, exercise_id, variation_id, record_id):
    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    record = CalisthenicRecord.query.filter_by(
        id=record_id,
        user_id=user_id,
        variation_id=variation_id
    ).first()
    validate_existence(record, "record")

    db.session.delete(record)
    db.session.commit()

    return jsonify({'message':'The record has been deleted successfully'}), 200