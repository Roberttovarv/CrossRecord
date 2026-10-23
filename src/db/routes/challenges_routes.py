from datetime import timedelta
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from pymongo import DESCENDING, ReturnDocument

from ..common import APIError, body, number, oid, out, pagination
from ..connection import db, now
from ..services.challenges import LIMITS, challenge_baseline, challenge_view, expire_challenges
from ..services.records import best, measure, record_document, variation_for
from ..services.notifications import notify_challenge
from ..services.users import actor, public_record

challenges_api = Blueprint("challenges_api", __name__)


@challenges_api.get("/challenges/options")
@jwt_required()
def challenge_options():
    challenger = actor()
    target, variation, record, distance, allowed = challenge_baseline(challenger, request.args.get("user_id"), request.args.get("variation_id"), request.args.get("distance_m"))
    return jsonify(user_id=str(target["_id"]), variation_id=str(variation["_id"]), distance_m=distance, baseline=record["value"], limits=allowed, max_percentage=float(LIMITS[variation["kind"]] * 100))


@challenges_api.post("/challenges")
@jwt_required()
def create_challenge():
    challenger, data = actor(), body()
    target, variation, record, distance, allowed = challenge_baseline(challenger, data.get("user_id"), data.get("variation_id"), data.get("distance_m"))
    value = number(data.get("target"), "target", integer=variation["kind"] in ("calisthenic", "cardio"))
    if not Decimal(str(allowed["min"])) <= Decimal(str(value)) <= Decimal(str(allowed["max"])):
        raise APIError("Target outside allowed limits")
    message = data.get("message", "")
    if not isinstance(message, str) or len(message) > 500:
        raise APIError("Invalid message")
    expire_challenges()
    created = now()
    challenge = {"challenger_id": challenger["_id"], "challenged_id": target["_id"], "variation_id": variation["_id"], "exercise_id": variation["exercise_id"], "kind": variation["kind"], "distance_m": distance, "baseline": record["value"], "baseline_record_id": record["_id"], "target": value, "message": message.strip(), "status": "pending", "active": True, "created_at": created, "expires_at": created + timedelta(days=7), "completed_at": None}
    baseline_decimal = Decimal(str(record["value"]))
    challenge["improvement_ratio"] = str((baseline_decimal - Decimal(str(value)) if variation["kind"] == "cardio" else Decimal(str(value)) - baseline_decimal) / baseline_decimal)
    def save(session):
        db().users.update_one({"_id": target["_id"]}, {"$inc": {"record_revision": 1}}, session=session)
        current_best = best(target["_id"], variation, distance, session)
        if not current_best or current_best["_id"] != record["_id"] or current_best["value"] != record["value"]:
            raise APIError("Best record changed; refresh and try again", 409)
        challenge["_id"] = db().challenges.insert_one(challenge, session=session).inserted_id
        notify_challenge(challenge, "received", session, [target["_id"]])
    with current_app.extensions["mongo_client"].start_session() as session:
        session.with_transaction(save)
    return jsonify(out(challenge)), 201


@challenges_api.get("/challenges")
@jwt_required()
def list_challenges():
    user = actor()
    expire_challenges()
    limit, offset = pagination()
    query = {"$or": [{"challenger_id": user["_id"]}, {"challenged_id": user["_id"]}]}
    docs = list(db().challenges.find(query).sort([("created_at", DESCENDING), ("_id", DESCENDING)]).skip(offset).limit(limit + 1))
    return jsonify(items=[challenge_view(c, user) for c in docs[:limit]], next_offset=offset + limit if len(docs) > limit else None)


@challenges_api.post("/challenges/<challenge_id>/<action>")
@jwt_required()
def change_challenge(challenge_id, action):
    user = actor()
    challenge_id = oid(challenge_id)
    expire_challenges()
    challenge = db().challenges.find_one({"_id": challenge_id})
    if not challenge or user["_id"] not in (challenge["challenger_id"], challenge["challenged_id"]):
        raise APIError("Challenge not found", 404)
    if action in ("accept", "reject", "cancel"):
        owner_field = "challenger_id" if action == "cancel" else "challenged_id"
        if challenge[owner_field] != user["_id"]:
            raise APIError("Not authorized for this action", 403)
        statuses = ["pending", "accepted"] if action == "cancel" else ["pending"]
        status = {"accept": "accepted", "reject": "rejected", "cancel": "cancelled"}[action]
        changes = {"status": status, "active": status == "accepted"}
        if action == "accept":
            changes["accepted_at"] = now()
        def transition(session):
            updated = db().challenges.find_one_and_update({"_id": challenge_id, "status": {"$in": statuses}, "expires_at": {"$gt": now()}}, {"$set": changes}, return_document=ReturnDocument.AFTER, session=session)
            if not updated:
                raise APIError("Invalid challenge state", 409)
            notify_challenge(updated, status, session, [updated["challenged_id"] if action == "cancel" else updated["challenger_id"]])
            return updated
        with current_app.extensions["mongo_client"].start_session() as session:
            updated = session.with_transaction(transition)
        return jsonify(challenge_view(updated, user))
    if action != "complete":
        raise APIError("Unknown action", 404)
    if user["_id"] != challenge["challenged_id"]:
        raise APIError("Only the challenged user can complete this challenge", 403)
    data = body()
    variation = variation_for(str(challenge["variation_id"]))
    value, distance = measure(data, variation["kind"])
    if distance != challenge["distance_m"]:
        raise APIError("Distance must match the challenge")
    if (value > challenge["target"] if variation["kind"] == "cardio" else value < challenge["target"]):
        raise APIError("Result does not reach the target")

    def complete(session):
        db().users.update_one({"_id": user["_id"]}, {"$inc": {"record_revision": 1}}, session=session)
        updated = db().challenges.find_one_and_update({"_id": challenge_id, "challenged_id": user["_id"], "status": "accepted", "expires_at": {"$gt": now()}}, {"$set": {"status": "completed", "active": False, "completed_at": now()}}, return_document=ReturnDocument.AFTER, session=session)
        if not updated:
            raise APIError("Challenge is not active and accepted", 409)
        record = record_document(user, variation, data, challenge_id, session)
        if not updated.get("accepted_at") or record["performed_at"] <= updated["accepted_at"]:
            raise APIError("Result must be performed after the challenge was accepted")
        record["_id"] = db().records.insert_one(record, session=session).inserted_id
        notify_challenge(updated, "completed", session, [updated["challenger_id"]])
        return updated, record

    with current_app.extensions["mongo_client"].start_session() as session:
        updated, record = session.with_transaction(complete)
    return jsonify(challenge=out(updated), record=public_record(record))
