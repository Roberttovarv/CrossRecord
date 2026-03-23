from datetime import date

from flask import Blueprint, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import jwt_required

from src.db.models.calisthenic_models import CalisthenicExerciseVariations, CalisthenicRecord
from src.db.models.challenge_models import CalisthenicChallenge
from src.db.models.user_models import Users
from src.db.routes.challenges.common import (
    abort_with_error,
    get_authenticated_user_id,
    refresh_challenge_status,
    refresh_challenges,
    validate_calisthenic_target,
    validate_positive_number,
    validate_single_active_challenge,
)
from src.extensions import db, validate_existence, validate_user_access

calisthenic_challenges_api = Blueprint("calisthenic_challenges_api", __name__)

CORS(calisthenic_challenges_api)


def get_best_calisthenic_record(user_id: int, variation_id: int):
    return CalisthenicRecord.query.filter_by(
        user_id=user_id,
        variation_id=variation_id,
    ).order_by(CalisthenicRecord.repetitions.desc()).first()


def get_calisthenic_variation_or_404(exercise_id: int, variation_id: int):
    variation = CalisthenicExerciseVariations.query.filter_by(
        id=variation_id,
        exercise_id=exercise_id,
    ).first()
    validate_existence(variation, "variation")
    return variation


def get_calisthenic_challenge_or_404(user_id: int, variation_id: int, challenge_id: int):
    challenge = CalisthenicChallenge.query.filter_by(
        id=challenge_id,
        variation_id=variation_id,
        challenged_id=user_id,
    ).first()
    validate_existence(challenge, "challenge")
    return refresh_challenge_status(challenge)


def serialize_calisthenic_challenges(challenges):
    return [challenge.serialize() for challenge in refresh_challenges(challenges)]


@calisthenic_challenges_api.route(
    "/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/challenges",
    methods=["GET"],
)
@jwt_required()
def get_all_calisthenic_exercise_challenges(user_id, exercise_id):
    validate_user_access(user_id)
    challenged = db.session.get(Users, user_id)
    validate_existence(challenged, "challenged")

    variations_subquery = CalisthenicExerciseVariations.query.with_entities(
        CalisthenicExerciseVariations.id
    ).filter_by(exercise_id=exercise_id)
    challenges = CalisthenicChallenge.query.filter(
        CalisthenicChallenge.challenged_id == user_id,
        CalisthenicChallenge.variation_id.in_(variations_subquery),
    ).all()

    return jsonify(serialize_calisthenic_challenges(challenges)), 200


@calisthenic_challenges_api.route(
    "/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges",
    methods=["GET"],
)
@jwt_required()
def get_all_single_calisthenic_variation_challenges(user_id, exercise_id, variation_id):
    validate_user_access(user_id)
    challenged = db.session.get(Users, user_id)
    validate_existence(challenged, "challenged")
    get_calisthenic_variation_or_404(exercise_id, variation_id)

    challenges = CalisthenicChallenge.query.filter_by(
        challenged_id=user_id,
        variation_id=variation_id,
    ).all()

    return jsonify(serialize_calisthenic_challenges(challenges)), 200


@calisthenic_challenges_api.route(
    "/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges",
    methods=["POST"],
)
@jwt_required()
def add_single_calisthenic_variation_challenge(user_id, exercise_id, variation_id):
    data = request.json
    validate_existence(data, "data")

    challenger_id = data.get("challenger_id")
    validate_existence(challenger_id, "challenger_id")
    validate_user_access(challenger_id)
    if challenger_id == user_id:
        return jsonify({"error": "You cant challenge yourself"}), 400

    challenger = db.session.get(Users, challenger_id)
    validate_existence(challenger, "challenger")
    challenged = db.session.get(Users, user_id)
    validate_existence(challenged, "challenged")
    get_calisthenic_variation_or_404(exercise_id, variation_id)

    target_repetitions = int(validate_positive_number(data.get("record_to_complete"), "record_to_complete"))
    best_record = get_best_calisthenic_record(user_id, variation_id)
    validate_existence(best_record, "current_calisthenic_record")
    validate_calisthenic_target(best_record.repetitions, target_repetitions)
    validate_single_active_challenge(CalisthenicChallenge, user_id, variation_id)

    challenge = CalisthenicChallenge(
        challenger_id=challenger_id,
        challenged_id=user_id,
        variation_id=variation_id,
        record_to_complete=target_repetitions,
        message=data.get("message", ""),
        date=date.today(),
        is_completed=False,
        status="pending",
    )

    db.session.add(challenge)
    db.session.commit()

    return jsonify(
        {
            "message": "Challenge created successfully",
            "challenge": challenge.serialize(),
        }
    ), 201


@calisthenic_challenges_api.route(
    "/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges/<int:challenge_id>",
    methods=["GET"],
)
@jwt_required()
def get_single_calisthenic_variation_challenge(user_id, exercise_id, variation_id, challenge_id):
    validate_user_access(user_id)
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")
    get_calisthenic_variation_or_404(exercise_id, variation_id)

    challenge = get_calisthenic_challenge_or_404(user_id, variation_id, challenge_id)
    return jsonify(challenge.serialize()), 200


@calisthenic_challenges_api.route(
    "/users/<int:user_id>/exercises/calisthenic/<int:exercise_id>/variations/<int:variation_id>/challenges/<int:challenge_id>",
    methods=["PUT"],
)
@jwt_required()
def update_single_calisthenic_variation_challenge(user_id, exercise_id, variation_id, challenge_id):
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")
    get_calisthenic_variation_or_404(exercise_id, variation_id)
    challenge = get_calisthenic_challenge_or_404(user_id, variation_id, challenge_id)

    data = request.json or {}
    action = data.get("action", "complete")
    current_user_id = get_authenticated_user_id()

    if action == "accept":
        if current_user_id != challenge.challenged_id:
            abort_with_error("Only the challenged user can accept this challenge", 403)
        if challenge.status != "pending":
            abort_with_error("Only pending challenges can be accepted")
        challenge.status = "accepted"
        db.session.commit()
        return jsonify({"message": "The challenge has been accepted", "challenge": challenge.serialize()}), 200

    if action == "reject":
        if current_user_id != challenge.challenged_id:
            abort_with_error("Only the challenged user can reject this challenge", 403)
        if challenge.status != "pending":
            abort_with_error("Only pending challenges can be rejected")
        challenge.status = "rejected"
        db.session.commit()
        return jsonify({"message": "The challenge has been rejected", "challenge": challenge.serialize()}), 200

    if action == "cancel":
        if current_user_id != challenge.challenger_id:
            abort_with_error("Only the creator can cancel this challenge", 403)
        if challenge.status not in {"pending", "accepted"}:
            abort_with_error("Only active challenges can be cancelled")
        challenge.status = "cancelled"
        db.session.commit()
        return jsonify({"message": "The challenge has been cancelled", "challenge": challenge.serialize()}), 200

    if action != "complete":
        abort_with_error("Unsupported action")

    if current_user_id != challenge.challenged_id:
        abort_with_error("Only the challenged user can complete this challenge", 403)
    if challenge.status != "accepted":
        abort_with_error("The challenge must be accepted before completing it")

    new_record = CalisthenicRecord(
        repetitions=challenge.record_to_complete,
        date=challenge.date,
        is_a_challenge=True,
        is_private=False,
        bodyweight=user.weight,
        user_id=user_id,
        variation_id=variation_id,
    )

    db.session.add(new_record)
    challenge.is_completed = True
    challenge.status = "completed"
    db.session.commit()

    return jsonify(
        {
            "message": "The challenge has been completed successfully",
            "challenge": challenge.serialize(),
            "record": new_record.serialize(),
        }
    ), 200
