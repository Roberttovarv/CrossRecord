from flask import Blueprint, request, jsonify
from models import db, CalisthenicExercises, CalisthenicExerciseVariations, CalisthenicRecord
from flask_jwt_extended import create_access_token
from flask_cors import CORS

calisthenic_api = Blueprint('calisthenic_api', __name__)

CORS(calisthenic_api)

@calisthenic_api.route('/calisthenic', method=['POST'])
def create_calisthenic():
    data = request.json

