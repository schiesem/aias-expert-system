import os, json, time, rdflib
from flask import Blueprint, jsonify, request
from pyshacl import validate
from expert_system.modules.ontology_manager import OntologyManager
from expert_system.modules.graph_plot import create_pyviy_network_plot
from expert_system.rule_base import get_rule_base_path
from data_store import DataStore
from io import BytesIO

DELAY = 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DATA_DIR = os.path.join(BASE_DIR,"../received_data")

RULE_DIR = get_rule_base_path()
SHACLE_FILE = "shacl_rules.ttl"
SHACL_RULE_PATH = os.path.join(RULE_DIR, SHACLE_FILE)

rule_data_store = DataStore()
local_receive_storing = True
local_ontology_storing = True

rule_bp = Blueprint("rule_bp", __name__)
@rule_bp.route("/", methods=['POST', 'OPTIONS'], strict_slashes=False)
def handle_rule_base():

    if request.method == 'POST':
        time.sleep(DELAY)
        received_data = request.get_json(force=True)
        print("Empfangene Daten:", received_data)

        try:
            rule_data_store.update(received_data)

            if local_receive_storing == True:
                with open(os.path.join(RECEIVED_DATA_DIR,"rule_data_store.json"), "w", encoding="utf-8") as file:
                    json.dump(rule_data_store.get(), file, ensure_ascii=False, indent=4)
        
            manager = OntologyManager()
            manager.load_ontologie()
            nodes, edges = manager.instantiate_nodes(rule_data_store.get())
            properties = manager.instantiate_properties(rule_data_store.get(), nodes, edges)

            if local_ontology_storing == True:
                manager.save_ontology(file_path=RECEIVED_DATA_DIR, name="rule_ontology", format="rdfxml")

            byte_stream = manager.save_ontology_byteStream(format="rdfxml")

            # Lade die Ontologie als rdflib-Graph
            data_graph = rdflib.Graph()
            #data_graph.parse(os.path.join(manager.folder_path, "ontology_recieved.rdfxml"), format="xml") # diese Variante funktioniert, wenn man lokal speichert.
            data_graph.parse(byte_stream, format="xml")  # Parse die Ontologie direkt aus dem ByteStream

            # Lade SHACL-Shapes
            shapes_graph = rdflib.Graph()
            shapes_graph.parse(SHACL_RULE_PATH, format="turtle")

            # SHACL-Validierung
            conforms, results_graph, results_text = validate(
                data_graph,
                shacl_graph=shapes_graph,
                inference='owlrl',
                abort_on_first=False,
                meta_shacl=False,
                debug=False
            )

            # SHACL-Fehler extrahieren
            violations = {}
            i = 1
            for s in results_graph.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/shacl#ValidationResult")):
                message = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultMessage"))
                focus_node = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#focusNode"))
                result_path = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultPath"))
                severity = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultSeverity"))

                violations[f"violation_{i}"] = {
                    "message": str(message) if message else None,
                    "focusNode": str(focus_node) if focus_node else None,
                    "resultPath": str(result_path) if result_path else None,
                    "severity": str(severity) if severity else None
                }
                i += 1

            create_pyviy_network_plot(manager.get_ontology())

            manager.unload_ontologie()
            rule_data_store.clear()
            data_graph = None
            shapes_graph = None
            byte_stream = None

            return jsonify({
                "message": "Regeln erfolgreich ausgewertet:",
                "payload": violations
            })

        except Exception as e:
            return jsonify({"Fehler": str(e)}), 500


    elif request.method == 'OPTIONS':
        response = jsonify({"message": "Allowed methods: POST"})
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200