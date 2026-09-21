# routes/ontology_config.py
import time
from flask import Blueprint, request, jsonify
from expert_system.modules.ontology_manager import OntologyManager

# import des globalen ontology config store
from data_store import onto_config_store

ontology_bp = Blueprint("ontology_bp", __name__)
DELAY = 1

@ontology_bp.route("/", methods=['GET', 'OPTIONS'], strict_slashes=False)
def handle_ontology_config():
    if request.method == 'GET':
        time.sleep(DELAY)

        try:
            # Ontologie laden
            ontoManager = OntologyManager()
            ontoManager.load_ontologie()
            hierarchy = ontoManager.get_class_hierarchy()

            # Prüfen, ob die Schlüssel existieren
            #functions = hierarchy.get("Function", {}).get("Function", [])
            functions = hierarchy.get("Function", [])
            # Process and ProcessOperator are now properly subclasses of Function
            # No need to move Process anymore since it's already under Function in the ontology
            resources = hierarchy.get("Component", [])
            relations = hierarchy.get("Relation", [])

            # DataStore aktualisieren
            onto_config_store.update({
                "Functions": functions,
                "Resources": resources,
                "Relations": relations
            })

            ontoManager.unload_ontologie()  # Entladen der Ontologie
            
            return jsonify(onto_config_store.get())

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'OPTIONS':
        response = jsonify({"message": "Allowed methods: GET"})
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response, 200
