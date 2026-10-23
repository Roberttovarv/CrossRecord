"""Transactional corrections of existing records and their derived state."""
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

from pymongo import ASCENDING, DESCENDING

from ..common import APIError, boolean, number, oid, timestamp
from ..connection import db, now
from .notifications import notify_challenge
from .records import best


def matching_challenge(user_id, record, session=None):
    challenge = db().challenges.find_one({"challenged_id": user_id, "variation_id": record["variation_id"], "distance_m": record.get("distance_m"), "active": True, "expires_at": {"$gt": now()}}, session=session)
    if challenge and (record["value"] <= challenge["target"] if record["kind"] == "cardio" else record["value"] >= challenge["target"]):
        return challenge
    return None


def apply_challenge_decision(user, record, data, session):
    challenge = matching_challenge(user["_id"], record, session)
    choice = data.get("challenge_decision")
    if not challenge:
        if choice is not None:
            raise APIError("Challenge no longer matches; refresh and try again", 409)
        return
    if choice not in ("complete", "cancel") or oid(data.get("challenge_id")) != challenge["_id"]:
        raise APIError("Challenge decision and matching challenge_id are required", 409)
    if data.get("challenge_target") != challenge["target"]:
        raise APIError("Challenge target changed; refresh and try again", 409)
    update = {"active": False}
    if choice == "complete":
        if challenge["status"] == "pending":
            if data.get("performed_at") is not None or record["performed_at"] < now() - timedelta(seconds=5):
                raise APIError("Pending challenges require a result performed at confirmation")
            update["accepted_at"] = record["performed_at"]
            update["accepted_and_completed"] = True
        elif not challenge.get("accepted_at") or record["performed_at"] <= challenge["accepted_at"]:
            raise APIError("Result must be performed after acceptance")
        update.update({"status": "completed", "completed_at": now()})
        if record.get("challenge_id") and record["challenge_id"] != challenge["_id"]:
            raise APIError("Record already belongs to another challenge", 409)
        record["challenge_id"] = challenge["_id"]
    else:
        update["status"] = "cancelled"
    result = db().challenges.update_one({"_id": challenge["_id"], "status": challenge["status"], "active": True, "expires_at": {"$gt": now()}}, {"$set": update}, session=session)
    if not result.modified_count:
        raise APIError("Challenge changed; refresh and try again", 409)
    notify_challenge(challenge, update["status"], session)


def can_access_record(user, record, session=None):
    if user.get("premium"):
        return True
    query = {"user_id": user["_id"], "variation_id": record["variation_id"], "distance_m": record.get("distance_m")}
    recent = db().records.find(query, {"_id": 1}, session=session).sort([("performed_at", DESCENDING), ("_id", DESCENDING)]).limit(3)
    return record["_id"] in {item["_id"] for item in recent}


def recalculate_bests(user_id, variation, distance, session):
    query = {"user_id": user_id, "variation_id": variation["_id"], "distance_m": distance}
    previous = None
    for record in db().records.find(query, session=session).sort([("performed_at", ASCENDING), ("_id", ASCENDING)]):
        value = record["value"]
        improved = previous is None or (value < previous if variation["kind"] == "cardio" else value > previous)
        if record.get("is_best") != improved:
            db().records.update_one({"_id": record["_id"]}, {"$set": {"is_best": improved}}, session=session)
        if improved:
            previous = value


def recalculated_target(challenge, baseline):
    old = Decimal(str(challenge["baseline"]))
    original_target = Decimal(str(challenge["target"]))
    ratio = Decimal(challenge.get("improvement_ratio") or str((old - original_target if challenge["kind"] == "cardio" else original_target - old) / old))
    value = Decimal(str(baseline["value"]))
    delta = value * ratio
    if challenge["kind"] == "calisthenic":
        whole = delta.to_integral_value(rounding=ROUND_FLOOR)
        delta = whole + (1 if delta - whole >= Decimal("0.65") else 0)
        return (int(value + delta) if delta >= 1 else None), str(ratio)
    if challenge["kind"] == "cardio":
        result = (value - delta).to_integral_value(rounding=ROUND_CEILING)
        return (int(result) if 1 <= result < value else None), str(ratio)
    result = (value + delta).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
    return (float(result) if result > value else None), str(ratio)


def reconcile_challenges(record, variation, delete, changes, session):
    if not delete and not ({"value", "performed_at"} & changes.keys()):
        return
    challenge_id = record.get("challenge_id")
    completed = db().challenges.find_one({"_id": challenge_id, "status": "completed"}, session=session) if challenge_id else None
    if completed:
        value = record["value"]
        valid = not delete and (value <= completed["target"] if record["kind"] == "cardio" else value >= completed["target"])
        accepted_at = completed.get("accepted_at")
        valid = valid and accepted_at is not None and (record["performed_at"] >= accepted_at if completed.get("accepted_and_completed") else record["performed_at"] > accepted_at)
        if not valid:
            active = db().challenges.find_one({"challenged_id": record["user_id"], "variation_id": record["variation_id"], "distance_m": record.get("distance_m"), "active": True, "expires_at": {"$gt": now()}}, session=session)
            if active:
                update = {"status": "cancelled", "active": False, "completed_at": None}
            else:
                # Expired active documents must release the unique active slot.
                db().challenges.update_many({"challenged_id": record["user_id"], "variation_id": record["variation_id"], "distance_m": record.get("distance_m"), "active": True, "expires_at": {"$lte": now()}}, {"$set": {"active": False, "status": "expired"}}, session=session)
                update = {"status": "accepted", "active": True, "completed_at": None, "expires_at": now() + timedelta(days=7)}
            db().challenges.update_one({"_id": challenge_id}, {"$set": update}, session=session)
            if not delete:
                db().records.update_one({"_id": record["_id"]}, {"$set": {"challenge_id": None}}, session=session)
            notify_challenge(completed, "cancelled" if active else "reopened", session)
    for challenge in db().challenges.find({"baseline_record_id": record["_id"], "active": True, "expires_at": {"$gt": now()}}, session=session):
        baseline = best(record["user_id"], variation, record.get("distance_m"), session)
        target, ratio = recalculated_target(challenge, baseline) if baseline else (None, None)
        if target is None:
            update = {"status": "cancelled", "active": False}
            event = "cancelled"
        else:
            update = {"baseline": baseline["value"], "baseline_record_id": baseline["_id"], "target": target, "improvement_ratio": ratio}
            event = "target_changed"
            if target != challenge["target"]:
                update.update({"status": "pending", "accepted_at": None, "expires_at": now() + timedelta(days=7)})
            else:
                event = None
        db().challenges.update_one({"_id": challenge["_id"]}, {"$set": update}, session=session)
        if event:
            notify_challenge(challenge, event, session)


def correct_record(user, record_id, data, delete, session):
    record = db().records.find_one({"_id": record_id, "user_id": user["_id"]}, session=session)
    if not record:
        raise APIError("Record not found", 404)
    if not can_access_record(user, record, session):
        raise APIError("Premium required for older records", 403)
    variation = db().variations.find_one({"_id": record["variation_id"]}, session=session)
    if not variation:
        raise APIError("Variation not found", 404)
    # A shared write serializes mutations for this owner, including competing
    # corrections in separate groups, without relying on read-only snapshots.
    db().users.update_one({"_id": user["_id"]}, {"$inc": {"record_revision": 1}}, session=session)
    changes = {}
    if not delete:
        unknown = set(data) - {"value", "performed_at", "is_private", "challenge_id", "challenge_target", "challenge_decision"}
        if unknown:
            raise APIError("Only value, performed_at and is_private can be edited")
        if "value" in data:
            changes["value"] = number(data["value"], "value", integer=record["kind"] in ("calisthenic", "cardio"))
        if "is_private" in data:
            changes["is_private"] = boolean(data, "is_private")
        if "performed_at" in data:
            changed_date = timestamp(data["performed_at"])
            group = {"user_id": user["_id"], "variation_id": record["variation_id"], "distance_m": record.get("distance_m")}
            earlier = db().records.find_one({**group, "$or": [{"performed_at": {"$lt": record["performed_at"]}}, {"performed_at": record["performed_at"], "_id": {"$lt": record_id}}]}, sort=[("performed_at", DESCENDING), ("_id", DESCENDING)], session=session)
            later = db().records.find_one({**group, "$or": [{"performed_at": {"$gt": record["performed_at"]}}, {"performed_at": record["performed_at"], "_id": {"$gt": record_id}}]}, sort=[("performed_at", ASCENDING), ("_id", ASCENDING)], session=session)
            if (earlier and changed_date < earlier["performed_at"]) or (later and changed_date > later["performed_at"]):
                raise APIError("performed_at must stay between adjacent records")
            changes["performed_at"] = changed_date
        active = db().challenges.find_one({"challenged_id": user["_id"], "variation_id": record["variation_id"], "distance_m": record.get("distance_m"), "active": True, "expires_at": {"$gt": now()}}, session=session)
        proposed = {**record, **changes}
        if active and active.get("baseline_record_id") != record_id:
            apply_challenge_decision(user, proposed, data, session)
            if proposed.get("challenge_id") != record.get("challenge_id"):
                changes["challenge_id"] = proposed["challenge_id"]
    if delete:
        db().records.delete_one({"_id": record_id}, session=session)
    elif changes:
        db().records.update_one({"_id": record_id}, {"$set": changes}, session=session)
        record.update(changes)
    recalculate_bests(user["_id"], variation, record.get("distance_m"), session)
    reconcile_challenges(record, variation, delete, changes, session)
    return db().records.find_one({"_id": record_id}, session=session) if not delete else None
