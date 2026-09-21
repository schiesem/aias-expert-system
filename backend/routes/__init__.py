# routes/__init__.py
import os
import json
from .store_recieve import store_recieve_bp
from .rule_eval import rule_bp
from .case_eval import case_bp
from .onto_config import ontology_bp
from .config_data import config_bp
from .graph_view import graph_bp
from .main import main_bp

from .case_routes import case_routes
from .annotation_routes import annotation_bp
from .reasoning import reasoning_bp
from .model_routes import model_bp
from .world_routes import world_bp
from .graph_routes import graph_viz_bp
from .validation_routes import validation_bp
from .case_filter_routes import case_filter_bp

# Basisverzeichnis: Verzeichnis, in dem das aktuelle Skript liegt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RELATIVE_CONFIG_PATH = "../configData.json"

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), RELATIVE_CONFIG_PATH))
with open(config_path) as file:
    configData_dict = json.load(file)

def register_blueprints(app):
    app.register_blueprint(store_recieve_bp, url_prefix=configData_dict["routes"]["STORE"])
    app.register_blueprint(rule_bp, url_prefix=configData_dict["routes"]["RULE_BASE"])
    app.register_blueprint(case_bp, url_prefix=configData_dict["routes"]["CASE_BASE"])
    app.register_blueprint(ontology_bp, url_prefix=configData_dict["routes"]["ONTOLOGY_CONFIG"])
    app.register_blueprint(config_bp, url_prefix=configData_dict["routes"]["CONFIG_DATA"])
    app.register_blueprint(graph_bp, url_prefix=configData_dict["routes"]["GRAPH"])
    app.register_blueprint(main_bp, url_prefix=configData_dict["routes"]["MAIN"])
    app.register_blueprint(case_routes, url_prefix=configData_dict["routes"]["CASES"])
    app.register_blueprint(annotation_bp)  # Annotation routes have their own prefix defined
    app.register_blueprint(reasoning_bp, url_prefix=configData_dict["routes"]["REASONING"])
    app.register_blueprint(model_bp)  # Model routes have their own prefix defined (/api/model)
    app.register_blueprint(world_bp)  # World routes have their own prefix defined (/api/worlds)
    app.register_blueprint(graph_viz_bp)  # Graph visualization routes (/api/graph)
    app.register_blueprint(validation_bp, url_prefix=configData_dict["routes"]["VALIDATION"])
    app.register_blueprint(case_filter_bp, url_prefix="/api/case-filter")
