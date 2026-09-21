# routes/reasoning.py

import json
from flask import Blueprint, jsonify
from app_globals import get_ontology_manager, get_current_world_id, get_world_manager
from expert_system.modules.graph_plot import create_pyviy_network_plot
from expert_system.rule_base import get_rule_base_path, get_world_rule_path
from expert_system.modules.rule_utils import (
    load_swrl_rules_from_file,
    expand_swrl_rules,
    parse_reasoner_output,
    build_swrl_namespace_dict
)
from owlready2 import Imp
# Angepasste Fassung des Pellet-Aufrufs: Sie liefert das Protokoll des
# Reasoners als Rueckgabewert zurueck (Parameter report), damit die
# abgeleiteten Fakten in der Oberflaeche angezeigt werden koennen.
from expert_system.reasoning import sync_reasoner_pellet
import re
import os

# Global rule base path (fallback)
GLOBAL_RULE_DIR = get_rule_base_path()
SWRL_FILE = "swrl_rules.txt"

def get_swrl_rule_path():
    """Get SWRL rule path for the current world."""
    try:
        world_id = get_current_world_id()
        world_manager = get_world_manager()
        world_paths = world_manager.get_world_paths(world_id)
        return world_paths["swrl_rules"]
    except Exception as e:
        print(f"⚠️ Could not get world-specific SWRL rules, falling back to global: {e}")
        return os.path.join(GLOBAL_RULE_DIR, SWRL_FILE)

def replace_iris_with_prefixes(namespace_dict, parsed_reasonner_log):
    """
    Replace IRIs with prefixes in the reasoner output.
    (Copied from store_recieve.py for consistency)
    """
    iri_to_prefix = {}

    # IRI -> Prefix Mapping, für Web-IRIs (z. B. http://...)
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
            # Web-IRIs ersetzen: z. B. http://.../AIAS#Resource -> AIAS.Resource
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


reasoning_bp = Blueprint("reasoning_bp", __name__)

@reasoning_bp.route("/run_reasoner", methods=['GET'])
def run_reasoner():
    """
    Run reasoning on the inferred ontology.

    Workflow:
    1. Check if instance ontology exists
    2. Copy instance → inferred
    3. Load inferred ontology
    4. Apply SWRL rules
    5. Run reasoner (Pellet)
    6. Save inferred ontology
    7. Generate inferred graph visualization
    8. Return reasoning results
    """
    print("\n" + "="*60)
    print("🧠 REASONING ENDPOINT CALLED")
    print("="*60)

    try:
        # Get the global world-aware ontology manager singleton
        manager = get_ontology_manager()

        # Step 1: Prepare for reasoning (copy instance → inferred)
        print("\n📋 Step 1: Preparing for reasoning...")
        if not manager.prepare_for_reasoning():
            return jsonify({
                "status": "error",
                "message": "Failed to prepare for reasoning. Instance ontology may not exist."
            }), 500

        # Step 2: Load inferred ontology
        print("\n📂 Step 2: Loading inferred ontology...")
        if not manager.load_inferred_ontology():
            return jsonify({
                "status": "error",
                "message": "Failed to load inferred ontology"
            }), 500

        # Step 3: Load and apply SWRL rules (world-specific)
        print("\n📜 Step 3: Loading SWRL rules...")
        try:
            swrl_rule_path = get_swrl_rule_path()
            print(f"   Loading from: {swrl_rule_path}")
            swrl_rules = load_swrl_rules_from_file(swrl_rule_path)
            print(f"   Loaded {len(swrl_rules)} SWRL rules")

            namespaces_dict = manager.get_ontology().world.ontologies.keys()
            namespaces = build_swrl_namespace_dict(namespaces_dict)

            expanded_swrl_rules = expand_swrl_rules(swrl_rules, namespaces)
            print(f"   Expanded to {len(expanded_swrl_rules)} rules")

            # Apply rules to ontology
            with manager.ontology:
                for rule_str in expanded_swrl_rules:
                    try:
                        rule = Imp()
                        rule.set_as_rule(rule_str)
                        print(f"   ✅ Rule applied: {rule_str[:50]}...")
                    except Exception as e:
                        print(f"   ⚠️ Rule failed: {rule_str[:50]}... - {e}")

        except Exception as e:
            print(f"❌ Error loading SWRL rules: {e}")
            return jsonify({
                "status": "error",
                "message": f"Failed to load SWRL rules: {str(e)}"
            }), 500

        # Step 4: Run reasoner
        print("\n🔬 Step 4: Running Pellet reasoner...")
        try:
            reasoner_log = sync_reasoner_pellet(
                manager.ontology,
                infer_property_values=True,
                infer_data_property_values=True,
                debug=0,
                report=1
            )

            parsed_reasoner_log = parse_reasoner_output(reasoner_log)
            result_log = replace_iris_with_prefixes(namespaces, parsed_reasoner_log)

            print(f"   ✅ Reasoning completed")
            print(f"   Inferences found: {len(result_log.get('AddRelation', []))} AddRelation, {len(result_log.get('Equivalenting', []))} Equivalenting, {len(result_log.get('Reparenting', []))} Reparenting")

        except Exception as e:
            print(f"❌ Error running reasoner: {e}")
            return jsonify({
                "status": "error",
                "message": f"Reasoner failed: {str(e)}"
            }), 500

        # Step 5: Save inferred ontology
        print("\n💾 Step 5: Saving inferred ontology...")
        if not manager.save_inferred_ontology():
            print("⚠️ Warning: Failed to save inferred ontology")

        # Step 6: Generate inferred graph visualization (in world-specific folder)
        print("\n🎨 Step 6: Generating inferred graph visualization...")
        try:
            from app_globals import get_world_manager, get_current_world_id

            world_mgr = get_world_manager()
            world_id = get_current_world_id()
            world_dir = world_mgr._get_world_dir(world_id)

            create_pyviy_network_plot(
                manager.get_ontology(),
                templates_path=world_dir,
                graph_type='inferred'
            )
            print("   ✅ Inferred graph generated in world folder")
        except Exception as e:
            print(f"⚠️ Warning: Failed to generate graph: {e}")

        # Step 7: Cleanup and reload instance ontology
        print("\n🧹 Step 7: Cleaning up and reloading instance ontology...")
        manager.unload_ontologie()

        # Reload the instance ontology so frontend can continue working
        # IMPORTANT: Use load_from_working_copy() NOT load_ontologie()
        # load_ontologie() would overwrite AIAS-instance.owl with a fresh copy!
        print("📂 Reloading AIAS-instance.owl for continued modeling...")
        manager.load_from_working_copy()
        print("✅ Instance ontology reloaded")

        print("\n" + "="*60)
        print("✅ REASONING COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")

        return jsonify({
            "status": "success",
            "message": "Reasoning completed successfully",
            "inferences": result_log
        }), 200

    except Exception as e:
        print(f"\n❌ REASONING FAILED: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": f"Unexpected error during reasoning: {str(e)}"
        }), 500
