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
    # The free limit applies to published bests per variation/distance, not to
    # the three latest training records across all exercises.
    own_allowed = {}
    items = []
    matched = 0
    for record in db().records.find(query).sort([("created_at", DESCENDING), ("_id", DESCENDING)]):
        owner = db().users.find_one({"_id": record["user_id"]})
        if not owner or owner.get("deactivated_at"):
            continue
        if record["user_id"] == user["_id"] and not user.get("premium"):
            group = (record["variation_id"], record.get("distance_m"))
            if group not in own_allowed:
                own_allowed[group] = {r["_id"] for r in db().records.find({"user_id": user["_id"], "variation_id": group[0], "distance_m": group[1], "is_best": True, "is_private": False}, {"_id": 1}).sort([("created_at", DESCENDING), ("_id", DESCENDING)]).limit(3)}
            if record["_id"] not in own_allowed[group]:
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
        if matched >= offset:
            items.append(item)
            if len(items) > limit:
                break
        matched += 1
    return jsonify(items=items[:limit], next_offset=offset + limit if len(items) > limit else None)
