from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pymongo import ASCENDING

from ..common import APIError, body, out, pagination, text_field
from ..connection import db, now
from ..services.users import actor, admin

KINDS = ("calisthenic", "weighted", "cardio", "mixed")

exercises_api = Blueprint("exercises_api", __name__)


@exercises_api.get("/exercises")
@jwt_required()
def exercises():
    actor()
    query = {}
    if request.args.get("kind"):
        if request.args["kind"] not in KINDS:
            raise APIError("Invalid kind")
        query["kind"] = request.args["kind"]
    if request.args.get("domain"):
        query["domain"] = request.args["domain"]
    limit, offset = pagination()
    return jsonify(items=out(list(db().exercises.find(query).sort("name", ASCENDING).skip(offset).limit(limit))))


@exercises_api.post("/exercises")
@admin
def create_exercise():
    data = body()
    kind = data.get("kind")
    if kind not in KINDS:
        raise APIError("Invalid kind")
    doc = {"name": text_field(data, "name"), "kind": kind, "slug": text_field(data, "slug", 100) if data.get("slug") else None, "domain": data.get("domain", "general"), "family": data.get("family", "general"), "equipment": data.get("equipment", []), "aliases": data.get("aliases", []), "record_kinds": data.get("record_kinds", [kind] if kind != "mixed" else []), "created_at": now()}
    if not isinstance(doc["domain"], str) or not isinstance(doc["family"], str) or not isinstance(doc["equipment"], list) or not isinstance(doc["aliases"], list) or not isinstance(doc["record_kinds"], list):
        raise APIError("Invalid catalog metadata")
    doc = {key: value for key, value in doc.items() if value is not None}
    doc["_id"] = db().exercises.insert_one(doc).inserted_id
    return jsonify(out(doc)), 201
