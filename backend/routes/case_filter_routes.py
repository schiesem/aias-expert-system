# routes/case_filter_routes.py

from flask import Blueprint, jsonify, request
from expert_system.modules.case_filter import CaseFilter
from expert_system.case_base import get_case_base_path
from app_globals import get_ontology_manager
import rdflib
import tempfile
import os

case_filter_bp = Blueprint("case_filter", __name__)


@case_filter_bp.route("/available-types", methods=['GET'])
def get_available_types():
    """
    Get available component and function types for filtering.

    This endpoint returns the same class types used in the UI dropdowns,
    ensuring consistency across the application.

    Returns:
        JSON with available components and functions from the ontology
    """
    try:
        manager = get_ontology_manager()
        if manager.ontology is None:
            manager.load_from_working_copy()

        # Get Function subclasses
        function_class = manager.get_class_by_name('Function')
        function_types = []
        if function_class:
            for subclass in function_class.descendants():
                if subclass != function_class:
                    # Get simple class name (without namespace)
                    class_name = subclass.name
                    if class_name:
                        function_types.append(class_name)

        # Get Resource subclasses (components)
        resource_class = manager.get_class_by_name('Resource')
        component_types = []
        if resource_class:
            for subclass in resource_class.descendants():
                if subclass != resource_class:
                    # Get simple class name (without namespace)
                    class_name = subclass.name
                    if class_name:
                        component_types.append(class_name)

        return jsonify({
            "status": "success",
            "components": sorted(component_types),
            "functions": sorted(function_types)
        })

    except Exception as e:
        print(f"   ⚠️  Error getting available types: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@case_filter_bp.route("/analyze", methods=['GET'])
def analyze_current_model():
    """
    Analyze current model to provide initial filter state.

    Workflow:
    1. Load current world's AIAS-instance.owl
    2. Convert to rdflib Graph
    3. Count all components, functions
    4. Detect architecture
    5. Return data for pre-filling filter UI

    Returns:
        JSON with current model analysis for filter initialization
    """
    try:
        # Load current model
        manager = get_ontology_manager()
        if manager.ontology is None:
            manager.load_from_working_copy()

        # Convert to RDFlib graph
        with tempfile.NamedTemporaryFile(mode='w', suffix='.owl', delete=False) as tmp:
            temp_path = tmp.name
        manager.ontology.save(temp_path, format="rdfxml")

        current_graph = rdflib.Graph()
        current_graph.parse(temp_path, format="xml")
        os.unlink(temp_path)

        # Get available types from ontology
        function_class = manager.get_class_by_name('Function')
        function_types = []
        if function_class:
            for subclass in function_class.descendants():
                if subclass != function_class and subclass.name:
                    function_types.append(subclass.name)

        resource_class = manager.get_class_by_name('Resource')
        component_types = []
        if resource_class:
            for subclass in resource_class.descendants():
                if subclass != resource_class and subclass.name:
                    component_types.append(subclass.name)

        # Analyze model with discovered types
        filter_engine = CaseFilter(current_graph, get_case_base_path(), component_types, function_types)
        analysis = filter_engine.analyze_current_model()

        return jsonify({
            "status": "success",
            "analysis": analysis
        })

    except Exception as e:
        print(f"   ⚠️  Error analyzing current model: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@case_filter_bp.route("/search", methods=['POST'])
def search_with_filters():
    """
    Search for cases matching filter criteria.

    Request Body:
    {
        "components": {
            "Sensor": {"enabled": true, "min": 2, "max": 4},
            "Actuator": {"enabled": true, "min": 1, "max": 3}
        },
        "architecture": "edge",
        "functions": {
            "Inference": {"enabled": true, "min": 1, "max": 3}
        }
    }

    Returns:
        JSON with matching cases sorted by best match
    """
    try:
        filter_criteria = request.json

        # Load current model
        manager = get_ontology_manager()
        if manager.ontology is None:
            manager.load_from_working_copy()

        # Convert to RDFlib graph
        with tempfile.NamedTemporaryFile(mode='w', suffix='.owl', delete=False) as tmp:
            temp_path = tmp.name
        manager.ontology.save(temp_path, format="rdfxml")

        current_graph = rdflib.Graph()
        current_graph.parse(temp_path, format="xml")
        os.unlink(temp_path)

        # Get available types from ontology
        function_class = manager.get_class_by_name('Function')
        function_types = []
        if function_class:
            for subclass in function_class.descendants():
                if subclass != function_class and subclass.name:
                    function_types.append(subclass.name)

        resource_class = manager.get_class_by_name('Resource')
        component_types = []
        if resource_class:
            for subclass in resource_class.descendants():
                if subclass != resource_class and subclass.name:
                    component_types.append(subclass.name)

        # Search with filters using discovered types
        filter_engine = CaseFilter(current_graph, get_case_base_path(), component_types, function_types)
        matching_cases = filter_engine.search_with_filters(filter_criteria)

        return jsonify({
            "status": "success",
            "cases": matching_cases,
            "message": f"Found {len(matching_cases)} matching cases"
        })

    except Exception as e:
        print(f"   ⚠️  Error searching with filters: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
