from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from pymongo import DESCENDING

from ..common import APIError, body, boolean, fail, oid, pagination
from ..connection import db
from ..services.records import record_document, variation_for
from ..services.users import actor, public_record

records_api = Blueprint("records_api", __name__)


@records_api.post("/records")
@jwt_required()
def create_record():
    user, data = actor(), body()
    variation = variation_for(data.get("variation_id"))
    record = record_document(user, variation, data)
    record["_id"] = db().records.insert_one(record).inserted_id
    return jsonify(public_record(record)), 201


@records_api.get("/me/records")
@jwt_required()
def history():
    user = actor()
    limit, offset = pagination()
    query = {"user_id": user["_id"]}
    if not user.get("premium"):
        if offset:
            return fail("Premium required for more history", 403)
        records = list(db().records.find(query).sort([("performed_at", DESCENDING), ("_id", DESCENDING)]).limit(4))
        return jsonify(items=[public_record(r) for r in records[:3]], has_more_locked=len(records) > 3, next_offset=None)
    records = list(db().records.find(query).sort([("performed_at", DESCENDING), ("_id", DESCENDING)]).skip(offset).limit(limit + 1))
    return jsonify(items=[public_record(r) for r in records[:limit]], has_more_locked=False, next_offset=offset + limit if len(records) > limit else None)


@records_api.patch("/records/<record_id>/visibility")
@jwt_required()
def record_visibility(record_id):
    user, data = actor(), body()
    if "is_private" not in data:
        raise APIError("is_private is required")
    result = db().records.update_one({"_id": oid(record_id), "user_id": user["_id"]}, {"$set": {"is_private": boolean(data, "is_private")}})
    if not result.matched_count:
        raise APIError("Record not found", 404)
    return jsonify(updated=True)
