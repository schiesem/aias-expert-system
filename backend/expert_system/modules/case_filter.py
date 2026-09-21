# expert_system/modules/case_filter.py

from rdflib import Graph
import os


class CaseFilter:
    """
    Filter-based case search system.

    Workflow:
    1. Analyze current model to extract component/function counts and architecture
    2. Return initial filter state (pre-filled with current model data)
    3. Accept filter criteria from user
    4. Query case_base/ to find matching cases
    5. Sort by best match (closest to filter criteria)
    """

    def __init__(self, current_graph: Graph, case_base_path: str, component_types: list = None, function_types: list = None):
        self.current_graph = current_graph
        self.case_base_path = case_base_path
        self.namespaces = {
            "ISO22989": "http://www.semanticweb.org/schieseck/ISO22989#",
            "AIAS": "http://www.semanticweb.org/schieseck/AIAS#",
            "VDI3682": "http://www.semanticweb.org/schieseck/VDI3682#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        }
        # Use provided types or discover from ontology
        self.component_types = component_types if component_types else self._discover_component_types()
        self.function_types = function_types if function_types else self._discover_function_types()

    def analyze_current_model(self) -> dict:
        """
        Analyze current model to populate initial filter state.

        Returns: {
            "components": {
                "Sensor": 3,
                "Actuator": 2,
                "Controller": 0,
                "EdgeDevice": 1,
                "CloudSystem": 0,
                "ComputerSystem": 0,
                "PersonalComputer": 0
            },
            "architecture": "edge|cloud|hybrid|unknown",
            "functions": {
                "Training": 0,
                "Inference": 2,
                "Validation": 0,
                "Evaluation": 0,
                "Storage": 0,
                "DataProcess": 0,
                "Acquisition": 0,
                "Filtering": 1,
                "Automate": 0
            }
        }
        """
        return {
            "components": self._count_all_components(self.current_graph),
            "architecture": self._detect_architecture(self.current_graph),
            "functions": self._count_all_functions(self.current_graph)
        }

    def search_with_filters(self, filter_criteria: dict) -> list:
        """
        Search case_base/ using filter criteria.

        Args:
            filter_criteria: {
                "components": {
                    "Sensor": {"enabled": True, "min": 2, "max": 4},
                    "Actuator": {"enabled": True, "min": 1, "max": 3},
                    ...
                },
                "architecture": "edge|cloud|hybrid|all",
                "functions": {
                    "Inference": {"enabled": True, "min": 1, "max": 3},
                    ...
                }
            }

        Returns:
            List of matching cases sorted by best match (fewest deviations)
        """
        cases = []

        # Load all case ontologies
        for case_folder in os.listdir(self.case_base_path):
            case_path = os.path.join(self.case_base_path, case_folder, "AIAS-instance.owl")
            if not os.path.exists(case_path):
                continue

            # Load case graph
            case_graph = Graph()
            try:
                case_graph.parse(case_path, format="xml")
            except Exception as e:
                print(f"   ⚠️  Error loading case {case_folder}: {e}")
                continue

            # Analyze case
            case_data = {
                "case_name": case_folder,
                "components": self._count_all_components(case_graph),
                "architecture": self._detect_architecture(case_graph),
                "functions": self._count_all_functions(case_graph)
            }

            # Check if case matches filters
            match_result = self._check_filter_match(case_data, filter_criteria)
            if match_result["matches"]:
                cases.append({
                    **case_data,
                    "match_score": match_result["score"],
                    "match_details": match_result["details"]
                })

        # Sort by best match (highest score = closest match)
        cases.sort(key=lambda x: x["match_score"], reverse=True)
        return cases

    def _discover_component_types(self) -> list:
        """Discover component types from ontology using SPARQL."""
        # Query for all subclasses of Resource (AIAS components)
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX AIAS: <http://www.semanticweb.org/schieseck/AIAS#>
        PREFIX VDI3682: <http://www.semanticweb.org/schieseck/VDI3682#>

        SELECT DISTINCT ?class WHERE {
            ?class rdfs:subClassOf* VDI3682:Resource .
            FILTER(?class != VDI3682:Resource)
        }
        """
        types = []
        try:
            results = list(self.current_graph.query(query))
            for row in results:
                class_uri = str(row.class_)
                # Extract class name from URI
                class_name = class_uri.split('#')[-1]
                if class_name and class_name != 'Resource':
                    types.append(class_name)
        except Exception as e:
            print(f"   ⚠️  Error discovering component types: {e}")
        return sorted(types)

    def _discover_function_types(self) -> list:
        """Discover function types from ontology using SPARQL."""
        # Query for all subclasses of Function (ISO22989 functions)
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ISO22989: <http://www.semanticweb.org/schieseck/ISO22989#>
        PREFIX VDI3682: <http://www.semanticweb.org/schieseck/VDI3682#>

        SELECT DISTINCT ?class WHERE {
            ?class rdfs:subClassOf* VDI3682:Function .
            FILTER(?class != VDI3682:Function)
        }
        """
        types = []
        try:
            results = list(self.current_graph.query(query))
            for row in results:
                class_uri = str(row.class_)
                # Extract class name from URI
                class_name = class_uri.split('#')[-1]
                if class_name and class_name != 'Function':
                    types.append(class_name)
        except Exception as e:
            print(f"   ⚠️  Error discovering function types: {e}")
        return sorted(types)

    def _count_all_components(self, graph: Graph) -> dict:
        """Count all component types using SPARQL."""
        counts = {}
        for comp_type in self.component_types:
            counts[comp_type] = self._count_class(graph, f"AIAS:{comp_type}")
        return counts

    def _count_all_functions(self, graph: Graph) -> dict:
        """Count all function types using SPARQL."""
        counts = {}
        for func_type in self.function_types:
            counts[func_type] = self._count_class(graph, f"ISO22989:{func_type}")
        return counts

    def _count_class(self, graph: Graph, class_name: str) -> int:
        """
        Count instances of a class using SPARQL.

        SPARQL Query:
        SELECT (COUNT(?instance) as ?count) WHERE {
            ?instance a <http://www.semanticweb.org/schieseck/AIAS#Sensor> .
        }
        """
        prefix, local_name = class_name.split(":")
        class_uri = self.namespaces[prefix] + local_name

        query = f"""
        SELECT (COUNT(?instance) as ?count) WHERE {{
            ?instance a <{class_uri}> .
        }}
        """

        try:
            results = list(graph.query(query))
            return int(results[0][0]) if results else 0
        except Exception as e:
            print(f"   ⚠️  Error counting {class_name}: {e}")
            return 0

    def _detect_architecture(self, graph: Graph) -> str:
        """
        Detect architecture type by checking for instances of ISO22989 SystemDesign subclasses.

        Logic:
        - Check for instances of ISO22989:Cloud, ISO22989:Edge, ISO22989:Hybrid
        - Return the architecture type based on which instances exist
        - If hybrid instances exist, return "hybrid" (most specific)
        - Return "unknown" if no architecture instances found
        """
        has_cloud = self._count_class(graph, "ISO22989:Cloud") > 0
        has_edge = self._count_class(graph, "ISO22989:Edge") > 0
        has_hybrid = self._count_class(graph, "ISO22989:Hybrid") > 0

        if has_hybrid:
            return "hybrid"
        elif has_cloud:
            return "cloud"
        elif has_edge:
            return "edge"
        else:
            return "unknown"

    def _check_filter_match(self, case_data: dict, filter_criteria: dict) -> dict:
        """
        Check if case matches filter criteria and calculate match score.

        Match score: Number of matching filters (higher = better match)

        Returns: {
            "matches": bool,
            "score": int,
            "details": {
                "Sensor": "match|miss|within_range|out_of_range",
                ...
            }
        }
        """
        matches = True
        score = 0
        details = {}

        # Check component filters
        for comp_type, filter_config in filter_criteria.get("components", {}).items():
            if not filter_config.get("enabled", False):
                continue

            case_count = case_data["components"].get(comp_type, 0)
            min_count = filter_config["min"]
            max_count = filter_config["max"]

            if min_count <= case_count <= max_count:
                details[comp_type] = "match"
                score += 1
            else:
                details[comp_type] = "out_of_range"
                matches = False

        # Check architecture filter
        arch_filter = filter_criteria.get("architecture", "all")
        if arch_filter != "all":
            if case_data["architecture"] == arch_filter:
                details["architecture"] = "match"
                score += 1
            else:
                details["architecture"] = "miss"
                matches = False

        # Check function filters
        for func_type, filter_config in filter_criteria.get("functions", {}).items():
            if not filter_config.get("enabled", False):
                continue

            case_count = case_data["functions"].get(func_type, 0)
            min_count = filter_config["min"]
            max_count = filter_config["max"]

            if min_count <= case_count <= max_count:
                details[func_type] = "match"
                score += 1
            else:
                details[func_type] = "out_of_range"
                matches = False

        return {
            "matches": matches,
            "score": score,
            "details": details
        }
