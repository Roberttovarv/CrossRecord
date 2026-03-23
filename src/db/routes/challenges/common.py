from datetime import date, timedelta
from math import ceil, floor

from flask import abort, jsonify
from flask_jwt_extended import get_jwt_identity

from src.extensions import db

ACTIVE_CHALLENGE_STATUSES = {"pending", "accepted"}
FINAL_CHALLENGE_STATUSES = {"rejected", "completed", "expired", "cancelled"}
CHALLENGE_EXPIRATION_DAYS = 7


def abort_with_error(message: str, status_code: int = 400):
    response = jsonify({"error": message})
    response.status_code = status_code
    abort(response)


def get_authenticated_user_id():
    identity = get_jwt_identity()
    return identity.get("user_id") if isinstance(identity, dict) else identity


def get_expiration_date(challenge_date: date):
    return challenge_date + timedelta(days=CHALLENGE_EXPIRATION_DAYS)


def refresh_challenge_status(challenge):
    if challenge.status in ACTIVE_CHALLENGE_STATUSES and get_expiration_date(challenge.date) < date.today():
        challenge.status = "expired"
        challenge.is_completed = False
        db.session.commit()
    return challenge


def refresh_challenges(challenges):
    return [refresh_challenge_status(challenge) for challenge in challenges]


def validate_single_active_challenge(challenge_model, challenged_id: int, variation_id: int):
    existing_challenge = challenge_model.query.filter(
        challenge_model.challenged_id == challenged_id,
        challenge_model.variation_id == variation_id,
        challenge_model.status.in_(tuple(ACTIVE_CHALLENGE_STATUSES)),
    ).first()
    if existing_challenge:
        abort_with_error("This user already has an active challenge for this variation")


def validate_weighted_target(current_value, proposed_value):
    if proposed_value <= current_value:
        abort_with_error("The challenge must improve the user's current weighted record")
    max_allowed = ceil(float(current_value) * 1.10)
    if proposed_value > max_allowed:
        abort_with_error(f"The challenge cannot exceed {max_allowed}")


def validate_calisthenic_target(current_value, proposed_value):
    if proposed_value <= current_value:
        abort_with_error("The challenge must improve the user's current calisthenic record")
    max_allowed = ceil(float(current_value) * 1.20)
    if proposed_value > max_allowed:
        abort_with_error(f"The challenge cannot exceed {max_allowed}")


def validate_cardio_target(current_value, proposed_value):
    if proposed_value >= current_value:
        abort_with_error("The challenge must improve the user's current cardio time")
    min_allowed = floor(float(current_value) * 0.85)
    if proposed_value < min_allowed:
        abort_with_error(f"The challenge cannot be lower than {min_allowed}")


def validate_positive_number(value, field_name: str):
    if value is None:
        abort_with_error(f"{field_name} not found.")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        abort_with_error(f"{field_name} must be a valid number")
    if numeric_value <= 0:
        abort_with_error(f"{field_name} must be greater than 0")
    return numeric_value
