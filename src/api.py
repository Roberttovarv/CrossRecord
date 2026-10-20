"""API blueprint and error handlers."""
from flask import Blueprint
from pymongo.errors import DuplicateKeyError

from .db.common import APIError, fail
from .db.routes.auth_routes import auth_api
from .db.routes.challenges_routes import challenges_api
from .db.routes.exercises_routes import exercises_api
from .db.routes.feed_routes import feed_api
from .db.routes.follow_routes import follow_api
from .db.routes.records_routes import records_api
from .db.routes.statistics_routes import statistics_api
from .db.routes.user_routes import user_api
from .db.routes.variations_routes import variations_api

api = Blueprint("api", __name__)


@api.errorhandler(APIError)
def api_error(error):
    return fail(error.message, error.status)


@api.errorhandler(DuplicateKeyError)
def duplicate(_error):
    return fail("A conflicting item already exists", 409)


for route_blueprint in (auth_api, user_api, follow_api, exercises_api, variations_api, records_api, statistics_api, challenges_api, feed_api):
    api.register_blueprint(route_blueprint)
