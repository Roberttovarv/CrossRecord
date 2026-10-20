import os

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

from .api import api
from .db.connection import create_indexes


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        MONGO_URI=os.environ.get("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        MONGO_DATABASE=os.environ.get("MONGO_DATABASE", "crossrecord"),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
    )
    if config:
        app.config.update(config)
    if not app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("JWT_SECRET_KEY must be configured")
    app.extensions["mongo_client"] = app.config.get("MONGO_CLIENT") or MongoClient(app.config["MONGO_URI"], tz_aware=True)
    app.extensions["mongo_db"] = app.extensions["mongo_client"][app.config["MONGO_DATABASE"]]
    JWTManager(app)
    app.register_blueprint(api, url_prefix="/api/v1")
    create_indexes(app.extensions["mongo_db"])

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Not found"), 404

    return app


if __name__ == "__main__":
    create_app().run()
