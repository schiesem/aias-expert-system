"""
Rule Management Module

Handles reading, parsing, and modifying SHACL and SPARQL rules for world-specific rule catalogs.
Supports toggling rules on/off using SHACL's sh:deactivated property and custom disabled field.
"""

import json
import os
from typing import Dict, List, Tuple
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import SH, RDF


# Namespaces
AIAS = Namespace("http://www.semanticweb.org/schieseck/AIAS#")
ISO22989 = Namespace("http://www.semanticweb.org/schieseck/ISO22989#")
VDI3682 = Namespace("http://www.semanticweb.org/schieseck/VDI3682#")


class RuleManager:
    """Manages SHACL and SPARQL rules for a specific world."""

    def __init__(self, world_id: str):
        """
        Initialize RuleManager for a specific world.

        Args:
            world_id: World ID to manage rules for
        """
        self.world_id = world_id

        # Import here to avoid circular dependency
        from app_globals import get_world_manager
        world_manager = get_world_manager()
        world_paths = world_manager.get_world_paths(world_id)

        self.rules_dir = world_paths["rules_dir"]
        self.shacl_notes_path = os.path.join(self.rules_dir, "shacl_rules_notes.ttl")
        self.sparql_notes_path = os.path.join(self.rules_dir, "sparql_rules_notes.json")
        self.shacl_consistency_path = os.path.join(self.rules_dir, "shacl_rules_consistency.ttl")
        self.swrl_path = os.path.join(self.rules_dir, "swrl_rules.txt")

    # ======================================================================
    # SHACL Rule Methods
    # ======================================================================

    def get_shacl_rules(self) -> List[Dict]:
        """
        Parse SHACL TTL file and extract all rule shapes with their state.

        Returns:
            List of dicts with rule information:
            [
                {
                    "id": "AIAS:InferenceOnCloudSystemLatencyShape",
                    "name": "Rule 1: Inference on CloudSystem - Latency",
                    "message": "Bei der Inferenz auf einer externen Cloud...",
                    "type": "shacl",
                    "enabled": True
                },
                ...
            ]
        """
        if not os.path.exists(self.shacl_notes_path):
            print(f"⚠️ SHACL rules file not found: {self.shacl_notes_path}")
            return []

        rules = []
        g = Graph()
        g.parse(self.shacl_notes_path, format="turtle")

        # Find all NodeShapes
        for shape in g.subjects(RDF.type, SH.NodeShape):
            rule_info = self._extract_shacl_rule_info(g, shape)
            if rule_info:
                rules.append(rule_info)

        return rules

    def _extract_shacl_rule_info(self, graph: Graph, shape: URIRef) -> Dict:
        """
        Extract rule information from a SHACL shape.

        Args:
            graph: RDFlib graph containing the shape
            shape: URIRef of the shape

        Returns:
            Dict with rule info or None if extraction fails
        """
        from rdflib.namespace import RDFS

        # Get rule ID (last part of URI)
        rule_id = str(shape)

        # Try to extract name from rdfs:label
        rule_name = None
        for label in graph.objects(shape, RDFS.label):
            rule_name = str(label)
            break

        # Fallback: use the shape name itself
        if not rule_name:
            rule_name = rule_id.split("#")[-1] if "#" in rule_id else rule_id.split("/")[-1]

        # Check if deactivated
        enabled = True
        for deactivated_value in graph.objects(shape, SH.deactivated):
            if str(deactivated_value).lower() == "true":
                enabled = False
                break

        # Extract message from sh:message property
        message = ""

        # Check direct sh:message on shape
        for msg in graph.objects(shape, SH.message):
            message = str(msg)
            break

        # If no direct message, check sh:property > sh:message
        if not message:
            for prop in graph.objects(shape, SH.property):
                for msg in graph.objects(prop, SH.message):
                    message = str(msg)
                    break
                if message:
                    break

        # If no property message, check sh:sparql > sh:message
        if not message:
            for sparql_constraint in graph.objects(shape, SH.sparql):
                for msg in graph.objects(sparql_constraint, SH.message):
                    message = str(msg)
                    break
                if message:
                    break

        return {
            "id": rule_id,
            "name": rule_name,
            "message": message,
            "type": "shacl",
            "enabled": enabled
        }

    def toggle_shacl_rule(self, rule_id: str, enabled: bool) -> bool:
        """
        Toggle a SHACL rule by setting sh:deactivated property.

        Args:
            rule_id: Full URI of the rule shape (e.g., "AIAS:InferenceOnCloudSystemLatencyShape")
            enabled: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.shacl_notes_path):
            print(f"❌ SHACL rules file not found: {self.shacl_notes_path}")
            return False

        try:
            # Load graph
            g = Graph()
            g.parse(self.shacl_notes_path, format="turtle")

            # Find the shape
            shape_uri = URIRef(rule_id)

            # Check if shape exists
            if (shape_uri, RDF.type, SH.NodeShape) not in g:
                print(f"❌ Shape not found: {rule_id}")
                return False

            # Remove existing sh:deactivated statements
            g.remove((shape_uri, SH.deactivated, None))

            # Add new sh:deactivated statement (only if disabling)
            if not enabled:
                g.add((shape_uri, SH.deactivated, Literal(True)))

            # Save back to file
            g.serialize(destination=self.shacl_notes_path, format="turtle")

            print(f"✅ SHACL rule {'enabled' if enabled else 'disabled'}: {rule_id}")
            return True

        except Exception as e:
            print(f"❌ Error toggling SHACL rule {rule_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ======================================================================
    # SPARQL Rule Methods
    # ======================================================================

    def get_sparql_rules(self) -> List[Dict]:
        """
        Parse SPARQL JSON file and extract all rules with their state.

        Returns:
            List of dicts with rule information:
            [
                {
                    "id": "absence_checks.19",
                    "name": "Rule 19: Automate absence check",
                    "message": "Es fehlt eine Definition...",
                    "type": "sparql_absence",
                    "enabled": True
                },
                ...
            ]
        """
        if not os.path.exists(self.sparql_notes_path):
            print(f"⚠️ SPARQL rules file not found: {self.sparql_notes_path}")
            return []

        rules = []

        try:
            with open(self.sparql_notes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract absence checks
            if "absence_checks" in data:
                for rule_num, rule_data in data["absence_checks"].items():
                    enabled = not rule_data.get("disabled", False)
                    rules.append({
                        "id": f"absence_checks.{rule_num}",
                        "name": f"Rule {rule_num}: {rule_data.get('class', 'Unknown')} absence check",
                        "message": rule_data.get("message", ""),
                        "type": "sparql_absence",
                        "enabled": enabled
                    })

            # Extract complex rules
            if "complex_rules" in data:
                for rule_num, rule_data in data["complex_rules"].items():
                    enabled = not rule_data.get("disabled", False)
                    rules.append({
                        "id": f"complex_rules.{rule_num}",
                        "name": f"Rule {rule_num}: {rule_data.get('type', 'Unknown')}",
                        "message": rule_data.get("message", ""),
                        "type": "sparql_complex",
                        "enabled": enabled
                    })

            # Extract regulation rules
            if "regulation_rules" in data:
                for rule_num, rule_data in data["regulation_rules"].items():
                    enabled = not rule_data.get("disabled", False)
                    rules.append({
                        "id": f"regulation_rules.{rule_num}",
                        "name": f"EU AI Act Rule {rule_num}",
                        "message": rule_data.get("message", ""),
                        "type": "sparql_regulation",
                        "enabled": enabled
                    })

            return rules

        except Exception as e:
            print(f"❌ Error reading SPARQL rules: {e}")
            import traceback
            traceback.print_exc()
            return []

    def toggle_sparql_rule(self, rule_id: str, enabled: bool) -> bool:
        """
        Toggle a SPARQL rule by setting 'disabled' field in JSON.

        Args:
            rule_id: Rule ID in format "category.number" (e.g., "absence_checks.19")
            enabled: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.sparql_notes_path):
            print(f"❌ SPARQL rules file not found: {self.sparql_notes_path}")
            return False

        try:
            # Parse rule ID
            parts = rule_id.split(".")
            if len(parts) != 2:
                print(f"❌ Invalid rule ID format: {rule_id}")
                return False

            category, rule_num = parts

            # Load JSON
            with open(self.sparql_notes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find and update rule
            if category not in data:
                print(f"❌ Category not found: {category}")
                return False

            if rule_num not in data[category]:
                print(f"❌ Rule not found: {rule_num} in {category}")
                return False

            # Update disabled field
            data[category][rule_num]["disabled"] = not enabled

            # Save back to file
            with open(self.sparql_notes_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✅ SPARQL rule {'enabled' if enabled else 'disabled'}: {rule_id}")
            return True

        except Exception as e:
            print(f"❌ Error toggling SPARQL rule {rule_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ======================================================================
    # Consistency Rule Methods (Read-Only)
    # ======================================================================

    def get_consistency_rules(self) -> List[Dict]:
        """
        Parse SHACL consistency rules (read-only, always active).

        Returns:
            List of dicts with rule information:
            [
                {
                    "id": "AIAS:ResourceShape",
                    "name": "Resource Communication Check",
                    "message": "Jede Resource muss mindestens eine hasCommunication-Beziehung haben.",
                    "type": "shacl_consistency"
                },
                ...
            ]
        """
        if not os.path.exists(self.shacl_consistency_path):
            print(f"⚠️ SHACL consistency rules file not found: {self.shacl_consistency_path}")
            return []

        rules = []
        g = Graph()
        g.parse(self.shacl_consistency_path, format="turtle")

        # Find all NodeShapes
        for shape in g.subjects(RDF.type, SH.NodeShape):
            rule_info = self._extract_shacl_rule_info_readonly(g, shape, "shacl_consistency")
            if rule_info:
                rules.append(rule_info)

        return rules

    def _extract_shacl_rule_info_readonly(self, graph: Graph, shape: URIRef, rule_type: str) -> Dict:
        """
        Extract rule information from a SHACL shape (read-only version without enabled field).

        Args:
            graph: RDFlib graph containing the shape
            shape: URIRef of the shape
            rule_type: Type identifier for the rule

        Returns:
            Dict with rule info or None if extraction fails
        """
        from rdflib.namespace import RDFS

        # Get rule ID (last part of URI)
        rule_id = str(shape)

        # Try to extract name from rdfs:label
        rule_name = None
        for label in graph.objects(shape, RDFS.label):
            rule_name = str(label)
            break

        # Fallback: use the shape name itself
        if not rule_name:
            rule_name = rule_id.split("#")[-1] if "#" in rule_id else rule_id.split("/")[-1]

        # Extract message from sh:message property
        message = ""

        # Check direct sh:message on shape
        for msg in graph.objects(shape, SH.message):
            message = str(msg)
            break

        # If no direct message, check sh:property > sh:message
        if not message:
            for prop in graph.objects(shape, SH.property):
                for msg in graph.objects(prop, SH.message):
                    message = str(msg)
                    break
                if message:
                    break

        # If no property message, check sh:sparql > sh:message
        if not message:
            for sparql_constraint in graph.objects(shape, SH.sparql):
                for msg in graph.objects(sparql_constraint, SH.message):
                    message = str(msg)
                    break
                if message:
                    break

        return {
            "id": rule_id,
            "name": rule_name,
            "message": message,
            "type": rule_type
        }

    # ======================================================================
    # SWRL Rule Methods (Read-Only)
    # ======================================================================

    def get_swrl_rules(self) -> List[Dict]:
        """
        Parse SWRL rules from text file (read-only, always active).

        Returns:
            List of dicts with rule information:
            [
                {
                    "id": "swrl.1",
                    "name": "SWRL Rule 1",
                    "message": "AIAS:hasCommunication(?a, ?c), AIAS:hasCommunication(?b, ?c)...",
                    "type": "swrl"
                },
                ...
            ]
        """
        if not os.path.exists(self.swrl_path):
            print(f"⚠️ SWRL rules file not found: {self.swrl_path}")
            return []

        rules = []

        try:
            with open(self.swrl_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            rule_num = 1
            for line in lines:
                line = line.strip()
                # Skip empty lines
                if not line:
                    continue

                # Remove trailing quote if present
                rule_text = line.rstrip('"')

                rules.append({
                    "id": f"swrl.{rule_num}",
                    "name": f"SWRL Rule {rule_num}",
                    "message": rule_text,
                    "type": "swrl"
                })
                rule_num += 1

            return rules

        except Exception as e:
            print(f"❌ Error reading SWRL rules: {e}")
            import traceback
            traceback.print_exc()
            return []

    # ======================================================================
    # Combined Methods
    # ======================================================================

    def get_all_rules(self) -> List[Dict]:
        """
        Get all rules (SHACL + SPARQL) for the current world.

        Returns:
            Combined list of all rules with metadata
        """
        shacl_rules = self.get_shacl_rules()
        sparql_rules = self.get_sparql_rules()

        return shacl_rules + sparql_rules

    def toggle_rule(self, rule_id: str, enabled: bool) -> bool:
        """
        Toggle any rule (automatically detects SHACL vs SPARQL).

        Args:
            rule_id: Rule ID (full URI for SHACL, "category.number" for SPARQL)
            enabled: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        # Detect rule type by ID format
        if "." in rule_id and not rule_id.startswith("http"):
            # SPARQL rule (category.number format)
            return self.toggle_sparql_rule(rule_id, enabled)
        else:
            # SHACL rule (URI format)
            return self.toggle_shacl_rule(rule_id, enabled)
