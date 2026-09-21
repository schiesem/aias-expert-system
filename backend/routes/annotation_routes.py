"""
annotation_routes.py

REST API routes for annotation operations.
Provides endpoints for:
- Relation discovery (get available relations for a class)
- Annotation retrieval (get annotations for an element)
- Annotation creation (create and link annotation instances)
- Annotation deletion (remove annotation links)
- Annotation count (get count of annotations)
"""

from flask import Blueprint, request, jsonify
from data_store import DataStore
from expert_system.modules.annotation_manager import AnnotationManager
from expert_system.modules.ontology_manager import OntologyManager

# Create Blueprint
annotation_bp = Blueprint('annotation', __name__, url_prefix='/api/annotations')

# Use global singleton from app_globals
# This ensures all routes share the same OntologyManager and World instance
from app_globals import get_annotation_manager


@annotation_bp.route('/relations/<class_name>', methods=['GET'])
def get_relations(class_name):
    """
    Get available relations for a class.

    URL Parameters:
        class_name: OWL class name (can be URL encoded)

    Query Parameters:
        - max_level: int (default 3) - Maximum relation depth
        - level: int (optional) - Get specific level only

    Returns:
        JSON:
        {
            "success": true,
            "class_name": "ISO22989.Training",
            "relations": [
                {
                    "property": "isExecutedBy",
                    "target_class": "ISO22989.Model",
                    "cardinality": "1..1",
                    "level": 1,
                    "is_required": true,
                    "description": "Links training function to the model being trained"
                },
                ...
            ],
            "total_count": 5
        }

    Example:
        GET /api/annotations/relations/ISO22989.Training?max_level=3
        GET /api/annotations/relations/ISO22989.Training?level=1
    """
    try:
        manager = get_annotation_manager()

        max_level = request.args.get('max_level', 1, type=int)
        specific_level = request.args.get('level', type=int)

        # Validate parameters
        if max_level < 1 or max_level > 10:
            return jsonify({
                'success': False,
                'error': 'max_level must be between 1 and 10'
            }), 400

        print(f"📋 Getting relations for {class_name}, max_level={max_level}")

        # Get relations
        relations = manager.get_relation_level_n(class_name, max_level)

        # Filter by specific level if requested
        if specific_level:
            relations = [r for r in relations if r['level'] == specific_level]

        # Add is_graphical flag to each relation
        for relation in relations:
            target_class = relation.get('target_class')
            if target_class:
                relation['is_graphical'] = manager.is_graphical_class(target_class)
            else:
                relation['is_graphical'] = False

        # Debug: Log relations with direction
        print(f"📋 Returning {len(relations)} relations:")
        for r in relations:
            direction = r.get('direction', 'MISSING')
            print(f"   - {r.get('property')} → {r.get('target_class')} (direction: {direction}, level: {r.get('level')})")

        return jsonify({
            'success': True,
            'class_name': class_name,
            'relations': relations,
            'total_count': len(relations)
        }), 200

    except Exception as e:
        print(f"❌ Error in get_relations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/<element_id>', methods=['GET'])
def get_annotations(element_id):
    """
    Get all annotations for an element.

    URL Parameters:
        element_id: ID of the graphical element

    Query Parameters:
        - max_depth: int (default 3) - Maximum annotation graph depth

    Returns:
        JSON:
        {
            "success": true,
            "annotations": {
                "element_id": "Training1",
                "element_class": "ISO22989.Training",
                "annotations": {
                    "isExecutedBy": [
                        {
                            "name": "ProductionNet",
                            "class": "ISO22989.Model",
                            "properties": {
                                "version": "1.0"
                            },
                            "sub_annotations": {...}
                        }
                    ]
                }
            }
        }

    Example:
        GET /api/annotations/Training1?max_depth=3
    """
    try:
        manager = get_annotation_manager()
        max_depth = request.args.get('max_depth', 3, type=int)

        # Validate parameters
        if max_depth < 1 or max_depth > 10:
            return jsonify({
                'success': False,
                'error': 'max_depth must be between 1 and 10'
            }), 400

        print(f"📖 Getting annotations for {element_id}, max_depth={max_depth}")

        annotations = manager.get_annotations(element_id, max_depth)

        return jsonify({
            'success': True,
            'annotations': annotations
        }), 200

    except Exception as e:
        print(f"❌ Error in get_annotations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/<element_id>', methods=['POST'])
def create_annotation(element_id):
    """
    Create an annotation for an element.

    URL Parameters:
        element_id: ID of the graphical element

    Request Body:
        {
            "relation_property": "isExecutedBy",
            "target_class": "ISO22989.Model",
            "instance_data": {
                "name": "ProductionNet",
                "properties": {
                    "version": "1.0",
                    "description": "Neural network for production"
                }
            }
        }

    Returns:
        JSON:
        {
            "success": true,
            "annotation": {
                "name": "ProductionNet",
                "class": "ISO22989.Model"
            }
        }

    Example:
        POST /api/annotations/Training1
        Body: {...}
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['element_class', 'relation_property', 'target_class', 'instance_data']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Validate instance_data has name
        if 'name' not in data['instance_data']:
            return jsonify({
                'success': False,
                'error': 'instance_data must contain "name" field'
            }), 400

        manager = get_annotation_manager()

        # Get optional parent instance (for Level 2+ annotations)
        parent_instance_name = data.get('parent_instance', None)

        # Get optional direction (outgoing or incoming)
        direction = data.get('direction', 'outgoing')

        print(f"➕ Creating {direction} annotation for {element_id}")
        print(f"   Element Class: {data['element_class']}")
        print(f"   Property: {data['relation_property']}")
        print(f"   Target: {data['target_class']}")
        print(f"   Instance: {data['instance_data']['name']}")
        print(f"   Direction: {direction}")
        if parent_instance_name:
            print(f"   Parent: {parent_instance_name} (nested annotation)")

        annotation = manager.create_annotation(
            element_id=element_id,
            element_class_name=data['element_class'],
            relation_property=data['relation_property'],
            target_class_name=data['target_class'],
            instance_data=data['instance_data'],
            parent_instance_name=parent_instance_name,
            direction=direction
        )

        if annotation:
            # Save ontology to persist changes
            try:
                manager.onto_manager.save_ontology()
                print(f"💾 Ontology saved after creating {annotation.name}")
            except Exception as save_error:
                print(f"⚠️ Warning: Could not save ontology: {save_error}")

            # Generate instance graph visualization (includes annotations) in world folder
            try:
                from expert_system.modules.graph_plot import create_pyviy_network_plot
                from app_globals import get_world_manager, get_current_world_id

                world_mgr = get_world_manager()
                world_id = get_current_world_id()
                world_dir = world_mgr._get_world_dir(world_id)

                create_pyviy_network_plot(manager.onto_manager.get_ontology(), templates_path=world_dir, graph_type='instance')
                print(f"✓ Generated instance graph visualization in world folder")
            except Exception as graph_error:
                print(f"⚠️ Warning: Could not generate graph: {graph_error}")

            # Clear inferred ontology since model changed
            try:
                manager.onto_manager.clear_inferred_ontology()
                print(f"✓ Cleared inferred ontology (reasoning now outdated)")
            except Exception as clear_error:
                print(f"⚠️ Warning: Could not clear inferred ontology: {clear_error}")

            return jsonify({
                'success': True,
                'annotation': {
                    'id': annotation.name,  # Random ID is the OWL individual name
                    'display_name': annotation.hasName[0] if annotation.hasName else '',
                    'class': manager._get_class_full_name(annotation.__class__)
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create annotation'
            }), 500

    except Exception as e:
        print(f"❌ Error in create_annotation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/<element_id>/<relation_property>/<annotation_id>', methods=['DELETE'])
def delete_annotation(element_id, relation_property, annotation_id):
    """
    Delete an annotation from an element.

    URL Parameters:
        element_id: ID of the graphical element
        relation_property: Object property name
        annotation_id: Random ID of the annotation instance to delete

    Query Parameters:
        direction: "outgoing" (default) or "incoming"

    Returns:
        JSON:
        {
            "success": true,
            "message": "Annotation deleted successfully"
        }

    Example:
        DELETE /api/annotations/Training1/isExecutedBy/abc123ef
        DELETE /api/annotations/Inference1/executes/model123?direction=incoming
    """
    try:
        manager = get_annotation_manager()

        # Get direction from query params (default: outgoing)
        direction = request.args.get('direction', 'outgoing')

        print(f"🗑️ Deleting {direction} annotation: {element_id} -> {relation_property} -> {annotation_id}")

        success = manager.delete_annotation(
            element_id=element_id,
            relation_property=relation_property,
            annotation_id=annotation_id,
            direction=direction
        )

        if success:
            # Save ontology to persist changes
            try:
                manager.onto_manager.save_ontology()
                print(f"💾 Ontology saved after deleting {annotation_id}")
            except Exception as save_error:
                print(f"⚠️ Warning: Could not save ontology: {save_error}")

            # Generate instance graph visualization (reflects deletion)
            try:
                from expert_system.modules.graph_plot import create_pyviy_network_plot
                create_pyviy_network_plot(manager.onto_manager.get_ontology(), graph_type='instance')
                print(f"✓ Generated instance graph visualization")
            except Exception as graph_error:
                print(f"⚠️ Warning: Could not generate graph: {graph_error}")

            # Clear inferred ontology since model changed
            try:
                manager.onto_manager.clear_inferred_ontology()
                print(f"✓ Cleared inferred ontology (reasoning now outdated)")
            except Exception as clear_error:
                print(f"⚠️ Warning: Could not clear inferred ontology: {clear_error}")

            return jsonify({
                'success': True,
                'message': 'Annotation deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete annotation'
            }), 500

    except Exception as e:
        print(f"❌ Error in delete_annotation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/instances/<class_name>', methods=['GET'])
def get_instances_by_class(class_name):
    """
    Get all existing instances of a specific ontology class.
    Used for "Use Existing" dropdown in annotation UI.

    Args:
        class_name: Fully qualified class name (e.g., "ISO22989.Task")

    Query Parameters:
        world_id: Optional world ID

    Returns:
        JSON:
        {
            "success": true,
            "class_name": "ISO22989.Task",
            "instances": [
                {
                    "id": "abc123ef",
                    "display_name": "ClassificationTask",
                    "class": "ISO22989.Task",
                    "properties": {...}
                }
            ]
        }
    """
    try:
        # Get annotation manager singleton
        manager = get_annotation_manager()

        # Get the ontology class
        onto_class = manager.onto_manager.get_class_by_name(class_name)

        instances = []
        seen_ids = set()  # Track seen instance IDs to avoid duplicates

        if onto_class:
            # Collect all classes to check (including equivalent classes)
            classes_to_check = [onto_class]

            # Check for equivalent classes (owl:equivalentClass)
            if hasattr(onto_class, 'equivalent_to'):
                for equiv_class in onto_class.equivalent_to:
                    if hasattr(equiv_class, 'instances') and equiv_class not in classes_to_check:
                        classes_to_check.append(equiv_class)
                        print(f"   → Including equivalent class: {equiv_class.name}")

            # Also check reverse direction (if this class is equivalent to another)
            # This handles the case where ISO22989.Data is marked as equivalent to ISO7489.Data
            world = manager.onto_manager.world
            for other_class in world.classes():
                if hasattr(other_class, 'equivalent_to'):
                    if onto_class in other_class.equivalent_to and other_class not in classes_to_check:
                        classes_to_check.append(other_class)
                        print(f"   → Including reverse equivalent class: {other_class.name}")

            # Iterate through all instances of all equivalent classes
            for check_class in classes_to_check:
                for individual in check_class.instances():
                    # Skip if already seen (avoid duplicates)
                    if individual.name in seen_ids:
                        continue
                    seen_ids.add(individual.name)

                    # Get display name from hasName property, fallback to ID
                    display_name = individual.hasName[0] if individual.hasName else individual.name

                    instances.append({
                        'id': individual.name,  # Random UUID ID
                        'display_name': display_name,
                        'class': manager._get_class_full_name(individual.__class__),
                        'properties': manager._get_datatype_properties(individual)
                    })

        print(f"📋 Found {len(instances)} instances of class {class_name} (checked {len(classes_to_check) if onto_class else 0} equivalent classes)")

        return jsonify({
            'success': True,
            'class_name': class_name,
            'instances': instances
        })

    except Exception as e:
        print(f"❌ Error getting instances of class {class_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/<element_id>/link', methods=['POST'])
def link_existing_annotation(element_id):
    """
    Link an existing annotation instance to an element or parent annotation.
    Used for "Use Existing" functionality in annotation UI.

    Args:
        element_id: ID of the element or parent annotation

    Payload:
        {
            "relation_property": "fulfills",
            "instance_id": "abc123ef",
            "parent_instance": null or "xyz789",
            "direction": "outgoing" or "incoming"
        }

    Query Parameters:
        world_id: Optional world ID

    Returns:
        JSON:
        {
            "success": true,
            "message": "Linked source → target via property"
        }
    """
    try:
        data = request.get_json()

        # Extract payload data
        relation_property = data.get('relation_property')
        instance_id = data.get('instance_id')
        parent_instance_name = data.get('parent_instance')
        direction = data.get('direction', 'outgoing')  # Default to outgoing for backwards compatibility

        # Validation
        if not relation_property:
            return jsonify({
                'success': False,
                'error': 'relation_property is required'
            }), 400

        if not instance_id:
            return jsonify({
                'success': False,
                'error': 'instance_id is required'
            }), 400

        # Get annotation manager singleton
        manager = get_annotation_manager()

        # Determine source individual (element or parent annotation)
        if parent_instance_name:
            # Level 2+: Link from parent annotation
            source_individual = manager.onto_manager.get_individual_by_name(parent_instance_name)
            if not source_individual:
                return jsonify({
                    'success': False,
                    'error': f'Parent instance {parent_instance_name} not found'
                }), 404
            source_name = parent_instance_name
        else:
            # Level 1: Link from graphical element
            source_individual = manager.onto_manager.get_individual_by_name(element_id)
            if not source_individual:
                return jsonify({
                    'success': False,
                    'error': f'Element {element_id} not found'
                }), 404
            source_name = element_id

        # Get the selected existing instance
        selected_individual = manager.onto_manager.get_individual_by_name(instance_id)
        if not selected_individual:
            return jsonify({
                'success': False,
                'error': f'Instance {instance_id} not found'
            }), 404

        # Determine actual source and target based on direction
        # For INCOMING relations (e.g., "Data → isProcessedBy → Merging" on a Merging element):
        #   - source_individual is the current element (Merging)
        #   - selected_individual is the existing instance (Data)
        #   - But the property belongs to Data, so we need to SWAP them!
        #   - Correct: Data.isProcessedBy = Merging
        # For OUTGOING relations (e.g., "Merging → usesData → Data" on a Merging element):
        #   - source_individual is the current element (Merging)
        #   - selected_individual is the existing instance (Data)
        #   - Correct: Merging.usesData = Data

        if direction == "incoming":
            # Incoming: selected_instance --property--> element
            # The selected instance (e.g., Data) has the property pointing to our element (e.g., Merging)
            property_owner = selected_individual
            property_target = source_individual
            link_description = f"{instance_id} --{relation_property}--> {source_name}"
            print(f"🔗 Creating INCOMING link: {instance_id} --{relation_property}--> {source_name}")
        else:
            # Outgoing: element --property--> selected_instance
            # Our element (e.g., Merging) has the property pointing to selected instance (e.g., Data)
            property_owner = source_individual
            property_target = selected_individual
            link_description = f"{source_name} --{relation_property}--> {instance_id}"
            print(f"🔗 Creating OUTGOING link: {source_name} --{relation_property}--> {instance_id}")

        # Create link via object property
        manager.onto_manager.create_individual_property(
            property_owner.name,
            relation_property,
            property_target.name
        )

        # Save ontology
        manager.onto_manager.save_ontology()

        # Generate instance graph visualization (includes the new link)
        try:
            from expert_system.modules.graph_plot import create_pyviy_network_plot
            from app_globals import get_world_manager, get_current_world_id

            world_mgr = get_world_manager()
            world_id = get_current_world_id()
            world_dir = world_mgr._get_world_dir(world_id)

            create_pyviy_network_plot(manager.onto_manager.get_ontology(), templates_path=world_dir, graph_type='instance')
            print(f"✓ Generated instance graph visualization in world folder")
        except Exception as graph_error:
            print(f"⚠️ Warning: Could not generate graph: {graph_error}")

        print(f"✅ Linked {link_description}")

        return jsonify({
            'success': True,
            'message': f'Linked via {relation_property}: {link_description}'
        })

    except Exception as e:
        print(f"❌ Error linking instance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/clear-all', methods=['POST'])
def clear_all_annotations():
    """
    Clear all annotation instances from the ontology.
    This deletes all individuals while keeping class definitions intact.
    Useful when starting a fresh modeling session.

    Returns:
        JSON:
        {
            "success": true,
            "message": "Cleared N instances",
            "count": N
        }

    Example:
        POST /api/annotations/clear-all
    """
    try:
        manager = get_annotation_manager()

        print(f"🗑️ Clearing all annotation instances...")

        count = manager.onto_manager.clear_all_individuals()

        if count >= 0:
            # Save ontology to persist the deletion
            try:
                manager.onto_manager.save_ontology()
                print(f"💾 Ontology saved after clearing {count} instances")
            except Exception as save_error:
                print(f"⚠️ Warning: Could not save ontology: {save_error}")

            return jsonify({
                'success': True,
                'message': f'Cleared {count} instance(s)',
                'count': count
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clear instances'
            }), 500

    except Exception as e:
        print(f"❌ Error in clear_all_annotations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/<element_id>/count', methods=['GET'])
def get_annotation_count(element_id):
    """
    Get count of annotations for an element.

    URL Parameters:
        element_id: ID of the graphical element

    Returns:
        JSON:
        {
            "success": true,
            "element_id": "Training1",
            "count": 3
        }

    Example:
        GET /api/annotations/Training1/count
    """
    try:
        manager = get_annotation_manager()

        print(f"🔢 Getting annotation count for {element_id}")

        count = manager.get_annotation_count(element_id)

        return jsonify({
            'success': True,
            'element_id': element_id,
            'count': count
        }), 200

    except Exception as e:
        print(f"❌ Error in get_annotation_count: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify annotation service is running.

    Returns:
        JSON:
        {
            "success": true,
            "message": "Annotation service is running",
            "manager_initialized": true
        }
    """
    try:
        manager_initialized = (
            hasattr(DataStore, 'annotation_manager') and
            DataStore.annotation_manager is not None
        )

        return jsonify({
            'success': True,
            'message': 'Annotation service is running',
            'manager_initialized': manager_initialized
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/sync-model', methods=['POST'])
def sync_graphical_model():
    """
    Synchronize the graphical model (nodes/edges) to the ontology.

    SIMPLIFIED APPROACH:
    - Clear all graphical elements (nodes/edges)
    - Recreate exactly what frontend sends
    - Annotations persist independently (NOT deleted)
    - No complex inheritance checking needed

    Request Body:
        {
            "nodes": [...],  // ReactFlow nodes with class names
            "edges": [...]   // ReactFlow edges
        }

    Returns:
        JSON:
        {
            "success": true,
            "message": "Model synchronized",
            "stats": {
                "nodes_synced": N,
                "edges_synced": M
            }
        }
    """
    try:
        data = request.get_json()

        if not data or 'nodes' not in data or 'edges' not in data:
            return jsonify({
                'success': False,
                'error': 'Request must include "nodes" and "edges" arrays'
            }), 400

        manager = get_annotation_manager()

        print(f"🔄 Syncing graphical model (simple recreate)...")
        print(f"   Nodes to sync: {len(data['nodes'])}")
        print(f"   Edges to sync: {len(data['edges'])}")

        # Step 1: Clear all graphical elements (nodes/edges only - annotations stay)
        cleared_count = manager.onto_manager.clear_graphical_elements()
        print(f"   ✓ Cleared {cleared_count} old graphical elements")

        # Step 2: Convert frontend format to backend format using DataStore
        data_store = DataStore()
        data_store.update(data)
        model_data = data_store.get()

        # Step 3: Recreate graphical elements from frontend state
        nodes_created, edges_created = manager.onto_manager.instantiate_nodes(model_data)
        properties_created = manager.onto_manager.instantiate_properties(model_data, nodes_created, edges_created)

        # Step 4: Save to AIAS-instance.owl
        manager.onto_manager.save_ontology()

        # Step 5: Generate instance graph visualization (user model only, NO reasoning)
        from expert_system.modules.graph_plot import create_pyviy_network_plot
        create_pyviy_network_plot(manager.onto_manager.get_ontology(), graph_type='instance')
        print(f"   ✓ Generated instance graph visualization")

        # Step 6: Clear inferred ontology since user model changed
        manager.onto_manager.clear_inferred_ontology()
        print(f"   ✓ Cleared inferred ontology (reasoning now outdated)")

        print(f"✅ Sync complete!")
        print(f"   Graphical: {len(nodes_created)} nodes, {len(edges_created)} edges")
        print(f"   Annotations: preserved (not deleted)")

        return jsonify({
            'success': True,
            'message': 'Model synchronized successfully',
            'stats': {
                'nodes_synced': len(nodes_created),
                'edges_synced': len(edges_created),
                'properties_synced': len(properties_created)
            }
        }), 200

    except Exception as e:
        print(f"❌ Error syncing model: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
