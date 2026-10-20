from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

from ..common import APIError, number, out
from ..connection import db, now
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


def challenge_view(challenge, viewer):
    if viewer["_id"] == challenge["challenged_id"]:
        return out(challenge)
    owner = db().users.find_one({"_id": challenge["challenged_id"]})
    baseline = db().records.find_one({"_id": challenge["baseline_record_id"]})
    if owner and baseline and visible(baseline, owner, viewer["_id"]):
        return out(challenge)
    return out({k: challenge[k] for k in ("_id", "challenger_id", "challenged_id", "status", "created_at", "expires_at", "completed_at")})


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
