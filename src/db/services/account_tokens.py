from datetime import timedelta
from hashlib import sha256
from html import escape
from secrets import token_urlsafe
from urllib.parse import urlencode

from flask import current_app

from ..connection import db, now
from .email import send


def _hash(token):
    return sha256(token.encode()).hexdigest()


def issue(user, purpose):
    db().account_tokens.update_many({"user_id": user["_id"], "purpose": purpose, "used_at": None}, {"$set": {"used_at": now()}})
    token = token_urlsafe(32)
    db().account_tokens.insert_one({"user_id": user["_id"], "purpose": purpose, "token_hash": _hash(token), "created_at": now(), "expires_at": now() + timedelta(hours=1), "used_at": None})
    return token


def consume(token, purpose):
    return db().account_tokens.find_one_and_update(
        {"token_hash": _hash(token), "purpose": purpose, "used_at": None, "expires_at": {"$gt": now()}},
        {"$set": {"used_at": now()}},
    )


def send_link(user, purpose):
    token = issue(user, purpose)
    path = "verify-email" if purpose == "verify_email" else "reset-password"
    link = current_app.config["FRONTEND_URL"].rstrip("/") + "/" + path + "?" + urlencode({"token": token})
    title = "Verifica tu correo" if purpose == "verify_email" else "Restablece tu contraseña"
    send(user["email"], title + " · CrossRecord", "<p>" + title + "</p><p><a href=\"" + escape(link, quote=True) + "\">Continuar</a></p><p>El enlace caduca en una hora.</p>")
