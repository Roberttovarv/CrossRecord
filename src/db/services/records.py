from pymongo import ASCENDING, DESCENDING

from ..common import APIError, boolean, number, oid, timestamp
from ..connection import db, now


def variation_for(variation_id):
    variation = db().variations.find_one({"_id": oid(variation_id)})
    if not variation:
        raise APIError("Variation not found", 404)
    return variation


def measure(data, kind):
    value = number(data.get("value"), "value", integer=kind in ("calisthenic", "cardio"))
    distance = number(data.get("distance_m"), "distance_m") if kind == "cardio" else None
    return value, distance


def best(user_id, variation, distance=None, session=None):
    query = {"user_id": user_id, "variation_id": variation["_id"], "distance_m": distance}
    direction = ASCENDING if variation["kind"] == "cardio" else DESCENDING
    return db().records.find_one(query, sort=[("value", direction), ("performed_at", DESCENDING)], session=session)
def record_document(user, variation, data, challenge_id=None, session=None):
    value, distance = measure(data, variation["kind"])
    performed_at = timestamp(data.get("performed_at"))
    latest = db().records.find_one({"user_id": user["_id"], "variation_id": variation["_id"], "distance_m": distance}, sort=[("performed_at", DESCENDING), ("_id", DESCENDING)], session=session)
    if latest and performed_at < latest["performed_at"]:
        raise APIError("performed_at cannot be earlier than the latest record for this variation and distance")
    previous = best(user["_id"], variation, distance, session)
    improved = previous is None or (value < previous["value"] if variation["kind"] == "cardio" else value > previous["value"])
    return {"user_id": user["_id"], "exercise_id": variation["exercise_id"], "variation_id": variation["_id"], "kind": variation["kind"], "value": value, "distance_m": distance, "performed_at": performed_at, "created_at": now(), "is_private": boolean(data, "is_private", True), "bodyweight": user.get("weight"), "challenge_id": challenge_id, "is_best": improved}
