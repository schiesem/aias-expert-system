# routes/store_routes.py

import json, time, os, re
from flask import Blueprint, request, jsonify
from expert_system.modules.ontology_manager import OntologyManager
from expert_system.modules.graph_plot import create_pyviy_network_plot
from expert_system.rule_base import get_rule_base_path
from expert_system.modules.rule_utils import load_swrl_rules_from_file,expand_swrl_rules, parse_reasoner_output, build_swrl_namespace_dict
from owlready2 import sync_reasoner_pellet, Imp
from data_store import DataStore

from typing import List, Dict
DELAY = 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DATA_DIR = os.path.join(BASE_DIR,"../received_data")

RULE_DIR = get_rule_base_path()
SWRL_FILE = "swrl_rules.txt"
SWRL_RULE_PATH = os.path.join(RULE_DIR, SWRL_FILE)

import re
import os

def replace_iris_with_prefixes(namespace_dict, parsed_reasonner_log):
    iri_to_prefix = {}

    # IRI -> Prefix Mapping, für Web-IRIs (z. B. http://...)
    for prefix, iri in namespace_dict.items():
        iri_clean = iri.rstrip('#/')
        iri_to_prefix[iri_clean] = prefix

    # Zusätzlich: lokale Pfadvarianten abdecken
    for prefix, path in namespace_dict.items():
        if os.path.isabs(path):  # nur wenn es ein echter Dateipfad ist
            iri_to_prefix[path] = prefix

    def replace_iri_in_string(s):
        original = s
        for iri, prefix in sorted(iri_to_prefix.items(), key=lambda x: -len(x[0])):
            # Web-IRIs ersetzen: z. B. http://.../AIAS#Resource -> AIAS.Resource
            s = re.sub(re.escape(iri) + r'[#/\\]+([A-Za-z0-9_]+)', rf'{prefix}.\1', s)

            # Lokale Dateipfade wie ...\\AIAS.Resource -> AIAS.Resource
            s = re.sub(re.escape(iri) + r'[\\/]+([A-Za-z0-9_]+)', rf'{prefix}.\1', s)
        return s

    replaced_log = {}
    for key, value in parsed_reasonner_log.items():
        if isinstance(value, list):
            replaced_log[key] = [replace_iri_in_string(v) for v in value]
        elif isinstance(value, str):
            replaced_log[key] = replace_iri_in_string(value)
        else:
            replaced_log[key] = value

    return replaced_log


local_receive_storing = True
local_ontology_storing = True
data_store = DataStore()

store_recieve_bp = Blueprint("store_recieve_bp", __name__)
@store_recieve_bp.route("/", methods=['POST', 'OPTIONS'], strict_slashes=False)
def handle_store():

    if request.method == 'POST':
        time.sleep(DELAY)
        received_data = request.get_json(force=True)
        print("Empfangene Daten:", received_data)

        try:
            data_store.update(received_data)
        except ValueError as e:
            return jsonify({"Fehler": str(e)}), 400

        if local_receive_storing:
            with open(os.path.join(RECEIVED_DATA_DIR, "data_store_recieved.json"), "w", encoding="utf-8") as file:
                json.dump(data_store.get(), file, ensure_ascii=False, indent=4)

        manager = OntologyManager()
        manager.load_ontologie()
        nodes, edges = manager.instantiate_nodes(data_store.get())
        properties = manager.instantiate_properties(data_store.get(), nodes, edges)

        # Save the instance ontology (user model) - this is AIAS-instance.owl
        manager.save_ontology()  # Saves to default AIAS-instance.owl

        if local_ontology_storing:
            manager.save_ontology(file_path=RECEIVED_DATA_DIR, name="ontology_recieved", format="rdfxml")

        # Generate instance graph visualization (user model only, NO reasoning)
        create_pyviy_network_plot(manager.get_ontology(), graph_type='instance')

        # Clear inferred ontology since user model changed
        manager.clear_inferred_ontology()
        print("ℹ️ Inferred ontology cleared - reasoning results are now outdated")

        manager.unload_ontologie()

        return jsonify({
            "message": "Instance ontology updated successfully",
            "payload": {
                "nodes_created": len(nodes),
                "edges_created": len(edges),
                "note": "Run reasoning to generate inferences"
            }
        }), 200

    elif request.method == 'OPTIONS':
        response = jsonify({"message": "Allowed methods: POST, OPTIONS"})
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
