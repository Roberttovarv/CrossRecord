from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from ..common import APIError, body, boolean, fail, number, text_field
from ..connection import db, now
from ..services.account_tokens import consume, send_link
from ..services.users import actor, private_user

auth_api = Blueprint("auth_api", __name__)


@auth_api.post("/auth/register")
def register():
    data = body()
    email = text_field(data, "email", 254).lower()
    username = text_field(data, "username", 20)
    password = text_field(data, "password", 128)
    if "@" not in email or len(password) < 8:
        raise APIError("Invalid email or password (minimum 8 characters)")
    user = {"email": email, "email_key": email.casefold(), "username": username, "username_key": username.casefold(), "password_hash": generate_password_hash(password), "name": text_field(data, "name", 50), "last_name": text_field(data, "last_name", 50), "profile_picture": None, "profile_private": boolean(data, "profile_private", False), "weight": number(data["weight"], "weight") if data.get("weight") is not None else None, "premium": False, "is_admin": False, "email_verified": False, "session_version": 0, "created_at": now()}
    user["_id"] = db().users.insert_one(user).inserted_id
    send_link(user, "verify_email")
    return jsonify(user=private_user(user), access_token=create_access_token(identity=str(user["_id"]), additional_claims={"session_version": 0})), 201


@auth_api.post("/auth/login")
def login():
    data = body()
    user = db().users.find_one({"email_key": text_field(data, "email", 254).casefold()})
    password = data.get("password")
    if not user or not isinstance(password, str) or not check_password_hash(user["password_hash"], password):
        return fail("Invalid credentials", 401)
    if user.get("deactivated_at"):
        db().users.update_one({"_id": user["_id"]}, {"$set": {"deactivated_at": None}})
        user["deactivated_at"] = None
    return jsonify(user=private_user(user), access_token=create_access_token(identity=str(user["_id"]), additional_claims={"session_version": user.get("session_version", 0)}))


@auth_api.post("/auth/verify-email/request")
@jwt_required()
def request_verification():
    user = actor(allow_unverified=True)
    if not user.get("email_verified"):
        send_link(user, "verify_email")
    return jsonify(sent=True), 202


@auth_api.post("/auth/verify-email/confirm")
def confirm_verification():
    token = text_field(body(), "token", 512)
    item = consume(token, "verify_email")
    if not item:
        raise APIError("Invalid or expired token", 400)
    db().users.update_one({"_id": item["user_id"]}, {"$set": {"email_verified": True}})
    return jsonify(verified=True)


@auth_api.post("/auth/password-reset/request")
def request_password_reset():
    email = text_field(body(), "email", 254).casefold()
    user = db().users.find_one({"email_key": email})
    if user:
        send_link(user, "password_reset")
    return jsonify(sent=True), 202


@auth_api.post("/auth/password-reset/confirm")
def confirm_password_reset():
    data = body()
    token = text_field(data, "token", 512)
    password = text_field(data, "password", 128)
    if len(password) < 8:
        raise APIError("Invalid password (minimum 8 characters)")
    item = consume(token, "password_reset")
    if not item:
        raise APIError("Invalid or expired token", 400)
    db().users.update_one({"_id": item["user_id"]}, {"$set": {"password_hash": generate_password_hash(password)}, "$inc": {"session_version": 1}})
    return jsonify(reset=True)
