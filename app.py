from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configura tu base de datos (por ejemplo, SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mi_base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de ejemplo
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

@app.route('/')
def home():
    return "¡API funcionando!"

if __name__ == '__main__':
    # Crear las tablas antes de levantar el servidor
    with app.app_context():
        db.create_all()
    app.run(debug=True)
