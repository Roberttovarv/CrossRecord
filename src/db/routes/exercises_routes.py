from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pymongo import ASCENDING

from ..common import APIError, body, out, pagination, text_field
from ..connection import db, now
from ..services.users import actor, admin

KINDS = ("calisthenic", "weighted", "cardio")

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
    limit, offset = pagination()
    return jsonify(items=out(list(db().exercises.find(query).sort("name", ASCENDING).skip(offset).limit(limit))))


@exercises_api.post("/exercises")
@admin
def create_exercise():
    data = body()
    kind = data.get("kind")
    if kind not in KINDS:
        raise APIError("Invalid kind")
    doc = {"name": text_field(data, "name"), "kind": kind, "created_at": now()}
    doc["_id"] = db().exercises.insert_one(doc).inserted_id
    return jsonify(out(doc)), 201
