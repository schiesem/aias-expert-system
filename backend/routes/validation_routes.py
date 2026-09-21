# routes/validation_routes.py

import json
import os
import re
import rdflib
from flask import Blueprint, jsonify
from pyshacl import validate
from owlready2 import sync_reasoner_pellet, Imp

from app_globals import get_ontology_manager, get_current_world_id, get_world_manager
from expert_system.rule_base import get_rule_base_path, get_world_rule_path
from expert_system.modules.rule_utils import (
    load_swrl_rules_from_file,
    expand_swrl_rules,
    parse_reasoner_output,
    build_swrl_namespace_dict
)
from expert_system.modules.sparql_validator import SPARQLValidator
from expert_system.modules.rule_manager import RuleManager

# Global rule base path (fallback/template)
GLOBAL_RULE_DIR = get_rule_base_path()
SHACL_CONSISTENCY_FILE = "shacl_rules_consistency.ttl"
SHACL_NOTES_FILE = "shacl_rules_notes.ttl"
SWRL_FILE = "swrl_rules.txt"

def get_rule_paths():
    """Get rule paths for the current world."""
    try:
        world_id = get_current_world_id()
        world_manager = get_world_manager()
        world_paths = world_manager.get_world_paths(world_id)

        return {
            "shacl_consistency": world_paths["shacl_consistency"],
            "shacl_notes": world_paths["shacl_notes"],
            "swrl_rules": world_paths["swrl_rules"]
        }
    except Exception as e:
        print(f"⚠️ Could not get world-specific rules, falling back to global: {e}")
        # Fallback to global rules
        return {
            "shacl_consistency": os.path.join(GLOBAL_RULE_DIR, SHACL_CONSISTENCY_FILE),
            "shacl_notes": os.path.join(GLOBAL_RULE_DIR, SHACL_NOTES_FILE),
            "swrl_rules": os.path.join(GLOBAL_RULE_DIR, SWRL_FILE)
        }

validation_bp = Blueprint("validation_bp", __name__)


def replace_iris_with_prefixes(namespace_dict, parsed_reasoner_log):
    """
    Replace IRIs with prefixes in the reasoner output.
    """
    iri_to_prefix = {}

    # IRI -> Prefix Mapping for web IRIs
    for prefix, iri in namespace_dict.items():
        iri_clean = iri.rstrip('#/')
        iri_to_prefix[iri_clean] = prefix

    # Additional: cover local path variants
    for prefix, path in namespace_dict.items():
        if os.path.isabs(path):
            iri_to_prefix[path] = prefix

    def replace_iri_in_string(s):
        for iri, prefix in sorted(iri_to_prefix.items(), key=lambda x: -len(x[0])):
            # Web IRIs: http://.../AIAS#Resource -> AIAS.Resource
            s = re.sub(re.escape(iri) + r'[#/\\]+([A-Za-z0-9_]+)', rf'{prefix}.\1', s)
            # Local file paths
            s = re.sub(re.escape(iri) + r'[\\/]+([A-Za-z0-9_]+)', rf'{prefix}.\1', s)
        return s

    replaced_log = {}
    for key, value in parsed_reasoner_log.items():
        if isinstance(value, list):
            replaced_log[key] = [replace_iri_in_string(v) for v in value]
        elif isinstance(value, str):
            replaced_log[key] = replace_iri_in_string(value)
        else:
            replaced_log[key] = value

    return replaced_log


@validation_bp.route("/consistency", methods=['GET'])
def validate_consistency():
    """
    Run SHACL validation on the current world's AIAS-instance.owl.

    Workflow:
    1. Get world-aware ontology manager
    2. Ensure AIAS-instance.owl is loaded
    3. Convert ontology to RDFlib graph
    4. Load SHACL shapes
    5. Run pyshacl validation
    6. Extract violations
    7. Return violations

    Returns:
        JSON with status, conforms flag, and violations list
    """
    print("\n" + "="*60)
    print("✅ CONSISTENCY VALIDATION ENDPOINT CALLED")
    print("="*60)

    try:
        # Step 1: Get world-aware ontology manager
        from app_globals import get_current_world_id

        manager = get_ontology_manager()
        world_id = get_current_world_id()
        print(f"📂 Using world: {world_id}")
        print(f"📂 Instance file: {manager.instance_path}")

        # Step 2: Ensure instance ontology is loaded
        if manager.ontology is None:
            print("⚠️  Instance ontology not loaded, loading now...")
            manager.load_from_working_copy()

        print(f"✅ Instance ontology loaded: {manager.ontology}")

        # Step 3: Convert ontology to RDFlib graph
        print("\n🔄 Converting ontology to RDFlib graph...")

        # Save ontology to temporary RDF/XML format for RDFlib
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.owl', delete=False) as tmp_file:
            temp_path = tmp_file.name

        manager.ontology.save(temp_path, format="rdfxml")

        data_graph = rdflib.Graph()
        data_graph.parse(temp_path, format="xml")

        # Clean up temp file
        os.unlink(temp_path)

        print(f"✅ RDFlib graph created with {len(data_graph)} triples")

        # Step 4: Load SHACL shapes (world-specific)
        rule_paths = get_rule_paths()
        shacl_consistency_path = rule_paths["shacl_consistency"]
        print(f"\n📖 Loading SHACL consistency shapes from: {shacl_consistency_path}")

        if not os.path.exists(shacl_consistency_path):
            return jsonify({
                "status": "error",
                "message": f"SHACL consistency rules file not found: {shacl_consistency_path}"
            }), 404

        shapes_graph = rdflib.Graph()
        shapes_graph.parse(shacl_consistency_path, format="turtle")
        print(f"✅ SHACL shapes loaded with {len(shapes_graph)} triples")

        # Step 5: Run SHACL validation
        print("\n🔍 Running SHACL validation...")
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference='owlrl',
            abort_on_first=False,
            meta_shacl=False,
            debug=False
        )

        print(f"   Conforms: {conforms}")

        # Step 6: Extract violations
        violations = []
        for s in results_graph.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/shacl#ValidationResult")):
            message = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultMessage"))
            focus_node = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#focusNode"))
            result_path = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultPath"))
            severity = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultSeverity"))

            violations.append({
                "message": str(message) if message else "No message",
                "focusNode": str(focus_node) if focus_node else "Unknown",
                "resultPath": str(result_path) if result_path else "Unknown",
                "severity": str(severity) if severity else "http://www.w3.org/ns/shacl#Violation"
            })

        print(f"✅ Found {len(violations)} violations")

        # Cleanup
        data_graph = None
        shapes_graph = None

        return jsonify({
            "status": "success",
            "conforms": conforms,
            "violations": violations,
            "message": "No violations found" if conforms else f"Found {len(violations)} violations"
        })

    except Exception as e:
        print(f"❌ Error during consistency validation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@validation_bp.route("/notes", methods=['GET'])
def evaluate_notes():
    """
    Run SHACL validation for advisory notes on the current world's AIAS-instance.owl.

    This endpoint checks for conditions that should generate warnings/hints (notes)
    rather than hard violations. For example, checking if Inference is assigned to
    EdgeDevice should generate a note about latency/reliability.

    Workflow:
    1. Get world-aware ontology manager
    2. Ensure AIAS-instance.owl is loaded
    3. Convert ontology to RDFlib graph
    4. Load SHACL note shapes
    5. Run pyshacl validation
    6. Extract violations (displayed as "notes")
    7. Return violations as notes

    Returns:
        JSON with status, conforms flag, and violations (as notes) list
    """
    print("\n" + "="*60)
    print("📝 NOTES EVALUATION ENDPOINT CALLED")
    print("="*60)

    try:
        # Step 1: Get world-aware ontology manager
        from app_globals import get_current_world_id

        manager = get_ontology_manager()
        world_id = get_current_world_id()
        print(f"📂 Using world: {world_id}")
        print(f"📂 Instance file: {manager.instance_path}")

        # Step 2: Ensure instance ontology is loaded
        if manager.ontology is None:
            print("⚠️  Instance ontology not loaded, loading now...")
            manager.load_from_working_copy()

        print(f"✅ Instance ontology loaded: {manager.ontology}")

        # Step 3: Convert ontology to RDFlib graph
        print("\n🔄 Converting ontology to RDFlib graph...")

        # Save ontology to temporary RDF/XML format for RDFlib
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.owl', delete=False) as tmp_file:
            temp_path = tmp_file.name

        manager.ontology.save(temp_path, format="rdfxml")

        data_graph = rdflib.Graph()
        data_graph.parse(temp_path, format="xml")

        # Clean up temp file
        os.unlink(temp_path)

        print(f"✅ RDFlib graph created with {len(data_graph)} triples")

        # Step 4: Load SHACL note shapes (world-specific)
        rule_paths = get_rule_paths()
        shacl_notes_path = rule_paths["shacl_notes"]
        print(f"\n📖 Loading SHACL note shapes from: {shacl_notes_path}")

        if not os.path.exists(shacl_notes_path):
            return jsonify({
                "status": "error",
                "message": f"SHACL notes rules file not found: {shacl_notes_path}"
            }), 404

        shapes_graph = rdflib.Graph()
        shapes_graph.parse(shacl_notes_path, format="turtle")

        # Filter out deactivated shapes
        from rdflib.namespace import SH, RDF
        original_count = len(list(shapes_graph.subjects(RDF.type, SH.NodeShape)))
        deactivated_shapes = []

        for shape in shapes_graph.subjects(RDF.type, SH.NodeShape):
            for deactivated_value in shapes_graph.objects(shape, SH.deactivated):
                if str(deactivated_value).lower() == "true":
                    deactivated_shapes.append(shape)
                    break

        # Remove deactivated shapes and their related triples
        for shape in deactivated_shapes:
            # Remove all triples with this shape as subject
            for p, o in shapes_graph.predicate_objects(shape):
                shapes_graph.remove((shape, p, o))

        active_count = len(list(shapes_graph.subjects(RDF.type, SH.NodeShape)))
        print(f"✅ SHACL note shapes loaded: {original_count} total, {active_count} active, {len(deactivated_shapes)} deactivated")

        # Step 5: Run SHACL validation
        print("\n🔍 Running SHACL note validation...")
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference='owlrl',
            abort_on_first=False,
            meta_shacl=False,
            debug=False
        )

        print(f"   Conforms: {conforms}")

        # Step 6: Extract violations (displayed as notes)
        violations = []
        for s in results_graph.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/shacl#ValidationResult")):
            message = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultMessage"))
            focus_node = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#focusNode"))
            result_path = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultPath"))
            severity = results_graph.value(s, rdflib.URIRef("http://www.w3.org/ns/shacl#resultSeverity"))

            violations.append({
                "message": str(message) if message else "No message",
                "focusNode": str(focus_node) if focus_node else "Unknown",
                "resultPath": str(result_path) if result_path else "Unknown",
                "severity": str(severity) if severity else "http://www.w3.org/ns/shacl#Info"
            })

        print(f"✅ Found {len(violations)} SHACL notes")

        # Step 7: Execute SPARQL-based rules (Rules 19-28)
        print("\n🔍 Running SPARQL-based validation...")
        sparql_validator = SPARQLValidator(data_graph)
        sparql_notes = sparql_validator.validate_all()
        print(f"✅ Found {len(sparql_notes)} SPARQL notes")

        # Step 8: Combine SHACL and SPARQL results
        all_violations = violations + sparql_notes
        total_notes = len(all_violations)
        all_conforms = conforms and len(sparql_notes) == 0

        print(f"\n📊 Total notes: {total_notes} (SHACL: {len(violations)}, SPARQL: {len(sparql_notes)})")

        # Cleanup
        data_graph = None
        shapes_graph = None

        return jsonify({
            "status": "success",
            "conforms": all_conforms,
            "violations": all_violations,
            "message": "No notes" if all_conforms else f"Found {total_notes} notes"
        })

    except Exception as e:
        print(f"❌ Error during notes evaluation: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print("❌ Full traceback:")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}"
        }), 500


@validation_bp.route("/rules/catalog", methods=['GET'])
def get_rules_catalog():
    """
    Get all rules (SHACL and SPARQL) for the current world's rule catalog.

    Returns:
        JSON with all rules including their enabled/disabled state:
        {
            "status": "success",
            "rules": [
                {
                    "id": "AIAS:InferenceOnCloudSystemLatencyShape",
                    "name": "Rule 1: Inference on CloudSystem - Latency",
                    "message": "Bei der Inferenz auf einer externen Cloud...",
                    "type": "shacl",
                    "enabled": true
                },
                {
                    "id": "absence_checks.19",
                    "name": "Rule 19: Automate absence check",
                    "message": "Es fehlt eine Definition...",
                    "type": "sparql_absence",
                    "enabled": false
                },
                ...
            ]
        }
    """
    print("\n" + "="*60)
    print("📋 RULES CATALOG ENDPOINT CALLED")
    print("="*60)

    try:
        world_id = get_current_world_id()
        print(f"📂 Using world: {world_id}")

        # Initialize RuleManager for current world
        rule_manager = RuleManager(world_id)

        # Get all rules
        all_rules = rule_manager.get_all_rules()
        print(f"✅ Found {len(all_rules)} rules total")

        # Count by type
        shacl_count = len([r for r in all_rules if r["type"] == "shacl"])
        sparql_count = len([r for r in all_rules if r["type"].startswith("sparql")])
        print(f"   SHACL: {shacl_count}, SPARQL: {sparql_count}")

        return jsonify({
            "status": "success",
            "rules": all_rules,
            "total": len(all_rules)
        })

    except Exception as e:
        print(f"❌ Error fetching rules catalog: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@validation_bp.route("/rules/catalog/consistency", methods=['GET'])
def get_consistency_rules_catalog():
    """
    Get consistency rules (read-only) for the current world's rule catalog.

    Returns:
        JSON with all consistency rules (no enabled/disabled state):
        {
            "status": "success",
            "rules": [
                {
                    "id": "AIAS:ResourceShape",
                    "name": "Resource Communication Check",
                    "message": "Jede Resource muss mindestens eine hasCommunication-Beziehung haben.",
                    "type": "shacl_consistency"
                },
                ...
            ]
        }
    """
    print("\n" + "="*60)
    print("📋 CONSISTENCY RULES CATALOG ENDPOINT CALLED")
    print("="*60)

    try:
        world_id = get_current_world_id()
        print(f"📂 Using world: {world_id}")

        # Initialize RuleManager for current world
        rule_manager = RuleManager(world_id)

        # Get consistency rules
        consistency_rules = rule_manager.get_consistency_rules()
        print(f"✅ Found {len(consistency_rules)} consistency rules")

        return jsonify({
            "status": "success",
            "rules": consistency_rules,
            "total": len(consistency_rules)
        })

    except Exception as e:
        print(f"❌ Error fetching consistency rules catalog: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@validation_bp.route("/rules/catalog/swrl", methods=['GET'])
def get_swrl_rules_catalog():
    """
    Get SWRL rules (read-only) for the current world's rule catalog.

    Returns:
        JSON with all SWRL rules (no enabled/disabled state):
        {
            "status": "success",
            "rules": [
                {
                    "id": "swrl.1",
                    "name": "SWRL Rule 1",
                    "message": "AIAS:hasCommunication(?a, ?c), AIAS:hasCommunication(?b, ?c)...",
                    "type": "swrl"
                },
                ...
            ]
        }
    """
    print("\n" + "="*60)
    print("📋 SWRL RULES CATALOG ENDPOINT CALLED")
    print("="*60)

    try:
        world_id = get_current_world_id()
        print(f"📂 Using world: {world_id}")

        # Initialize RuleManager for current world
        rule_manager = RuleManager(world_id)

        # Get SWRL rules
        swrl_rules = rule_manager.get_swrl_rules()
        print(f"✅ Found {len(swrl_rules)} SWRL rules")

        return jsonify({
            "status": "success",
            "rules": swrl_rules,
            "total": len(swrl_rules)
        })

    except Exception as e:
        print(f"❌ Error fetching SWRL rules catalog: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@validation_bp.route("/rules/toggle", methods=['POST'])
def toggle_rule():
    """
    Toggle a rule on or off for the current world.

    Request body:
        {
            "rule_id": "AIAS:InferenceOnCloudSystemLatencyShape" or "absence_checks.19",
            "enabled": true or false
        }

    Returns:
        JSON with success status
    """
    print("\n" + "="*60)
    print("🔄 TOGGLE RULE ENDPOINT CALLED")
    print("="*60)

    try:
        from flask import request

        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400

        rule_id = data.get("rule_id")
        enabled = data.get("enabled")

        if rule_id is None or enabled is None:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: rule_id, enabled"
            }), 400

        world_id = get_current_world_id()
        print(f"📂 Using world: {world_id}")
        print(f"🔄 Toggling rule: {rule_id}")
        print(f"   Enabled: {enabled}")

        # Initialize RuleManager for current world
        rule_manager = RuleManager(world_id)

        # Toggle the rule
        success = rule_manager.toggle_rule(rule_id, enabled)

        if not success:
            return jsonify({
                "status": "error",
                "message": f"Failed to toggle rule: {rule_id}"
            }), 500

        return jsonify({
            "status": "success",
            "message": f"Rule {'enabled' if enabled else 'disabled'} successfully",
            "rule_id": rule_id,
            "enabled": enabled
        })

    except Exception as e:
        print(f"❌ Error toggling rule: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
