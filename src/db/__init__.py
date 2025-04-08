# src/db/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'

    db.init_app(app)
    jwt.init_app(app)

    # Registrar los blueprints aquí
    # from .routes import loginroutes, weightedroutes, calisthenicroutes, cardioroutes
    # app.register_blueprint(loginroutes.bp)
    # app.register_blueprint(weightedroutes.bp)
    # app.register_blueprint(calisthenicroutes.bp)
    # app.register_blueprint(cardioroutes.bp)
    
    return app
