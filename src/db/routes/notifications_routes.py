from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from pymongo import DESCENDING

from ..common import APIError, oid, out, pagination
from ..connection import db, now
from ..services.users import actor

notifications_api = Blueprint("notifications_api", __name__)


@notifications_api.get("/me/notifications")
@jwt_required()
def notifications():
    user = actor()
    limit, offset = pagination()
    docs = list(db().notifications.find({"user_id": user["_id"]}).sort([("created_at", DESCENDING), ("_id", DESCENDING)]).skip(offset).limit(limit + 1))
    return jsonify(items=[out(doc) for doc in docs[:limit]], next_offset=offset + limit if len(docs) > limit else None)


@notifications_api.post("/me/notifications/<notification_id>/read")
@jwt_required()
def read_notification(notification_id):
    user = actor()
    result = db().notifications.update_one({"_id": oid(notification_id), "user_id": user["_id"], "read_at": None}, {"$set": {"read_at": now()}})
    if not result.matched_count and not db().notifications.find_one({"_id": oid(notification_id), "user_id": user["_id"]}):
        raise APIError("Notification not found", 404)
    return jsonify(read=True)
