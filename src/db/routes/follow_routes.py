from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from pymongo import ASCENDING

from ..common import APIError, pagination
from ..connection import db, now
from ..services.users import actor, friends, get_user, public_user

follow_api = Blueprint("follow_api", __name__)


@follow_api.post("/users/<user_id>/follow")
@jwt_required()
def follow(user_id):
    user, target = actor(), get_user(user_id)
    if user["_id"] == target["_id"]:
        raise APIError("Cannot follow yourself")
    db().follows.insert_one({"follower_id": user["_id"], "followed_id": target["_id"], "created_at": now()})
    return jsonify(following=True, are_friends=friends(user["_id"], target["_id"])), 201


@follow_api.delete("/users/<user_id>/follow")
@jwt_required()
def unfollow(user_id):
    user, target = actor(), get_user(user_id)
    db().follows.delete_one({"follower_id": user["_id"], "followed_id": target["_id"]})
    return jsonify(following=False)


@follow_api.get("/me/<direction>")
@jwt_required()
def relationships(direction):
    user = actor()
    if direction not in ("following", "followers", "friends"):
        raise APIError("Not found", 404)
    limit, offset = pagination()
    field, other = ("followed_id", "follower_id") if direction == "followers" else ("follower_id", "followed_id")
    ids = [x[other] for x in db().follows.find({field: user["_id"]})]
    if direction == "friends":
        ids = [i for i in ids if friends(user["_id"], i)]
    return jsonify(items=[public_user(u) for u in db().users.find({"_id": {"$in": ids}, "deactivated_at": None}).sort("username_key", ASCENDING).skip(offset).limit(limit)])
