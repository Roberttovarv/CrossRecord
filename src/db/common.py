from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from bson import ObjectId
from bson.errors import InvalidId
from flask import jsonify, request

from .connection import now


def fail(message, code=400):
    return jsonify(error=message), code


class APIError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status
def oid(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise APIError("Invalid identifier")


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError("A JSON object is required")
    return data


def text_field(data, name, max_length=100):
    value = data.get(name)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_length:
        raise APIError(f"Invalid {name}")
    return value.strip()


def boolean(data, name, default=False):
    value = data.get(name, default)
    if not isinstance(value, bool):
        raise APIError(f"{name} must be a boolean")
    return value


def number(value, name, integer=False):
    if isinstance(value, bool) or value is None:
        raise APIError(f"Invalid {name}")
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result <= 0 or result > Decimal("1000000000"):
            raise ValueError()
        if integer and result != result.to_integral_value():
            raise ValueError()
        if not integer and result.as_tuple().exponent < -2:
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise APIError(f"Invalid {name}")
    return int(result) if integer else float(result)


def timestamp(value):
    if value is None:
        return now()
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        result = result.astimezone(timezone.utc)
        if result > now() + timedelta(minutes=5):
            raise ValueError()
        return result
    except (ValueError, AttributeError):
        raise APIError("performed_at must be an ISO 8601 timestamp with timezone and not in the future")


def out(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, list):
        return [out(v) for v in value]
    if isinstance(value, dict):
        return {("id" if k == "_id" else k): out(v) for k, v in value.items()}
    return value
def pagination():
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        if not 1 <= limit <= 50 or offset < 0:
            raise ValueError()
        return limit, offset
    except ValueError:
        raise APIError("Invalid pagination")
