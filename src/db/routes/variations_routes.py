from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from pymongo import ASCENDING

from ..common import APIError, body, oid, out, text_field
from ..connection import db, now
from ..services.users import actor, admin

variations_api = Blueprint("variations_api", __name__)


@variations_api.get("/exercises/<exercise_id>/variations")
@jwt_required()
def variations(exercise_id):
    actor()
    return jsonify(items=out(list(db().variations.find({"exercise_id": oid(exercise_id)}).sort("name", ASCENDING))))


@variations_api.post("/exercises/<exercise_id>/variations")
@admin
def create_variation(exercise_id):
    exercise = db().exercises.find_one({"_id": oid(exercise_id)})
    if not exercise:
        raise APIError("Exercise not found", 404)
    name = text_field(body(), "name")
    doc = {"exercise_id": exercise["_id"], "kind": exercise["kind"], "name": name, "name_key": name.casefold(), "created_at": now()}
    doc["_id"] = db().variations.insert_one(doc).inserted_id
    return jsonify(out(doc)), 201
