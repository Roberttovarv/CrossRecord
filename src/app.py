from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from .db.routes import cardio_variations_routes
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    base_dir = os.path.abspath(os.path.dirname(__file__))

    db_path = os.path.join(base_dir, 'instance', 'mi_base.db')

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)


    from .db.models import user_models, calisthenic_models, cardio_models, weighted_models, challenge_models, user_exercise_models, user_follows_models
    from .db.routes import auth_routes, calisthenic_variations_routes, exercises_routes, user_routes, weighted_variations_routes
        
    @app.route('/')
    def sitemap():
        return '<h1>Hola</h1>'

    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
