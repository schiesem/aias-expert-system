# routes/case_eval.py
import os, json, time
from flask import Blueprint, request, jsonify
from data_store import DataStore
from expert_system.modules.ontology_manager import OntologyManager
from expert_system.modules.case_utils import get_class_instance_summary, query_instances_of, query_relations, compare_class_counts
from expert_system.case_base import get_case_base_path
from rdflib import Graph
import math

DELAY = 1  # Falls du das zentral managen willst, kannst du später auslagern

CASE_PATH = get_case_base_path()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DATA_DIR = os.path.join(BASE_DIR,"../received_data")

case_data_store = DataStore()
local_receive_storing = True
local_ontology_storing = True

case_bp = Blueprint("case_bp", __name__)
@case_bp.route("/", methods=['POST', 'OPTIONS'], strict_slashes=False)
def handle_case_base():

    if request.method == 'POST':
        time.sleep(DELAY)
        received_data = request.get_json(force=True)
        print("Empfangene Daten:", received_data)

        try:
            case_data_store.update(received_data)

            if local_receive_storing:
                with open(os.path.join(RECEIVED_DATA_DIR,"case_data_store.json"), "w", encoding="utf-8") as file:
                    json.dump(case_data_store.get(), file, ensure_ascii=False, indent=4)

            # 1. Hauptontologie instanziieren
            manager = OntologyManager()
            manager.load_ontologie()
            nodes, edges = manager.instantiate_nodes(case_data_store.get())
            properties = manager.instantiate_properties(case_data_store.get(), nodes, edges)

            graph_a = manager.convert_to_rdflib()

            if local_ontology_storing:
                manager.save_ontology(file_path=RECEIVED_DATA_DIR, name="case_ontology", format="rdfxml")

            # 2. Alle RDF-Case-Ontologien im Zielordner durchlaufen
            case_format = "rdfxml"

            case_files = [
                f for f in os.listdir(CASE_PATH)
                if f.endswith(f".{case_format}")
            ]

            cases_data = []

            for case_file in case_files:
                case_name = os.path.splitext(case_file)[0]
                print(f"\n📦 Verarbeite Fall-Ontologie: {case_name}.{case_format}")

                # OntologyManager pro Fall
                c_manager = OntologyManager()
                c_manager.load_ontologie(case_path=CASE_PATH, case_name=case_name, case_format=case_format)
                graph_c = c_manager.convert_to_rdflib()

                ######### HIER KOMMEN DIE VERGLEICHE ###############
                # Analyse: Vergleich bestimmter Klassen
                compare_class_result = compare_class_counts(graph_a, graph_c, "http://www.semanticweb.org/schieseck/AIAS#Resource")

                # Nur falls eq_value eine Zahl ist → vergleichen
                if isinstance(compare_class_result["eq_value"], (int, float)) and math.isclose(compare_class_result["eq_value"], 1.0, rel_tol=1e-2):
                    compare_class_result["case_name"] = case_name
                    cases_data.append(compare_class_result)

                ######### HIER KOMMEN DIE VERGLEICHE ###############

                c_manager.unload_ontologie()
                c_manager = None
            
            manager.unload_ontologie()


            return jsonify({
                "message": "Fälle erfolgreich durchsucht:",
                "payload": cases_data
            }), 200

        except Exception as e:
            return jsonify({"Fehler": str(e)}), 500

    elif request.method == 'OPTIONS':
        response = jsonify({"message": "Allowed methods: POST"})
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
    



 