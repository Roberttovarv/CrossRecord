from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.challenge_models import CalisthenicChallenge
from src.db.models.calisthenic_models import CalisthenicExerciseVariations
from src.db.models.user_models import Users
from src.extensions import db, validate_existence
from datetime import datetime

calisthenic_challenges_api = Blueprint("calisthenic_challenges_api", __name__)

CORS(calisthenic_challenges_api)

@calisthenic_challenges_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/challenges',
                                  methods=["GET"])
def get_all_calisthenic_exercise_challenges(user_id, exercise_id):
    user = Users.query.get(user_id)
    validate_existence(user)

    variations = CalisthenicExerciseVariations.query.filter_by(exercise_id=exercise_id).all()
    variations_ids = [variation.id for variation in variations]

    all_calisthenic_exercise_challenges = [
        challenge.serialize() for challenge in user.received_challenges
        if challenge.variation_id in variations_ids
    ]

    return jsonify(all_calisthenic_exercise_challenges), 200

@calisthenic_challenges_api.route('/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges',
                                  methods=["GET"])
def get_all_single_calisthenic_variation_challenges(user_id, exercise_id, variation_id):
    user = Users.query.get(user_id)
    validate_existence(user)

    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    all_calisthenic_variation_challenges = [
        challenge.serialize() for challenge in user.received_calisthenic_challenges
        if challenge.variation_id == variation_id
    ]

    return jsonify(all_calisthenic_variation_challenges), 200

@calisthenic_challenges_api.route('/users/<int:challenged_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges',
                                  methods=["POST"])
def add_single_calisthenic_variation_challenge(challenged_id, exercise_id, variation_id):
    data = request.json
    validate_existence(data, "data")

    challenger_id = data.get("challenger_id")
    if challenger_id == challenged_id:
        return jsonify({'error': 'You cant challenge yourself'})
    
    challenger = Users.query.get(challenger_id)
    validate_existence(challenger, "challenger")
    challenged = Users.queey.get(challenged_id)
    validate_existence(challenged, "challenged")

    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    challenge = CalisthenicChallenge(
        challenger_id=challenger_id,
        challenged_id=challenged_id,
        variation_id=variation_id,
        record_to_complete=data["record_to_complete"],
        message=data.get("message", ""),
        date=datetime.strptime(data["date"], "%d/%m/%Y").date(),
        is_completed=False
    )

    db.session.add(challenge)
    db.session.commit()

    return jsonify({
        'message':f'Challenge created successfully',
        'challenge':challenge.serialize()
    }), 201

@calisthenic_challenges_api.route('/users/<int:challenged_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges/<int:challenge_id>',
                                  methods=["GET"])
def get_single_calisthenic_variation_challenge(user_id, exercise_id, variation_id, challenge_id):
    user = Users.query.get(user_id)
    validate_existence(user, "user")

    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    challenge = CalisthenicChallenge.query.filter_by(
        id=challenge_id,
        variation_id=variation_id,
        challenge_id=user_id
    ).first()
    validate_existence(challenge, "challenge")

    return jsonify(variation.serialize()), 200

@calisthenic_challenges_api.route('/users/<int:challenged_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges/<int:challenge_id>',
                                  methods=["PUT"])
def edit_single_weighted_variation_challenge(user_id, exercise_id, variation_id, challenge_id):
    user = Users.query.get(user_id)
    validate_existence(user, "user")

    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    challenge = CalisthenicChallenge.query.filter_by(
        id=challenge_id,
        variation_id=variation_id,
        challenged_id=user_id
    ).first()
    validate_existence(challenge, "challenge")

    challenge.is_completed = True

    db.session.commit()

    return jsonify({'message':'The challenge has been completed successfully'})

@calisthenic_challenges_api.route('/users/<int:challenged_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges/<int:challenge_id>',
                                  methods=["DELETE"])
def delete_single_calisthenic_variation_challenge(user_id, exercise_id, variation_id, challenge_id):
    user = Users.query.get(user_id)
    validate_existence(user, "user")

    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id
    ).first()
    validate_existence(variation, "variation")

    challenge = CalisthenicChallenge.query.filter_by(
        id=challenge_id,
        variation_id=variation_id,
        challenged_id=user_id
    ).first()
    validate_existence(challenge, "challenge")
    if challenge.is_completed:
        return jsonify({'error':'Completed challenges cant be deleted'})

    db.session.delete(challenge)
    db.session.commit()

    return jsonify({'message':'The challenge has been deleted successfully'}), 200