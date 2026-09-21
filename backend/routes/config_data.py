# routes/config_data.py
import time
import os
import json
from flask import Blueprint, request, jsonify

config_bp = Blueprint("config_bp", __name__)
DELAY = 1

# Pfad zur Konfigurationsdatei
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RELATIVE_CONFIG_PATH = "../configData.json"
config_path = os.path.abspath(os.path.join(BASE_DIR, RELATIVE_CONFIG_PATH))

# Lade Konfigurationsdaten
with open(config_path) as file:
    configData_dict = json.load(file)


@config_bp.route("/", methods=['GET', 'OPTIONS'], strict_slashes=False)
def handle_config_data():
    if request.method == 'GET':
        time.sleep(DELAY)
        return jsonify(configData_dict)

    elif request.method == 'OPTIONS':
        response = jsonify({"message": "Allowed methods: GET"})
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response, 200
