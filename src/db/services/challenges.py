from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

from flask import current_app

from ..common import APIError, number, out
from ..connection import db, now
from .notifications import notify_challenge
from .records import best, variation_for
from .users import friends, get_user, visible

LIMITS = {"calisthenic": Decimal("0.20"), "weighted": Decimal("0.10"), "cardio": Decimal("0.15")}


def bounds(record, kind):
    baseline = Decimal(str(record["value"]))
    increase = baseline * LIMITS[kind]
    if kind == "calisthenic":
        whole = increase.to_integral_value(rounding=ROUND_FLOOR)
        increase = whole + (1 if increase - whole >= Decimal("0.65") else 0)
        return {"min": int(baseline + 1), "max": int(baseline + increase), "step": 1}
    if kind == "weighted":
        maximum = (baseline + increase).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
        return {"min": float(baseline + Decimal("0.01")), "max": float(maximum), "step": 0.01}
    minimum = (baseline - increase).to_integral_value(rounding=ROUND_CEILING)
    return {"min": int(max(1, minimum)), "max": int(baseline - 1), "step": 1}
def expire_challenges():
    db().challenges.update_many({"active": True, "expires_at": {"$lte": now()}}, {"$set": {"status": "expired", "active": False}})
    # Legacy accepted challenges lack proof of when acceptance occurred.
    # Require fresh acceptance instead of inventing a timestamp.
    for item in db().challenges.find({"active": True, "status": "accepted", "accepted_at": None, "expires_at": {"$gt": now()}}, {"_id": 1}):
        def migrate(session):
            challenge = db().challenges.find_one_and_update(
                {"_id": item["_id"], "active": True, "status": "accepted", "accepted_at": None, "expires_at": {"$gt": now()}},
                {"$set": {"status": "pending"}}, session=session,
            )
            if challenge:
                notify_challenge(challenge, "acceptance_required", session)
        with current_app.extensions["mongo_client"].start_session() as session:
            session.with_transaction(migrate)


def challenge_view(challenge, viewer):
    def with_participants(result):
        for field in ("challenger", "challenged"):
            person = db().users.find_one({"_id": challenge[field + "_id"]})
            if person:
                result[field] = {"username": person["username"], "profile_id": None if person.get("deactivated_at") else str(person["_id"])}
        return result
    if viewer["_id"] == challenge["challenged_id"]:
        return with_participants(out(challenge))
    owner = db().users.find_one({"_id": challenge["challenged_id"]})
    baseline = db().records.find_one({"_id": challenge["baseline_record_id"]})
    if owner and baseline and visible(baseline, owner, viewer["_id"]):
        return with_participants(out(challenge))
    return with_participants(out({k: challenge[k] for k in ("_id", "challenger_id", "challenged_id", "status", "created_at", "expires_at", "completed_at")}))


def challenge_baseline(challenger, target_id, variation_id, distance_value):
    target = get_user(target_id)
    variation = variation_for(variation_id)
    if challenger["_id"] == target["_id"] or not friends(challenger["_id"], target["_id"]):
        raise APIError("Challenges require mutual following", 403)
    distance = number(distance_value, "distance_m") if variation["kind"] == "cardio" else None
    record = best(target["_id"], variation, distance)
    if not record or not visible(record, target, challenger["_id"]):
        raise APIError("A visible best record is required", 404)
    allowed = bounds(record, variation["kind"])
    if allowed["min"] > allowed["max"]:
        raise APIError("No valid target exists for this record", 400)
    return target, variation, record, distance, allowed
