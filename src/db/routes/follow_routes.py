from flask import Blueprint, request, jsonify
from src.db.models.user_models import Users
from flask_cors import CORS
from ...extensions import db

follow_api = Blueprint('follow_api', __name__)

CORS(follow_api)

