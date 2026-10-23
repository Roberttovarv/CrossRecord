import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

from .api import api
from .db.connection import create_indexes


# Local development configuration only. Hosted environments provide their own
# variables and therefore take precedence over this ignored file.
load_dotenv(Path(__file__).resolve().parents[1] / ".env.local", override=False)


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        MONGO_URI=os.environ.get("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        MONGO_DATABASE=os.environ.get("MONGO_DATABASE", "crossrecord"),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
        RESEND_API_KEY=os.environ.get("RESEND_API_KEY"),
        RESEND_REGION=os.environ.get("RESEND_REGION", "eu-west-1"),
        MAIL_FROM=os.environ.get("MAIL_FROM"),
        FRONTEND_URL=os.environ.get("FRONTEND_URL", "http://localhost:3000"),
        REQUIRE_EMAIL_VERIFICATION=True,
    )
    if config:
        app.config.update(config)
    if not app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("JWT_SECRET_KEY must be configured")
    app.extensions["mongo_client"] = app.config.get("MONGO_CLIENT") or MongoClient(app.config["MONGO_URI"], tz_aware=True)
    app.extensions["mongo_db"] = app.extensions["mongo_client"][app.config["MONGO_DATABASE"]]
    if app.config.get("MAIL_SENDER"):
        app.extensions["mail_sender"] = app.config["MAIL_SENDER"]
    JWTManager(app)
    app.register_blueprint(api, url_prefix="/api/v1")
    create_indexes(app.extensions["mongo_db"])

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Not found"), 404

    return app


if __name__ == "__main__":
    create_app().run()
