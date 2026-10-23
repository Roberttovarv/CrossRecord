from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pymongo import ASCENDING

from ..common import APIError, number, out
from ..connection import db
from ..services.records import best, variation_for
from ..services.users import actor, public_record

statistics_api = Blueprint("statistics_api", __name__)


@statistics_api.get("/me/statistics")
@jwt_required()
def statistics():
    user = actor()
    if not user.get("premium"):
        raise APIError("Premium required", 403)
    variation = variation_for(request.args.get("variation_id"))
    distance = number(request.args.get("distance_m"), "distance_m") if variation["kind"] == "cardio" else None
    records = list(db().records.find({"user_id": user["_id"], "variation_id": variation["_id"], "distance_m": distance}).sort([("performed_at", ASCENDING), ("_id", ASCENDING)]))
    first = records[0]["value"] if records else None
    last = records[-1]["value"] if records else None
    change = (first - last if variation["kind"] == "cardio" else last - first) if records else None
    percentage = change / first * 100 if records else None
    return jsonify(variation_id=str(variation["_id"]), distance_m=distance, count=len(records), best=public_record(best(user["_id"], variation, distance)) if records else None, first=first, last=last, change=change, change_percentage=percentage, series=[{"date": out(r["performed_at"]), "value": r["value"]} for r in records])
