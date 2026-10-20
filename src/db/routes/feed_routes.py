from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from pymongo import DESCENDING

from ..common import APIError, pagination
from ..connection import db
from ..services.users import actor, friends, public_record, public_user, visible

feed_api = Blueprint("feed_api", __name__)


@feed_api.get("/feed/<feed_type>")
@jwt_required()
def feed(feed_type):
    user = actor()
    if feed_type not in ("following", "global"):
        raise APIError("Not found", 404)
    limit, offset = pagination()
    query = {"is_best": True, "is_private": False}
    if feed_type == "following":
        ids = [f["followed_id"] for f in db().follows.find({"follower_id": user["_id"]})]
        query["user_id"] = {"$in": ids + [user["_id"]]}
    # Free accounts must not recover their older records via the feed.
    own_allowed = None
    if not user.get("premium"):
        own_allowed = {r["_id"] for r in db().records.find({"user_id": user["_id"]}, {"_id": 1}).sort([("performed_at", DESCENDING), ("_id", DESCENDING)]).limit(3)}
    candidates = []
    for record in db().records.find(query).sort([("created_at", DESCENDING), ("_id", DESCENDING)]):
        owner = db().users.find_one({"_id": record["user_id"]})
        if not owner or (record["user_id"] == user["_id"] and own_allowed is not None and record["_id"] not in own_allowed):
            continue
        if feed_type == "global" and owner["profile_private"]:
            continue
        if not visible(record, owner, user["_id"]):
            continue
        item = {"record": public_record(record), "user": public_user(owner), "challenger": None}
        if record.get("challenge_id"):
            challenge = db().challenges.find_one({"_id": record["challenge_id"]})
            challenger = db().users.find_one({"_id": challenge["challenger_id"]}) if challenge else None
            if challenger and (not challenger["profile_private"] or challenger["_id"] == user["_id"] or friends(challenger["_id"], user["_id"])):
                item["challenger"] = public_user(challenger)
        candidates.append(item)
    if feed_type == "global":
        # Diversify within recent batches while keeping the result deterministic.
        ordered = []
        for start in range(0, len(candidates), 50):
            remaining = candidates[start:start + 50]
            previous_user = previous_exercise = None
            while remaining:
                index = next((i for i, item in enumerate(remaining) if item["user"]["id"] != previous_user and item["record"]["exercise_id"] != previous_exercise), 0)
                item = remaining.pop(index)
                ordered.append(item)
                previous_user, previous_exercise = item["user"]["id"], item["record"]["exercise_id"]
        candidates = ordered
    return jsonify(items=candidates[offset:offset + limit], next_offset=offset + limit if len(candidates) > offset + limit else None)
