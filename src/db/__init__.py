from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from .models import db
from .routes.auth_routes import auth_api
from .routes.user_routes import user_api

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_api, url_prefix='/auth')
    app.register_blueprint(user_api, url_prefix='/user')
    
    return app
