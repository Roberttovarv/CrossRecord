from flask import Blueprint, jsonify
from flask_cors import CORS
from src.db.models.challenge_models import CardioChallenge, CalisthenicChallenge, WeightedChallenge
from src.db.models.user_models import Users
from src.db.routes.challenges.common import refresh_challenges
from src.extensions import db, validate_existence, validate_user_access
from flask_jwt_extended import jwt_required

user_challenges_api = Blueprint("user_challenges_api", __name__)

CORS(user_challenges_api)

@user_challenges_api.route('/users/<int:user_id>/challenges/received',
                               methods=["GET"])
@jwt_required()
def get_all_received_challenges(user_id):
    validate_user_access(user_id)
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")

    all_received_challenges = [
        *[
            challenge.serialize()
            for challenge in refresh_challenges(CardioChallenge.query.filter_by(challenged_id=user_id).all())
        ],
        *[
            challenge.serialize()
            for challenge in refresh_challenges(CalisthenicChallenge.query.filter_by(challenged_id=user_id).all())
        ],
        *[
            challenge.serialize()
            for challenge in refresh_challenges(WeightedChallenge.query.filter_by(challenged_id=user_id).all())
        ],
    ]

    return jsonify(all_received_challenges), 200

@user_challenges_api.route('/users/<int:user_id>/challenges/sent',
                               methods=["GET"])
@jwt_required()
def get_all_sent_challenges(user_id):
    validate_user_access(user_id)
    user = db.session.get(Users, user_id)
    validate_existence(user, "user")

    all_sent_challenges = [
        *[
            challenge.serialize()
            for challenge in refresh_challenges(CardioChallenge.query.filter_by(challenger_id=user_id).all())
        ],
        *[
            challenge.serialize()
            for challenge in refresh_challenges(CalisthenicChallenge.query.filter_by(challenger_id=user_id).all())
        ],
        *[
            challenge.serialize()
            for challenge in refresh_challenges(WeightedChallenge.query.filter_by(challenger_id=user_id).all())
        ],
    ]

    return jsonify(all_sent_challenges), 200
