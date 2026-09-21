import os
import json
from flask import Blueprint, jsonify, abort, send_from_directory
from expert_system.case_base import get_case_base_path

case_routes = Blueprint("case_routes", __name__)

CASE_PATH = get_case_base_path()

# Route: Einzelner Case als JSON zum Download
@case_routes.route("/<case_name>", methods=["GET"])
def download_case_file(case_name):
    filename = f"{case_name}.json"
    file_path = os.path.join(CASE_PATH, filename)

    if not os.path.isfile(file_path):
        return abort(404, description="Fall nicht gefunden.")

    return send_from_directory(
        CASE_PATH,
        filename,
        as_attachment=True,
        mimetype='application/json'
    )

