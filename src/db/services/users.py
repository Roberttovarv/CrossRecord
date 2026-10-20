from functools import wraps

from flask_jwt_extended import get_jwt_identity, jwt_required

from ..common import APIError, oid, out
from ..connection import db


def actor():
    user = db().users.find_one({"_id": oid(get_jwt_identity())})
    if not user:
        raise APIError("User not found", 401)
    return user


def get_user(user_id):
    user = db().users.find_one({"_id": oid(user_id)})
    if not user:
        raise APIError("User not found", 404)
    return user


def admin(fn):
    @wraps(fn)
    @jwt_required()
    def wrapped(*args, **kwargs):
        if not actor().get("is_admin", False):
            raise APIError("Administrator required", 403)
        return fn(*args, **kwargs)
    return wrapped


def friends(a, b):
    return bool(db().follows.find_one({"follower_id": a, "followed_id": b}) and db().follows.find_one({"follower_id": b, "followed_id": a}))


def visible(record, owner, viewer_id):
    if viewer_id == owner["_id"]:
        return True
    return not record["is_private"] and (not owner["profile_private"] or (viewer_id is not None and friends(owner["_id"], viewer_id)))


def public_user(user):
    return out({k: user.get(k) for k in ("_id", "username", "name", "profile_picture", "profile_private")})


def private_user(user):
    return {**public_user(user), "email": user["email"], "last_name": user["last_name"], "weight": user.get("weight"), "premium": user.get("premium", False), "show_ads": not user.get("premium", False), "is_admin": user.get("is_admin", False)}


def public_record(record):
    return out({k: v for k, v in record.items() if k not in ("is_best",)})
