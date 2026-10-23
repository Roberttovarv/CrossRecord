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
    data = body()
    name = text_field(data, "name")
    kind = data.get("kind", exercise["kind"])
    if kind not in ("calisthenic", "weighted", "cardio") or (exercise["kind"] != "mixed" and kind != exercise["kind"]):
        raise APIError("Invalid variation kind")
    doc = {"exercise_id": exercise["_id"], "kind": kind, "name": name, "name_key": name.casefold(), "slug": text_field(data, "slug", 120) if data.get("slug") else None, "equipment": data.get("equipment", exercise.get("equipment", [])), "aliases": data.get("aliases", []), "record_protocol": data.get("record_protocol", {"calisthenic": "max_reps", "weighted": "max_load", "cardio": "fastest_time"}[kind]), "record_enabled": data.get("record_enabled", True), "created_at": now()}
    if not isinstance(doc["equipment"], list) or not isinstance(doc["aliases"], list) or not isinstance(doc["record_protocol"], str) or not isinstance(doc["record_enabled"], bool):
        raise APIError("Invalid catalog metadata")
    doc = {key: value for key, value in doc.items() if value is not None}
    doc["_id"] = db().variations.insert_one(doc).inserted_id
    return jsonify(out(doc)), 201
