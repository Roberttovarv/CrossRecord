from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pymongo import ASCENDING

from ..common import body, boolean, number, pagination, text_field
from ..connection import db, now
from ..services.records import best
from ..services.users import actor, friends, get_user, private_user, public_record, public_user, visible

user_api = Blueprint("user_api", __name__)


@user_api.get("/me")
@jwt_required()
def me():
    return jsonify(private_user(actor(allow_unverified=True)))


@user_api.delete("/me")
@jwt_required()
def deactivate_me():
    user = actor()
    db().users.update_one({"_id": user["_id"]}, {"$set": {"deactivated_at": now()}, "$inc": {"session_version": 1}})
    return jsonify(deactivated=True)


@user_api.patch("/me")
@jwt_required()
def update_me():
    user, data = actor(), body()
    changes = {}
    for field in ("name", "last_name", "username"):
        if field in data:
            changes[field] = text_field(data, field, 20 if field == "username" else 50)
    if "username" in changes:
        changes["username_key"] = changes["username"].casefold()
    if "profile_private" in data:
        changes["profile_private"] = boolean(data, "profile_private")
    if "weight" in data:
        changes["weight"] = None if data["weight"] is None else number(data["weight"], "weight")
    if "profile_picture" in data:
        changes["profile_picture"] = None if data["profile_picture"] is None else text_field(data, "profile_picture", 2048)
    if changes:
        db().users.update_one({"_id": user["_id"]}, {"$set": changes})
        user.update(changes)
    return jsonify(private_user(user))


@user_api.get("/users")
@jwt_required()
def users():
    actor()
    limit, offset = pagination()
    query = request.args.get("q", "").strip().casefold()
    import re
    found = db().users.find({"username_key": {"$regex": "^" + re.escape(query)}, "deactivated_at": None}).sort("username_key", ASCENDING).skip(offset).limit(limit)
    return jsonify(items=[public_user(u) for u in found])


@user_api.get("/users/<user_id>")
@jwt_required()
def profile(user_id):
    viewer, owner = actor(), get_user(user_id)
    records = []
    # Profiles show current best marks, not a paginated history.
    for variation in db().variations.find():
        distances = db().records.distinct("distance_m", {"user_id": owner["_id"], "variation_id": variation["_id"]})
        for distance in distances:
            record = best(owner["_id"], variation, distance)
            if record and visible(record, owner, viewer["_id"]):
                records.append(public_record(record))
    return jsonify(user=private_user(owner) if viewer["_id"] == owner["_id"] else public_user(owner), records=records, are_friends=friends(viewer["_id"], owner["_id"]) if viewer["_id"] != owner["_id"] else False)
