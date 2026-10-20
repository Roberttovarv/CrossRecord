from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from ..common import APIError, body, boolean, fail, number, text_field
from ..connection import db, now
from ..services.users import private_user

auth_api = Blueprint("auth_api", __name__)


@auth_api.post("/auth/register")
def register():
    data = body()
    email = text_field(data, "email", 254).lower()
    username = text_field(data, "username", 20)
    password = text_field(data, "password", 128)
    if "@" not in email or len(password) < 8:
        raise APIError("Invalid email or password (minimum 8 characters)")
    user = {"email": email, "email_key": email.casefold(), "username": username, "username_key": username.casefold(), "password_hash": generate_password_hash(password), "name": text_field(data, "name", 50), "last_name": text_field(data, "last_name", 50), "profile_picture": None, "profile_private": boolean(data, "profile_private", False), "weight": number(data["weight"], "weight") if data.get("weight") is not None else None, "premium": False, "is_admin": False, "created_at": now()}
    user["_id"] = db().users.insert_one(user).inserted_id
    return jsonify(user=private_user(user), access_token=create_access_token(identity=str(user["_id"]))), 201


@auth_api.post("/auth/login")
def login():
    data = body()
    user = db().users.find_one({"email_key": text_field(data, "email", 254).casefold()})
    password = data.get("password")
    if not user or not isinstance(password, str) or not check_password_hash(user["password_hash"], password):
        return fail("Invalid credentials", 401)
    return jsonify(user=private_user(user), access_token=create_access_token(identity=str(user["_id"])))
