"""
model_routes.py

Unified model synchronization endpoints.
Replaces /store/recieve and /api/annotations/sync-model with a single,
consistent API for model state management.

This module provides:
- POST /api/model/sync - Unified synchronization (replaces dual endpoints)
- GET /api/model/load - Load complete state for frontend initialization
- GET /api/model/class-types - Discover available class types with namespaces
- GET /api/model/health - Health check and status information
"""

from flask import Blueprint, request, jsonify
from app_globals import get_ontology_manager, get_graphical_state_manager
from data_store import DataStore
import threading

# Create blueprint
model_bp = Blueprint('model', __name__, url_prefix='/api/model')

# Thread lock for synchronization operations
_sync_lock = threading.Lock()


@model_bp.route('/sync', methods=['POST', 'OPTIONS'])
def sync_model():
    """
    Synchronize graphical model to backend ontology.

    This is the UNIFIED endpoint that replaces:
    - /store/recieve (legacy)
    - /api/annotations/sync-model (old annotation sync)

    Request Body:
        {
            "nodes": [
                {
                    "id": "Training1",
                    "type": "FunctionNode",
                    "position": {"x": 150, "y": 200},
                    "data": {
                        "name": "ML Training",
                        "functionType": "ISO22989.Training"  // Namespace-qualified!
                    }
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "type": "AssignmentEdge",
                    "source": "Training1",
                    "target": "Resource1",
                    "data": {...}
                }
            ],
            "viewport": {
                "x": 150,
                "y": 200,
                "zoom": 1.2
            }
        }

    Response:
        {
            "success": true,
            "message": "Model synchronized successfully",
            "stats": {
                "nodes_synced": 5,
                "edges_synced": 8,
                "properties_synced": 16,
                "graphical_cleared": 13,
                "annotations_preserved": 27
            }
        }

    Features:
    - Preserves annotations (doesn't delete them)
    - Stores viewport state (zoom, pan)
    - Stores node positions
    - Uses global singleton (single World instance)
    - Thread-safe with mutex lock
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200

    # Acquire lock to prevent concurrent syncs
    if not _sync_lock.acquire(blocking=False):
        return jsonify({
            'success': False,
            'error': 'Sync already in progress. Please wait.',
            'error_type': 'conflict'
        }), 409

    try:
        data = request.get_json()

        # Validate request
        if not data or 'nodes' not in data or 'edges' not in data:
            return jsonify({
                'success': False,
                'error': 'Request must include "nodes" and "edges" arrays',
                'error_type': 'validation_error'
            }), 400

        # Get global singleton manager
        manager = get_ontology_manager()

        # Check if ontology is loaded
        if manager.ontology is None:
            return jsonify({
                'success': False,
                'error': 'No ontology loaded. Please load an ontology first using the Expert System panel.',
                'error_type': 'ontology_not_loaded'
            }), 400

        print(f"\n{'='*60}")
        print(f"🔄 SYNCHRONIZING MODEL TO BACKEND")
        print(f"{'='*60}")
        print(f"   Nodes to sync: {len(data['nodes'])}")
        print(f"   Edges to sync: {len(data['edges'])}")
        print(f"   Viewport included: {'viewport' in data}")

        # Step 1: Extract IDs from incoming model to preserve during clear
        keep_ids = set()
        for node in data.get('nodes', []):
            if 'id' in node:
                keep_ids.add(node['id'])
        for edge in data.get('edges', []):
            if 'id' in edge:
                keep_ids.add(edge['id'])

        # Step 2: Clear ONLY graphical elements not in the incoming model (preserves annotations!)
        cleared_count = manager.clear_graphical_elements(keep_ids)
        print(f"   ✓ Cleared {cleared_count} old graphical elements (annotations preserved)")

        # Step 3: Convert frontend format to backend format
        data_store = DataStore()
        data_store.update(data)
        model_data = data_store.get()

        # Step 4: Recreate graphical elements from frontend state
        nodes_created, edges_created = manager.instantiate_nodes(model_data)
        print(f"   ✓ Created {len(nodes_created)} nodes, {len(edges_created)} edges")

        # Step 5: Create properties (connections, etc.)
        properties_created = manager.instantiate_properties(
            model_data, nodes_created, edges_created
        )
        print(f"   ✓ Created {len(properties_created)} properties")

        # Step 6: Save graphical state (viewport + node positions + edge waypoints) to separate JSON
        world_id = str(id(manager.world))

        # Extract node positions from frontend data
        node_positions = {}
        for node in data.get('nodes', []):
            if 'position' in node and 'id' in node:
                node_positions[node['id']] = {
                    'x': node['position'].get('x', 0),
                    'y': node['position'].get('y', 0)
                }

        # Extract edge waypoints from frontend data
        edge_waypoints = {}
        for edge in data.get('edges', []):
            if 'data' in edge and 'waypoints' in edge['data'] and 'id' in edge:
                # Only save if waypoints exist (not empty list)
                waypoints = edge['data']['waypoints']
                if waypoints and len(waypoints) > 0:
                    edge_waypoints[edge['id']] = waypoints

        # Extract edge handles (anchor points) from frontend data
        # Also save source/target IDs to ensure correct handle assignment on load
        edge_handles = {}
        for edge in data.get('edges', []):
            if 'id' in edge:
                handles = {}
                if 'sourceHandle' in edge and edge['sourceHandle']:
                    handles['sourceHandle'] = edge['sourceHandle']
                if 'targetHandle' in edge and edge['targetHandle']:
                    handles['targetHandle'] = edge['targetHandle']
                # Save source/target IDs for correct handle assignment on load
                if 'source' in edge:
                    handles['source'] = edge['source']
                if 'target' in edge:
                    handles['target'] = edge['target']

                # Only save if at least one handle is defined
                if handles:
                    edge_handles[edge['id']] = handles

        # Extract edge label offsets from frontend data
        edge_label_offsets = {}
        for edge in data.get('edges', []):
            if 'data' in edge and 'labelOffset' in edge['data'] and 'id' in edge:
                # Only save if labelOffset is not default (0, 0)
                offset = edge['data']['labelOffset']
                if offset.get('x', 0) != 0 or offset.get('y', 0) != 0:
                    edge_label_offsets[edge['id']] = {
                        'x': offset.get('x', 0),
                        'y': offset.get('y', 0)
                    }

        # Extract edge data (showLabel, arrowForward, arrowBackward) from frontend data
        edge_data = {}
        for edge in data.get('edges', []):
            if 'data' in edge and 'id' in edge:
                edge_props = {}

                # Save showLabel if explicitly set to false (default is true)
                if 'showLabel' in edge['data'] and edge['data']['showLabel'] == False:
                    edge_props['showLabel'] = False

                # Save arrow directions if present
                if 'arrowForward' in edge['data']:
                    edge_props['arrowForward'] = edge['data']['arrowForward']
                if 'arrowBackward' in edge['data']:
                    edge_props['arrowBackward'] = edge['data']['arrowBackward']

                # Save jumpOverCrossings if present
                if 'jumpOverCrossings' in edge['data']:
                    edge_props['jumpOverCrossings'] = edge['data']['jumpOverCrossings']

                # Only save if there are properties to save
                if edge_props:
                    edge_data[edge['id']] = edge_props

        # Get viewport or use default
        viewport = data.get('viewport', {'x': 0, 'y': 0, 'zoom': 1.0})

        # Save to graphical state manager with all edge data
        graphical_state_mgr = get_graphical_state_manager()
        graphical_state_mgr.save_state(world_id, viewport, node_positions, edge_handles, edge_waypoints, edge_label_offsets, edge_data)
        print(f"   ✓ Saved graphical state (viewport + {len(node_positions)} positions + {len(edge_handles)} edge handles + {len(edge_waypoints)} edge waypoints + {len(edge_label_offsets)} label offsets + {len(edge_data)} edge data) to JSON")

        # Step 6: Save to AIAS-instance.owl
        manager.save_ontology()
        print(f"   ✓ Saved to AIAS-instance.owl")

        # Step 8: Generate instance graph visualization (in world-specific folder)
        try:
            from expert_system.modules.graph_plot import create_pyviy_network_plot
            from app_globals import get_world_manager, get_current_world_id

            world_mgr = get_world_manager()
            world_id = get_current_world_id()
            world_dir = world_mgr._get_world_dir(world_id)

            create_pyviy_network_plot(manager.get_ontology(), templates_path=world_dir, graph_type='instance')
            print(f"   ✓ Generated instance graph visualization in world folder")
        except Exception as graph_error:
            print(f"   ⚠️ Warning: Could not generate graph: {graph_error}")

        # Step 9: Clear inferred ontology (reasoning now outdated)
        manager.clear_inferred_ontology()
        print(f"   ✓ Cleared inferred ontology (reasoning results outdated)")

        # Step 10: Update world metadata with current counts
        from app_globals import get_world_manager, get_current_world_id
        world_mgr = get_world_manager()
        current_world_id = get_current_world_id()

        # Count annotations (for stats)
        all_individuals = list(manager.ontology.individuals())
        graphical_count = cleared_count
        annotations_count = len(all_individuals) - len(nodes_created) - len(edges_created)

        # Update metadata (using data['nodes'] and data['edges'] from request)
        world_mgr.update_world_metadata(current_world_id, {
            'node_count': len(data['nodes']),
            'edge_count': len(data['edges']),
            'annotation_count': max(0, annotations_count)
        })
        print(f"   ✓ Updated world metadata: {len(data['nodes'])} nodes, {len(data['edges'])} edges, {max(0, annotations_count)} annotations")

        print(f"{'='*60}")
        print(f"✅ SYNC COMPLETE")
        print(f"{'='*60}\n")

        # Elemente, die nicht in die Ontologie uebernommen werden konnten. Ohne
        # diese Rueckmeldung bliebe der Unterschied zwischen grafischem Modell
        # und Ontologie unbemerkt.
        warnings = getattr(manager, 'last_sync_warnings', [])
        if warnings:
            print(f"   ⚠️ {len(warnings)} Element(e) nicht uebernommen:")
            for w in warnings:
                print(f"      - {w['message']}")

        return jsonify({
            'success': True,
            'message': 'Model synchronized successfully',
            'warnings': warnings,
            'stats': {
                'nodes_synced': len(nodes_created),
                'edges_synced': len(edges_created),
                'properties_synced': len(properties_created),
                'positions_saved': len(node_positions),
                'graphical_cleared': cleared_count,
                'annotations_preserved': max(0, annotations_count),
                'not_synced': len(warnings)
            }
        }), 200

    except Exception as e:
        print(f"\n❌ SYNC ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'server_error'
        }), 500

    finally:
        # Always release lock
        _sync_lock.release()


@model_bp.route('/load', methods=['GET', 'OPTIONS'])
def load_model():
    """
    Load complete model state from backend for frontend initialization.

    This endpoint is called when:
    - Frontend starts up (page load/refresh)
    - User wants to restore from backend
    - Session needs to be recreated

    Response:
        {
            "success": true,
            "model": {
                "nodes": [
                    {
                        "id": "Training1",
                        "type": "FunctionNode",
                        "position": {"x": 150, "y": 200},
                        "data": {
                            "name": "ML Training",
                            "functionType": "ISO22989.Training"
                        }
                    }
                ],
                "edges": [...],
                "viewport": {
                    "x": 150,
                    "y": 200,
                    "zoom": 1.2
                },
                "metadata": {
                    "total_individuals": 127,
                    "graphical_elements": 45,
                    "annotations": 82,
                    "last_modified": "2025-12-13T10:30:00Z"
                }
            }
        }

    Features:
    - Loads from AIAS-instance.owl (working copy)
    - Includes node positions
    - Includes viewport state
    - Returns namespace-qualified class names
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200

    try:
        manager = get_ontology_manager()

        print(f"\n{'='*60}")
        print(f"📖 LOADING MODEL FROM BACKEND")
        print(f"{'='*60}")

        # Initialize collections
        nodes = []
        edges = []

        # Define class type mappings
        node_type_map = {
            'Function': 'FunctionNode',
            'Product': 'ProductNode',
            'Resource': 'ResourceNode'
        }

        edge_type_map = {
            'Assignment': 'AssignmentEdge',
            'Flow': 'FlowEdge',
            'Communication': 'CommunicationEdge'
        }

        # Extract all individuals
        all_individuals = list(manager.ontology.individuals())
        print(f"   Total individuals: {len(all_individuals)}")

        # Process each individual
        for individual in all_individuals:
            # Get ancestor classes
            ancestors = [cls.name for cls in individual.__class__.ancestors()
                        if hasattr(cls, 'name') and cls.name != 'Thing']

            # Check if this is a graphical node
            is_node = any(base in ancestors for base in ['Function', 'Product', 'Resource'])

            if is_node:
                # Determine base type
                base_type = None
                for base in ['Function', 'Product', 'Resource']:
                    if base in ancestors:
                        base_type = base
                        break

                if not base_type:
                    continue

                # Get namespace-qualified class name
                ns_class = manager._get_class_full_name(individual.__class__)

                # Get display name from hasName property, fallback to class name
                if hasattr(individual, 'hasName') and individual.hasName:
                    display_name = individual.hasName[0]
                else:
                    # Fallback: use class name if no hasName property
                    class_name = individual.__class__.name
                    if class_name and class_name not in ['Function', 'Resource', 'Product']:
                        display_name = class_name
                    else:
                        display_name = base_type

                # Build node object (position will be added from graphical state)
                node = {
                    'id': individual.name,
                    'type': node_type_map[base_type],
                    'position': {'x': 0, 'y': 0},  # Default, will be updated from graphical state
                    'data': {
                        'name': display_name  # Use hasName property or fallback
                    }
                }

                # Add type-specific field with namespace-qualified class name
                if base_type == 'Function':
                    node['data']['functionType'] = ns_class if ns_class else 'Function'
                elif base_type == 'Resource':
                    node['data']['resourceType'] = ns_class if ns_class else 'Resource'
                elif base_type == 'Product':
                    node['data']['productType'] = ns_class if ns_class else 'Product'

                nodes.append(node)

            # Check if this is a graphical edge
            is_edge = any(base in ancestors for base in ['Assignment', 'Flow', 'Communication'])

            if is_edge:
                # Determine edge type
                edge_base = None
                for base in ['Assignment', 'Flow', 'Communication']:
                    if base in ancestors:
                        edge_base = base
                        break

                if not edge_base:
                    continue

                # Debug: print edge being processed
                print(f"   🔍 Processing edge: {individual.name} ({edge_base})")

                # Find source and target by looking for nodes that reference this edge
                # Also detect direction based on which property is used

                # For each edge type, check all possible directional properties
                connected_info = {}  # {node_name: [properties_used]}

                for potential_node in all_individuals:
                    # Check all relevant properties for this edge type
                    properties_to_check = []

                    if edge_base == 'Assignment':
                        properties_to_check = ['isAssignedTo']
                    elif edge_base == 'Flow':
                        properties_to_check = ['hasFlow', 'hasInput', 'hasOutput']
                    elif edge_base == 'Communication':
                        properties_to_check = ['hasCommunication', 'hasInputCommunication', 'hasOutputCommunication']

                    for prop_name in properties_to_check:
                        # Try to get property values - handle both direct attributes and
                        # properties from imported ontologies (like VDI3682)
                        prop_values = []
                        try:
                            # First try direct attribute access
                            if hasattr(potential_node, prop_name):
                                prop_values = getattr(potential_node, prop_name, [])
                            else:
                                # For properties from imported ontologies, we need to search
                                # through all ontology properties
                                for onto in manager.world.ontologies.values():
                                    for prop in onto.object_properties():
                                        if prop.name == prop_name:
                                            # Get values using the property object
                                            prop_values = prop[potential_node]
                                            break
                                    if prop_values:
                                        break
                        except Exception:
                            prop_values = []

                        if not isinstance(prop_values, list):
                            prop_values = [prop_values] if prop_values else []

                        # Check if our edge is in the values
                        for val in prop_values:
                            if val and val.name == individual.name:
                                if potential_node.name not in connected_info:
                                    connected_info[potential_node.name] = []
                                connected_info[potential_node.name].append(prop_name)
                                break

                # Debug: print connected info
                print(f"      Connected info: {connected_info}")

                # Edges should have exactly 2 connected nodes (source and target)
                if len(connected_info) != 2:
                    print(f"   ⚠️ Edge {individual.name} ({edge_base}) has {len(connected_info)} connected nodes instead of 2")
                    continue

                connected_nodes = list(connected_info.keys())

                # Get display name from hasName property, fallback to class name
                if hasattr(individual, 'hasName') and individual.hasName:
                    edge_display_name = individual.hasName[0]
                else:
                    # Fallback: use class name if no hasName property
                    edge_class_name = individual.__class__.name
                    if edge_class_name and edge_class_name not in ['Assignment', 'Flow', 'Communication']:
                        edge_display_name = edge_class_name
                    else:
                        edge_display_name = edge_base

                # Determine source and target based on properties
                # For Flow/Communication: source has hasOutput, target has hasInput
                node1, node2 = connected_nodes[0], connected_nodes[1]
                props1 = connected_info[node1]
                props2 = connected_info[node2]

                source_node = node1
                target_node = node2
                arrow_forward = True
                arrow_backward = True

                if edge_base == 'Assignment':
                    # For Assignments: Function -> Resource
                    # Determine which node is the Function and which is the Resource
                    node1_obj = None
                    node2_obj = None
                    for ind in all_individuals:
                        if ind.name == node1:
                            node1_obj = ind
                        elif ind.name == node2:
                            node2_obj = ind

                    if node1_obj and node2_obj:
                        node1_ancestors = [cls.name for cls in node1_obj.__class__.ancestors()
                                          if hasattr(cls, 'name') and cls.name != 'Thing']
                        node2_ancestors = [cls.name for cls in node2_obj.__class__.ancestors()
                                          if hasattr(cls, 'name') and cls.name != 'Thing']

                        # Function is source, Resource is target
                        if 'Function' in node1_ancestors and 'Resource' in node2_ancestors:
                            source_node, target_node = node1, node2
                        elif 'Function' in node2_ancestors and 'Resource' in node1_ancestors:
                            source_node, target_node = node2, node1
                        # If both are same type, keep original order

                    arrow_forward = False
                    arrow_backward = False

                elif edge_base == 'Flow':
                    # Determine direction based on hasInput/hasOutput
                    if 'hasOutput' in props1 and 'hasInput' in props2:
                        source_node, target_node = node1, node2
                        arrow_forward = True
                        arrow_backward = False
                    elif 'hasInput' in props1 and 'hasOutput' in props2:
                        source_node, target_node = node2, node1
                        arrow_forward = True
                        arrow_backward = False
                    elif 'hasFlow' in props1 and 'hasFlow' in props2:
                        # Bidirectional
                        arrow_forward = True
                        arrow_backward = True
                    else:
                        # Fallback - check which makes sense
                        if 'hasOutput' in props1:
                            source_node, target_node = node1, node2
                        elif 'hasOutput' in props2:
                            source_node, target_node = node2, node1
                        arrow_forward = True
                        arrow_backward = True

                elif edge_base == 'Communication':
                    # Determine direction based on hasInputCommunication/hasOutputCommunication
                    if 'hasOutputCommunication' in props1 and 'hasInputCommunication' in props2:
                        source_node, target_node = node1, node2
                        arrow_forward = True
                        arrow_backward = False
                    elif 'hasInputCommunication' in props1 and 'hasOutputCommunication' in props2:
                        source_node, target_node = node2, node1
                        arrow_forward = True
                        arrow_backward = False
                    elif 'hasCommunication' in props1 and 'hasCommunication' in props2:
                        # Bidirectional
                        arrow_forward = True
                        arrow_backward = True
                    else:
                        # Fallback
                        if 'hasOutputCommunication' in props1:
                            source_node, target_node = node1, node2
                        elif 'hasOutputCommunication' in props2:
                            source_node, target_node = node2, node1
                        arrow_forward = True
                        arrow_backward = True

                print(f"      → Source: {source_node}, Target: {target_node}, Forward: {arrow_forward}, Backward: {arrow_backward}")

                # Build edge object
                edge = {
                    'id': individual.name,
                    'type': edge_type_map[edge_base],
                    'source': source_node,
                    'target': target_node,
                    'data': {
                        'name': edge_display_name,
                        'arrowForward': arrow_forward,
                        'arrowBackward': arrow_backward
                    }
                }

                # Add communication type if applicable
                if edge_base == 'Communication':
                    ns_class = manager._get_class_full_name(individual.__class__)
                    edge['data']['communicationType'] = ns_class if ns_class else 'Communication'

                edges.append(edge)

        # Load graphical state (viewport + node positions + edge waypoints + edge label offsets) from JSON
        world_id = str(id(manager.world))
        graphical_state_mgr = get_graphical_state_manager()
        graphical_state = graphical_state_mgr.load_state(world_id)

        if graphical_state:
            viewport = graphical_state.get('viewport', {'x': 0, 'y': 0, 'zoom': 1.0})
            node_positions = graphical_state.get('node_positions', {})
            edge_handles = graphical_state.get('edge_handles', {})
            edge_waypoints = graphical_state.get('edge_waypoints', {})
            edge_label_offsets = graphical_state.get('edge_label_offsets', {})
            edge_data = graphical_state.get('edge_data', {})

            # Update node positions from graphical state
            for node in nodes:
                if node['id'] in node_positions:
                    node['position'] = node_positions[node['id']]

            # Build node type lookup for handle validation
            node_type_lookup = {node['id']: node['type'] for node in nodes}

            # Define max anchor index per node type
            max_anchor_by_type = {
                'FunctionNode': 19,   # 20 anchors (0-19)
                'ResourceNode': 19,   # 20 anchors (0-19)
                'ProductNode': 9      # 10 anchors (0-9)
            }

            # Track which edges have swapped source/target for waypoint reversal
            swapped_edges = set()

            # Update edge handles (anchor points) from graphical state
            for edge in edges:
                if edge['id'] in edge_handles:
                    handles = edge_handles[edge['id']]

                    # Check if source/target were swapped during reconstruction
                    # by comparing with saved source/target IDs
                    saved_source = handles.get('source')
                    saved_target = handles.get('target')
                    current_source = edge['source']
                    current_target = edge['target']

                    # Determine if handles need to be swapped
                    swap_handles = False
                    if saved_source and saved_target:
                        if saved_source == current_target and saved_target == current_source:
                            # Source and target were swapped - swap handles too
                            swap_handles = True
                            swapped_edges.add(edge['id'])
                            print(f"   🔄 Edge {edge['id']}: source/target swapped, swapping handles and waypoints")

                    # Get the handles (potentially swapped)
                    source_handle = handles.get('sourceHandle')
                    target_handle = handles.get('targetHandle')
                    if swap_handles:
                        source_handle, target_handle = target_handle, source_handle

                    # Validate and apply sourceHandle
                    if source_handle:
                        source_type = node_type_lookup.get(edge['source'])
                        max_anchor = max_anchor_by_type.get(source_type, 19)
                        # Extract anchor index from "anchor-X" format
                        try:
                            anchor_index = int(source_handle.replace('anchor-', ''))
                            if anchor_index <= max_anchor:
                                edge['sourceHandle'] = source_handle
                            else:
                                print(f"   ⚠️ Invalid sourceHandle {source_handle} for {source_type} on edge {edge['id']}")
                        except (ValueError, AttributeError):
                            pass

                    # Validate and apply targetHandle
                    if target_handle:
                        target_type = node_type_lookup.get(edge['target'])
                        max_anchor = max_anchor_by_type.get(target_type, 19)
                        # Extract anchor index from "anchor-X" format
                        try:
                            anchor_index = int(target_handle.replace('anchor-', ''))
                            if anchor_index <= max_anchor:
                                edge['targetHandle'] = target_handle
                            else:
                                print(f"   ⚠️ Invalid targetHandle {target_handle} for {target_type} on edge {edge['id']}")
                        except (ValueError, AttributeError):
                            pass

            # Update edge waypoints from graphical state
            for edge in edges:
                if edge['id'] in edge_waypoints:
                    if 'data' not in edge:
                        edge['data'] = {}
                    waypoints = edge_waypoints[edge['id']]
                    # If source/target were swapped, reverse the waypoints order
                    if edge['id'] in swapped_edges:
                        waypoints = list(reversed(waypoints))
                        print(f"   🔄 Edge {edge['id']}: reversed waypoints order")
                    edge['data']['waypoints'] = waypoints

            # Update edge label offsets from graphical state
            for edge in edges:
                if edge['id'] in edge_label_offsets:
                    if 'data' not in edge:
                        edge['data'] = {}
                    edge['data']['labelOffset'] = edge_label_offsets[edge['id']]

            # Update edge data (showLabel, arrowForward, arrowBackward) from graphical state
            for edge in edges:
                if edge['id'] in edge_data:
                    if 'data' not in edge:
                        edge['data'] = {}
                    # Merge edge data properties
                    edge_props = edge_data[edge['id']]
                    if 'showLabel' in edge_props:
                        edge['data']['showLabel'] = edge_props['showLabel']
                    if 'arrowForward' in edge_props:
                        edge['data']['arrowForward'] = edge_props['arrowForward']
                    if 'arrowBackward' in edge_props:
                        edge['data']['arrowBackward'] = edge_props['arrowBackward']
                    if 'jumpOverCrossings' in edge_props:
                        edge['data']['jumpOverCrossings'] = edge_props['jumpOverCrossings']
        else:
            # No graphical state found, use defaults
            viewport = {'x': 0, 'y': 0, 'zoom': 1.0}

        # Calculate stats
        graphical_count = len(nodes) + len(edges)
        annotations_count = len(all_individuals) - graphical_count

        print(f"   ✓ Loaded {len(nodes)} nodes")
        print(f"   ✓ Loaded {len(edges)} edges")
        print(f"   ✓ Loaded viewport state")
        print(f"   ✓ {annotations_count} annotations preserved")
        print(f"{'='*60}\n")

        return jsonify({
            'success': True,
            'model': {
                'nodes': nodes,
                'edges': edges,
                'viewport': viewport,
                'metadata': {
                    'total_individuals': len(all_individuals),
                    'graphical_elements': graphical_count,
                    'annotations': annotations_count
                }
            }
        }), 200

    except Exception as e:
        print(f"\n❌ LOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'server_error'
        }), 500


@model_bp.route('/class-types', methods=['GET', 'OPTIONS'])
def get_class_types():
    """
    Get available class types with namespace-qualified names.

    This endpoint discovers all available classes for a given category
    and returns them with their full namespace prefixes.

    Query Parameters:
        category: 'function' | 'resource' | 'communication'
                  (default: 'function')

    Response:
        {
            "success": true,
            "classes": [
                {
                    "name": "ISO22989.Training",
                    "display_name": "Training (AI)",
                    "description": "ML model training process",
                    "namespace": "ISO22989"
                },
                {
                    "name": "ISO22989.Inference",
                    "display_name": "Inference (AI)",
                    "description": "Model inference/prediction",
                    "namespace": "ISO22989"
                }
            ]
        }

    Features:
    - Returns namespace-qualified names (e.g., "ISO22989.Training")
    - Includes human-readable display names
    - Includes descriptions from rdfs:comment
    - Organized by category (function/resource/communication)
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200

    try:
        category = request.args.get('category', 'function').lower()

        # Map category to base class
        base_class_map = {
            'function': 'Function',
            'resource': 'Resource',
            'communication': 'Communication'
        }

        base_class_name = base_class_map.get(category)
        if not base_class_name:
            return jsonify({
                'success': False,
                'error': f'Invalid category: {category}. Must be one of: function, resource, communication',
                'error_type': 'validation_error'
            }), 400

        manager = get_ontology_manager()

        print(f"\n📋 Discovering {category} class types...")

        # Get base class
        base_class = manager.get_class_by_name(base_class_name)
        if not base_class:
            return jsonify({
                'success': False,
                'error': f'Base class {base_class_name} not found in ontology',
                'error_type': 'not_found'
            }), 404

        # Get all subclasses (descendants)
        classes = []
        for subclass in base_class.descendants():
            # Skip the base class itself
            if subclass == base_class:
                continue

            # Get namespace-qualified name
            ns_name = manager._get_class_full_name(subclass)
            if not ns_name:
                # Fallback to simple name
                ns_name = subclass.name

            # Get description from rdfs:comment
            description = ""
            if hasattr(subclass, 'comment') and subclass.comment:
                comments = subclass.comment if isinstance(subclass.comment, list) else [subclass.comment]
                # Prefer German comment, fallback to first available
                for c in comments:
                    if hasattr(c, 'lang') and c.lang == 'de':
                        description = str(c)
                        break
                if not description and comments:
                    description = str(comments[0])

            # Extract namespace
            namespace = ns_name.split('.')[0] if '.' in ns_name else "AIAS"

            # Create display name
            display_name = f"{subclass.name}"
            if namespace and namespace != "AIAS":
                display_name = f"{subclass.name} ({namespace})"

            classes.append({
                'name': ns_name,
                'display_name': display_name,
                'description': description,
                'namespace': namespace
            })

        # Sort by display name
        classes.sort(key=lambda x: x['display_name'])

        print(f"   ✓ Found {len(classes)} {category} class types\n")

        return jsonify({
            'success': True,
            'classes': classes
        }), 200

    except Exception as e:
        print(f"\n❌ CLASS TYPES ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'server_error'
        }), 500


@model_bp.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """
    Health check endpoint for monitoring and debugging.

    Response:
        {
            "success": true,
            "status": "healthy",
            "ontology_loaded": true,
            "world_instance_id": "0x7f8a1c2d3e4f",
            "instance_file_exists": true,
            "individuals_count": 127,
            "graphical_elements_count": 45,
            "annotations_count": 82,
            "viewport_state": {"x": 0, "y": 0, "zoom": 1.0}
        }

    Features:
    - Reports singleton status
    - Counts individuals by type
    - Checks file existence
    - Returns World instance ID (for debugging)
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200

    try:
        from app_globals import get_singleton_status
        import os
        from expert_system.modules.ontology_manager import INSTANCE_ONTO_PATH

        # Get singleton status
        status = get_singleton_status()

        # Get detailed info if ontology is loaded
        manager = get_ontology_manager()

        if manager.ontology:
            individuals = list(manager.ontology.individuals())

            # Count graphical vs annotation individuals
            graphical_count = 0
            annotation_count = 0

            for ind in individuals:
                is_graphical = False
                for ancestor in ind.__class__.ancestors():
                    if hasattr(ancestor, 'name') and ancestor.name in [
                        'Function', 'Product', 'Resource',
                        'Assignment', 'Flow', 'Communication'
                    ]:
                        is_graphical = True
                        break

                if is_graphical:
                    graphical_count += 1
                else:
                    annotation_count += 1

            status['individuals_count'] = len(individuals)
            status['graphical_elements_count'] = graphical_count
            status['annotations_count'] = annotation_count

            # Load graphical state from JSON
            world_id = str(id(manager.world))
            graphical_state_mgr = get_graphical_state_manager()
            graphical_state = graphical_state_mgr.load_state(world_id)
            if graphical_state:
                status['viewport_state'] = graphical_state.get('viewport', {'x': 0, 'y': 0, 'zoom': 1.0})
                status['node_positions_count'] = len(graphical_state.get('node_positions', {}))
            else:
                status['viewport_state'] = {'x': 0, 'y': 0, 'zoom': 1.0}
                status['node_positions_count'] = 0

        # Check if instance file exists
        status['instance_file_exists'] = os.path.exists(INSTANCE_ONTO_PATH)
        status['status'] = 'healthy' if status['ontology_loaded'] else 'no_ontology'

        return jsonify({
            'success': True,
            **status
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e),
            'error_type': 'server_error'
        }), 500
