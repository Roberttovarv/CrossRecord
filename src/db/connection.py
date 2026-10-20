from datetime import datetime, timezone

from flask import current_app
from pymongo import ASCENDING, DESCENDING


def db():
    return current_app.extensions["mongo_db"]


def now():
    return datetime.now(timezone.utc)


def create_indexes(database):
    database.users.create_index("email_key", unique=True)
    database.users.create_index("username_key", unique=True)
    database.follows.create_index([("follower_id", ASCENDING), ("followed_id", ASCENDING)], unique=True)
    database.follows.create_index("followed_id")
    database.variations.create_index([("exercise_id", ASCENDING), ("name_key", ASCENDING)], unique=True)
    database.records.create_index([("user_id", ASCENDING), ("performed_at", DESCENDING), ("_id", DESCENDING)])
    database.records.create_index([("user_id", ASCENDING), ("variation_id", ASCENDING), ("distance_m", ASCENDING)])
    database.records.create_index([("is_best", ASCENDING), ("created_at", DESCENDING)])
    database.challenges.create_index([("challenged_id", ASCENDING), ("variation_id", ASCENDING), ("distance_m", ASCENDING), ("active", ASCENDING)], unique=True, partialFilterExpression={"active": True})
    database.challenges.create_index([("challenger_id", ASCENDING), ("created_at", DESCENDING)])
    database.challenges.create_index([("challenged_id", ASCENDING), ("created_at", DESCENDING)])
    database.records.create_index("challenge_id", unique=True, partialFilterExpression={"challenge_id": {"$type": "objectId"}})
