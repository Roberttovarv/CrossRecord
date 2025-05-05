from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.db.models.challenge_models import WeightedChallenge
from src.db.models.user_models import Users
from ....extensions import db, validate_existence
from datetime import datetime

weighted_challenges_api = Blueprint("weighted_challenges_api", __name__)

CORS(weighted_challenges_api)

@weighted_challenges_api.route('/users/<int:user_id>/challenges/received',
                               methods=["GET"])
def get_all_received_challenges(user_id):
    user = Users.query.get(user_id)
    validate_existence(user, "user")

    all_received_challenges = user.serialize()['received_challenges']

    return jsonify(all_received_challenges), 200

@weighted_challenges_api.route('/users/<int:user_id>/challenges/sent',
                               methods=["GET"])
def get_all_sent_challenges(user_id):
    user = Users.query.get(user_id)
    validate_existence(user, "user")

    all_sent_challenges = user.serialize()['sent_challenges']

    return jsonify(all_sent_challenges), 200



