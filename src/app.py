from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os
from src.extensions import db
from flask_jwt_extended import JWTManager


from .db.routes.auth_routes import auth_api
from .db.routes.user_routes import user_api
from .db.routes.variations.calisthenic_variations_routes import calisthenic_variations_api
from .db.routes.variations.weighted_variations_routes import weighted_variations_api
from .db.routes.variations.cardio_variations_routes import cardio_variations_api
from .db.routes.exercises_routes import exercises_api
from .db.routes.follow_routes import follow_api
from .db.routes.records.calisthenic_records_routes import calisthenic_records_api
from .db.routes.records.cardio_records_routes import cardio_records_api
from .db.routes.records.weighted_records_routes import weighted_records_api


jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    base_dir = os.path.abspath(os.path.dirname(__file__))

    db_path = os.path.join(base_dir, 'instance', 'mi_base.db')

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'tu_clave_secreta_super_segura'


    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(auth_api)
    app.register_blueprint(user_api)
    app.register_blueprint(calisthenic_variations_api)
    app.register_blueprint(weighted_variations_api)
    app.register_blueprint(cardio_variations_api)
    app.register_blueprint(exercises_api)
    app.register_blueprint(follow_api)
    app.register_blueprint(cardio_records_api)
    app.register_blueprint(calisthenic_records_api)
    app.register_blueprint(weighted_records_api)

    from .db.models import user_models, calisthenic_models, cardio_models, weighted_models, challenge_models, user_follows_models
    from .db.routes import auth_routes, calisthenic_variations_routes, exercises_routes, user_routes, weighted_variations_routes

    jwt.init_app(app)       
    @app.route('/')
    def sitemap():
        return '<h1>Hola</h1>'

    with app.app_context():
        db.create_all()

    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
