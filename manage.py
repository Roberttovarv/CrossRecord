from src.app import create_app
from src.extensions import db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)
