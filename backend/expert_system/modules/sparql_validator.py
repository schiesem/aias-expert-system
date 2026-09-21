# expert_system/modules/sparql_validator.py

import json
import os
from rdflib import Graph
from expert_system.rule_base import get_rule_base_path


class SPARQLValidator:
    """
    Validator for SPARQL-based rules that cannot be implemented in SHACL.

    Handles:
    - Rules 19-27: Absence checks (checking for NON-existence of classes)
    - Rule 28: Complex comparison (Training and Inference on different components)
    - Rules I-VI: Regulation rules (EU AI Act and GDPR compliance checks)
    """

    def __init__(self, data_graph: Graph):
        """
        Initialize SPARQL validator with an rdflib Graph.

        Args:
            data_graph: rdflib.Graph containing the ontology data
        """
        self.data_graph = data_graph
        self.rule_registry = self._load_rule_registry()
        self.namespaces = self.rule_registry.get("namespaces", {})

    def _load_rule_registry(self):
        """Load SPARQL rules from JSON file (world-specific)."""
        try:
            # Try to load world-specific rules
            from expert_system.rule_base import get_world_rule_path
            rule_dir = get_world_rule_path()
            registry_path = os.path.join(rule_dir, "sparql_rules_notes.json")
            print(f"📖 Loading SPARQL rules from world-specific path: {registry_path}")
        except Exception as e:
            # Fallback to global rules
            print(f"⚠️  Could not get world-specific SPARQL rules, using global: {e}")
            rule_dir = get_rule_base_path()
            registry_path = os.path.join(rule_dir, "sparql_rules_notes.json")

        if not os.path.exists(registry_path):
            print(f"⚠️  SPARQL rule registry not found: {registry_path}")
            return {"absence_checks": {}, "complex_rules": {}, "regulation_rules": {}, "namespaces": {}}

        with open(registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_all(self):
        """
        Execute all SPARQL-based validation rules.

        Returns:
            list: List of violation dictionaries
        """
        violations = []

        # Execute absence checks (Rules 19-27)
        violations.extend(self.validate_absence_checks())

        # Execute complex rules (Rule 28)
        violations.extend(self.validate_complex_rules())

        # Execute regulation rules (Rules I-VI)
        violations.extend(self.validate_regulation_rules())

        return violations

    def validate_absence_checks(self):
        """
        Execute Rules 19-27: Check for absence of specific classes.

        These rules trigger when NO instances of a class exist.

        Returns:
            list: List of violation dictionaries
        """
        violations = []
        absence_rules = self.rule_registry.get("absence_checks", {})

        for rule_id, rule_config in absence_rules.items():
            # Skip disabled rules
            if rule_config.get("disabled", False):
                continue

            class_name = rule_config["class"]
            message = rule_config["message"]

            result = self._check_absence(rule_id, class_name, message)
            if result:
                violations.append(result)

        print(f"   ✅ Absence checks completed: {len(violations)} notes triggered")
        return violations

    def validate_complex_rules(self):
        """
        Execute Rule 28: Check if Training and Inference are on different components.

        Returns:
            list: List of violation dictionaries
        """
        violations = []
        complex_rules = self.rule_registry.get("complex_rules", {})

        if "28" in complex_rules:
            rule_config = complex_rules["28"]
            # Skip disabled rules
            if rule_config.get("disabled", False):
                print(f"   ⏭️  Rule 28 is disabled, skipping")
            elif rule_config["type"] == "training_inference_comparison":
                violations.extend(self._check_training_inference_mismatch(rule_config["message"]))

        print(f"   ✅ Complex rules completed: {len(violations)} notes triggered")
        return violations

    def _check_absence(self, rule_id, class_name, message):
        """
        Check if NO instances of a class exist.

        Args:
            rule_id: Rule identifier (e.g., "19")
            class_name: Class name with prefix (e.g., "ISO22989:Automate")
            message: Message to display if class is absent

        Returns:
            dict: Violation dictionary if class is absent, None otherwise
        """
        # Build full class URI
        prefix, local_name = class_name.split(":")
        class_uri = self.namespaces.get(prefix, "") + local_name

        # Build ASK query to check if instances exist
        query = f"""
        ASK {{
            ?instance a <{class_uri}> .
        }}
        """

        try:
            has_instances = self.data_graph.query(query).askAnswer

            # INVERTED LOGIC: Trigger note when NO instances exist
            if not has_instances:
                return {
                    "message": f"[Rule {rule_id}] {message}",
                    "focusNode": "Ontology",
                    "resultPath": "N/A",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                }
        except Exception as e:
            print(f"   ⚠️  Error checking absence for rule {rule_id}: {e}")

        return None

    def _check_training_inference_mismatch(self, message):
        """
        Check if Training and Inference are assigned to different components (Rule 28).

        Pattern:
        - Find Training function assigned to component A
        - Find Inference function assigned to component B
        - If A ≠ B, trigger note

        Args:
            message: Message to display when mismatch is found

        Returns:
            list: List of violation dictionaries
        """
        query = f"""
        PREFIX ISO22989: <{self.namespaces.get('ISO22989', '')}>
        PREFIX AIAS: <{self.namespaces.get('AIAS', '')}>
        PREFIX VDI3682: <{self.namespaces.get('VDI3682', '')}>

        SELECT ?training ?inference ?trainComponent ?inferComponent
        WHERE {{
            # Training assigned to component A
            ?training a ISO22989:Training .
            ?training AIAS:isAssignedTo ?trainAssignment .
            ?trainAssignment a VDI3682:Assignment .
            ?trainComponent AIAS:isAssignedTo ?trainAssignment .

            # Inference assigned to component B
            ?inference a ISO22989:Inference .
            ?inference AIAS:isAssignedTo ?inferAssignment .
            ?inferAssignment a VDI3682:Assignment .
            ?inferComponent AIAS:isAssignedTo ?inferAssignment .

            # Filter: components must be different
            FILTER(?trainComponent != ?inferComponent)
        }}
        """

        violations = []

        try:
            results = list(self.data_graph.query(query))

            for row in results:
                violations.append({
                    "message": f"[Rule 28] {message}",
                    "focusNode": str(row.training),
                    "resultPath": f"Training: {str(row.trainComponent)}, Inference: {str(row.inferComponent)}",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                })
        except Exception as e:
            print(f"   ⚠️  Error checking training/inference mismatch: {e}")

        return violations

    def validate_regulation_rules(self):
        """
        Execute Rules I-VI: Regulation compliance checks (EU AI Act, GDPR).

        Returns:
            list: List of violation dictionaries
        """
        violations = []
        regulation_rules = self.rule_registry.get("regulation_rules", {})

        for rule_id, rule_config in regulation_rules.items():
            # Skip disabled rules
            if rule_config.get("disabled", False):
                continue

            rule_type = rule_config.get("type")
            message = rule_config["message"]

            if rule_type == "existence":
                # Rule I: Simple existence check
                result = self._check_existence(rule_id, rule_config["class"], message)
                if result:
                    violations.append(result)

            elif rule_type == "existence_or":
                # Rule II: Check if any of the classes exist (OR logic)
                result = self._check_existence_or(rule_id, rule_config["classes"], message)
                if result:
                    violations.append(result)

            elif rule_type == "complex_existence_absence":
                # Rule III: Check existence of some AND absence of others
                result = self._check_complex_existence_absence(
                    rule_id,
                    rule_config["existence_classes"],
                    rule_config["absence_classes"],
                    message
                )
                if result:
                    violations.append(result)

            elif rule_type == "inference_on_process_resources":
                # Rule IV: Check if Inference is on resources connected to ProcessOperator
                violations.extend(self._check_inference_on_process_resources(
                    rule_id,
                    rule_config["function_class"],
                    rule_config["resource_classes"],
                    rule_config["process_operator_class"],
                    message
                ))

            elif rule_type == "assignment_or":
                # Rules V, VI: Check if any function is assigned to component
                violations.extend(self._check_assignment_or(
                    rule_id,
                    rule_config["function_classes"],
                    rule_config["component_class"],
                    message
                ))

        print(f"   ✅ Regulation rules completed: {len(violations)} notes triggered")
        return violations

    def _check_existence(self, rule_id, class_name, message):
        """
        Check if instances of a class exist (trigger note when they DO exist).

        Args:
            rule_id: Rule identifier (e.g., "I")
            class_name: Class name with prefix (e.g., "ISO22989:AISystem")
            message: Message to display if class exists

        Returns:
            dict: Violation dictionary if class exists, None otherwise
        """
        prefix, local_name = class_name.split(":")
        class_uri = self.namespaces.get(prefix, "") + local_name

        query = f"""
        ASK {{
            ?instance a <{class_uri}> .
        }}
        """

        try:
            has_instances = self.data_graph.query(query).askAnswer

            # Trigger note when instances EXIST
            if has_instances:
                return {
                    "message": f"[Regulation Rule {rule_id}] {message}",
                    "focusNode": "AISystem",
                    "resultPath": "N/A",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                }
        except Exception as e:
            print(f"   ⚠️  Error checking existence for regulation rule {rule_id}: {e}")

        return None

    def _check_existence_or(self, rule_id, class_names, message):
        """
        Check if ANY of the specified classes exist (OR logic).

        Args:
            rule_id: Rule identifier (e.g., "II")
            class_names: List of class names with prefix
            message: Message to display if any class exists

        Returns:
            dict: Violation dictionary if any class exists, None otherwise
        """
        # Build UNION query for OR logic
        union_patterns = []
        for class_name in class_names:
            prefix, local_name = class_name.split(":")
            class_uri = self.namespaces.get(prefix, "") + local_name
            union_patterns.append(f"{{ ?instance a <{class_uri}> . }}")

        union_query = " UNION ".join(union_patterns)
        query = f"""
        ASK {{
            {union_query}
        }}
        """

        try:
            has_instances = self.data_graph.query(query).askAnswer

            if has_instances:
                return {
                    "message": f"[Regulation Rule {rule_id}] {message}",
                    "focusNode": "Function",
                    "resultPath": "N/A",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                }
        except Exception as e:
            print(f"   ⚠️  Error checking existence_or for regulation rule {rule_id}: {e}")

        return None

    def _check_complex_existence_absence(self, rule_id, existence_classes, absence_classes, message):
        """
        Check if existence classes exist AND absence classes are missing.

        Args:
            rule_id: Rule identifier (e.g., "III")
            existence_classes: Classes that must exist
            absence_classes: Classes that must NOT exist
            message: Message to display

        Returns:
            dict: Violation dictionary if condition met, None otherwise
        """
        # Check if ANY existence class exists
        existence_union = []
        for class_name in existence_classes:
            prefix, local_name = class_name.split(":")
            class_uri = self.namespaces.get(prefix, "") + local_name
            existence_union.append(f"{{ ?instance a <{class_uri}> . }}")

        existence_query = f"""
        ASK {{
            {" UNION ".join(existence_union)}
        }}
        """

        # Check if ALL absence classes are missing
        absence_checks = []
        for class_name in absence_classes:
            prefix, local_name = class_name.split(":")
            class_uri = self.namespaces.get(prefix, "") + local_name
            absence_query = f"ASK {{ ?instance a <{class_uri}> . }}"
            try:
                has_instances = self.data_graph.query(absence_query).askAnswer
                absence_checks.append(not has_instances)  # True if absent
            except Exception as e:
                print(f"   ⚠️  Error checking absence for {class_name}: {e}")
                absence_checks.append(False)

        try:
            has_existence = self.data_graph.query(existence_query).askAnswer
            all_absent = all(absence_checks)

            # Trigger if existence classes present AND absence classes missing
            if has_existence and all_absent:
                return {
                    "message": f"[Regulation Rule {rule_id}] {message}",
                    "focusNode": "DataQuality",
                    "resultPath": "N/A",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                }
        except Exception as e:
            print(f"   ⚠️  Error checking complex_existence_absence for regulation rule {rule_id}: {e}")

        return None

    def _check_inference_on_process_resources(self, rule_id, function_class, resource_classes, process_operator_class, message):
        """
        Check if Inference is assigned to resources that are connected to ProcessOperator.

        Args:
            rule_id: Rule identifier (e.g., "IV")
            function_class: Function class (ISO22989:Inference)
            resource_classes: List of resource classes to check
            process_operator_class: ProcessOperator class
            message: Message to display

        Returns:
            list: List of violation dictionaries
        """
        # Build resource class filter
        resource_filters = []
        for class_name in resource_classes:
            prefix, local_name = class_name.split(":")
            class_uri = self.namespaces.get(prefix, "") + local_name
            resource_filters.append(f"?resource a <{class_uri}>")

        resource_filter = " || ".join(resource_filters)

        func_prefix, func_local = function_class.split(":")
        func_uri = self.namespaces.get(func_prefix, "") + func_local

        po_prefix, po_local = process_operator_class.split(":")
        po_uri = self.namespaces.get(po_prefix, "") + po_local

        query = f"""
        PREFIX AIAS: <{self.namespaces.get('AIAS', '')}>
        PREFIX VDI3682: <{self.namespaces.get('VDI3682', '')}>

        SELECT ?inference ?resource ?processOp
        WHERE {{
            # Inference assigned to resource
            ?inference a <{func_uri}> .
            ?inference AIAS:isAssignedTo ?assignment .
            ?assignment a VDI3682:Assignment .
            ?resource AIAS:isAssignedTo ?assignment .

            # Resource must be one of the specified types
            FILTER({resource_filter})

            # Resource or ProcessOperator connected (check if ProcessOperator exists)
            # This is a simplified check - in reality might need more complex connection logic
            ?processOp a <{po_uri}> .
        }}
        """

        violations = []
        try:
            results = list(self.data_graph.query(query))

            for row in results:
                violations.append({
                    "message": f"[Regulation Rule {rule_id}] {message}",
                    "focusNode": str(row.inference),
                    "resultPath": f"Resource: {str(row.resource)}",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                })
        except Exception as e:
            print(f"   ⚠️  Error checking inference_on_process_resources for regulation rule {rule_id}: {e}")

        return violations

    def _check_assignment_or(self, rule_id, function_classes, component_class, message):
        """
        Check if any of the functions is assigned to the specified component.

        Args:
            rule_id: Rule identifier (e.g., "V", "VI")
            function_classes: List of function classes
            component_class: Component class to check
            message: Message to display

        Returns:
            list: List of violation dictionaries
        """
        # Build function class filter
        function_filters = []
        for class_name in function_classes:
            prefix, local_name = class_name.split(":")
            class_uri = self.namespaces.get(prefix, "") + local_name
            function_filters.append(f"?function a <{class_uri}>")

        function_filter = " || ".join(function_filters)

        comp_prefix, comp_local = component_class.split(":")
        comp_uri = self.namespaces.get(comp_prefix, "") + comp_local

        query = f"""
        PREFIX AIAS: <{self.namespaces.get('AIAS', '')}>
        PREFIX VDI3682: <{self.namespaces.get('VDI3682', '')}>

        SELECT ?function ?component
        WHERE {{
            # Function assigned to component
            ?function AIAS:isAssignedTo ?assignment .
            ?assignment a VDI3682:Assignment .
            ?component AIAS:isAssignedTo ?assignment .
            ?component a <{comp_uri}> .

            # Function must be one of the specified types
            FILTER({function_filter})
        }}
        """

        violations = []
        try:
            results = list(self.data_graph.query(query))

            for row in results:
                violations.append({
                    "message": f"[Regulation Rule {rule_id}] {message}",
                    "focusNode": str(row.function),
                    "resultPath": f"Component: {str(row.component)}",
                    "severity": "http://www.w3.org/ns/shacl#Info"
                })
        except Exception as e:
            print(f"   ⚠️  Error checking assignment_or for regulation rule {rule_id}: {e}")

        return violations
