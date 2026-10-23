from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from pymongo import DESCENDING

from ..common import APIError, body, boolean, fail, number, oid, pagination, timestamp
from ..connection import db
from ..services.records import record_document, variation_for
from ..services.record_changes import apply_challenge_decision, can_access_record, correct_record, matching_challenge
from ..services.challenges import challenge_view
from ..services.users import actor, public_record

records_api = Blueprint("records_api", __name__)


@records_api.post("/records")
@jwt_required()
def create_record():
    user, data = actor(), body()
    variation = variation_for(data.get("variation_id"))
    def save(session):
        db().users.update_one({"_id": user["_id"]}, {"$inc": {"record_revision": 1}}, session=session)
        record = record_document(user, variation, data, session=session)
        apply_challenge_decision(user, record, data, session)
        record["_id"] = db().records.insert_one(record, session=session).inserted_id
        return record
    with current_app.extensions["mongo_client"].start_session() as session:
        record = session.with_transaction(save)
    return jsonify(public_record(record)), 201


@records_api.post("/records/preview")
@jwt_required()
def preview_record():
    user, data = actor(), body()
    variation = variation_for(data.get("variation_id"))
    record = record_document(user, variation, data)
    challenge = matching_challenge(user["_id"], record)
    return jsonify(challenge=challenge_view(challenge, user) if challenge else None)


@records_api.post("/records/<record_id>/preview")
@jwt_required()
def preview_record_change(record_id):
    user, data = actor(), body()
    record = db().records.find_one({"_id": oid(record_id), "user_id": user["_id"]})
    if not record:
        raise APIError("Record not found", 404)
    if not can_access_record(user, record):
        raise APIError("Premium required for older records", 403)
    if "value" in data:
        record["value"] = number(data["value"], "value", integer=record["kind"] in ("calisthenic", "cardio"))
    if "performed_at" in data:
        record["performed_at"] = timestamp(data["performed_at"])
    challenge = matching_challenge(user["_id"], record)
    if challenge and challenge.get("baseline_record_id") == record["_id"]:
        challenge = None
    return jsonify(challenge=challenge_view(challenge, user) if challenge else None)


@records_api.get("/me/records")
@jwt_required()
def history():
    user = actor()
    limit, offset = pagination()
    query = {"user_id": user["_id"]}
    variation_id = request.args.get("variation_id")
    if variation_id:
        variation = variation_for(variation_id)
        query["variation_id"] = variation["_id"]
        if variation["kind"] == "cardio":
            query["distance_m"] = number(request.args.get("distance_m"), "distance_m")
        elif request.args.get("distance_m") is not None:
            raise APIError("distance_m is only valid for cardio")
    elif not user.get("premium"):
        raise APIError("variation_id is required for free history")
    elif request.args.get("distance_m") is not None:
        raise APIError("variation_id is required with distance_m")
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
    record_id = oid(record_id)
    record = db().records.find_one({"_id": record_id, "user_id": user["_id"]})
    if record and not can_access_record(user, record):
        raise APIError("Premium required for older records", 403)
    result = db().records.update_one({"_id": record_id, "user_id": user["_id"]}, {"$set": {"is_private": boolean(data, "is_private")}})
    if not result.matched_count:
        raise APIError("Record not found", 404)
    return jsonify(updated=True)


@records_api.route("/records/<record_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def change_record(record_id):
    user = actor()
    identifier = oid(record_id)
    delete = request.method == "DELETE"
    data = {} if delete else body()
    with current_app.extensions["mongo_client"].start_session() as session:
        record = session.with_transaction(lambda s: correct_record(user, identifier, data, delete, s))
    return jsonify(deleted=True) if delete else jsonify(public_record(record))
