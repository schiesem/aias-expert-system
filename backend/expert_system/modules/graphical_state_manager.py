"""
Graphical State Manager

Manages the graphical representation state (viewport, node positions) separately from
the semantic ontology. This maintains clean separation of concerns:
- OWL ontology = semantic knowledge only
- JSON files = UI/graphical state only

The graphical state is linked to the ontology via world_id to ensure consistency.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List


class GraphicalStateManager:
    """
    Manages graphical state storage and retrieval.

    Stores viewport state and node positions in JSON files within world directories.
    """

    def __init__(self, world_dir: str = None):
        """
        Initialize the graphical state manager.

        Args:
            world_dir: Specific world directory to use.
                      If None, uses legacy storage in received_data/
        """
        self.world_dir = world_dir

        # Ensure directory exists
        if world_dir:
            os.makedirs(world_dir, exist_ok=True)

    def _get_state_file_path(self, world_id: str = None) -> str:
        """
        Get the file path for graphical state.

        Args:
            world_id: Legacy parameter, ignored if world_dir is set

        Returns:
            Path to graphical_state.json
        """
        if self.world_dir:
            # New world-based storage: graphical_state.json in world folder
            return os.path.join(self.world_dir, "graphical_state.json")
        else:
            # Legacy storage: graphical_state_{world_id}.json in received_data
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            storage_dir = os.path.join(backend_dir, "received_data")
            os.makedirs(storage_dir, exist_ok=True)
            return os.path.join(storage_dir, f"graphical_state_{world_id}.json")

    def save_state(self, world_id: str = None, viewport: Dict = None, node_positions: Dict = None, edge_handles: Dict = None, edge_waypoints: Dict = None, edge_label_offsets: Dict = None, edge_data: Dict = None) -> bool:
        """
        Save graphical state.

        Args:
            world_id: Legacy parameter (for backward compatibility)
            viewport: Viewport state dict with x, y, zoom
            node_positions: Dict mapping node_id -> {x, y}
            edge_handles: Dict mapping edge_id -> {sourceHandle, targetHandle}
            edge_waypoints: Dict mapping edge_id -> [{x, y}, {x, y}, ...]
            edge_label_offsets: Dict mapping edge_id -> {x, y}
            edge_data: Dict mapping edge_id -> {showLabel, arrowForward, arrowBackward, etc.}

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            state = {
                "viewport": viewport or {"x": 0, "y": 0, "zoom": 1.0},
                "node_positions": node_positions or {},
                "edge_handles": edge_handles or {},
                "edge_waypoints": edge_waypoints or {},
                "edge_label_offsets": edge_label_offsets or {},
                "edge_data": edge_data or {},
                "last_updated": datetime.now().isoformat()
            }

            file_path = self._get_state_file_path(world_id)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved graphical state")
            print(f"   Viewport: {viewport}")
            print(f"   Node positions: {len(node_positions or {})} nodes")
            print(f"   Edge handles: {len(edge_handles or {})} edges")
            print(f"   Edge waypoints: {len(edge_waypoints or {})} edges")
            print(f"   Edge label offsets: {len(edge_label_offsets or {})} edges")
            print(f"   Edge data (showLabel, etc.): {len(edge_data or {})} edges")

            return True

        except Exception as e:
            print(f"❌ Error saving graphical state: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_state(self, world_id: str = None) -> Optional[Dict]:
        """
        Load graphical state.

        Args:
            world_id: Legacy parameter (for backward compatibility)

        Returns:
            State dict with 'viewport' and 'node_positions', or None if not found
        """
        try:
            file_path = self._get_state_file_path(world_id)

            if not os.path.exists(file_path):
                print(f"ℹ️ No graphical state found")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            print(f"📖 Loaded graphical state")
            print(f"   Viewport: {state.get('viewport')}")
            print(f"   Node positions: {len(state.get('node_positions', {}))} nodes")
            print(f"   Edge handles: {len(state.get('edge_handles', {}))} edges")
            print(f"   Edge waypoints: {len(state.get('edge_waypoints', {}))} edges")
            print(f"   Edge label offsets: {len(state.get('edge_label_offsets', {}))} edges")
            print(f"   Edge data (showLabel, etc.): {len(state.get('edge_data', {}))} edges")

            return state

        except Exception as e:
            print(f"❌ Error loading graphical state: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_viewport(self, world_id: str, viewport: Dict) -> bool:
        """
        Update only the viewport state, preserving node positions, edge handles, edge waypoints, edge label offsets, and edge data.

        Args:
            world_id: Unique identifier for the ontology World instance
            viewport: New viewport state dict with x, y, zoom

        Returns:
            True if updated successfully, False otherwise
        """
        # Load existing state
        state = self.load_state(world_id)

        if state is None:
            # No existing state, create new one with empty positions, handles, waypoints, and data
            return self.save_state(world_id, viewport, {}, {}, {}, {}, {})

        # Update viewport only, preserve all existing data
        return self.save_state(
            world_id,
            viewport,
            state.get('node_positions', {}),
            state.get('edge_handles', {}),
            state.get('edge_waypoints', {}),
            state.get('edge_label_offsets', {}),
            state.get('edge_data', {})
        )

    def update_node_position(self, world_id: str, node_id: str, x: float, y: float) -> bool:
        """
        Update a single node's position, preserving edge handles and waypoints.

        Args:
            world_id: Unique identifier for the ontology World instance
            node_id: ID of the node to update
            x: X coordinate
            y: Y coordinate

        Returns:
            True if updated successfully, False otherwise
        """
        # Load existing state
        state = self.load_state(world_id)

        if state is None:
            # No existing state, create new one
            viewport = {"x": 0, "y": 0, "zoom": 1.0}
            node_positions = {node_id: {"x": x, "y": y}}
            return self.save_state(world_id, viewport, node_positions, {}, {}, {}, {})

        # Update single node position, preserve all existing data
        node_positions = state.get('node_positions', {})
        node_positions[node_id] = {"x": x, "y": y}

        return self.save_state(
            world_id,
            state.get('viewport'),
            node_positions,
            state.get('edge_handles', {}),
            state.get('edge_waypoints', {}),
            state.get('edge_label_offsets', {}),
            state.get('edge_data', {})
        )

    def update_node_positions(self, world_id: str, node_positions: Dict) -> bool:
        """
        Update multiple node positions at once, preserving edge handles and waypoints.

        Args:
            world_id: Unique identifier for the ontology World instance
            node_positions: Dict mapping node_id -> {x, y}

        Returns:
            True if updated successfully, False otherwise
        """
        # Load existing state
        state = self.load_state(world_id)

        if state is None:
            # No existing state, create new one
            viewport = {"x": 0, "y": 0, "zoom": 1.0}
            return self.save_state(world_id, viewport, node_positions, {}, {}, {}, {})

        # Merge with existing positions, preserve all existing data
        existing_positions = state.get('node_positions', {})
        existing_positions.update(node_positions)

        return self.save_state(
            world_id,
            state.get('viewport'),
            existing_positions,
            state.get('edge_handles', {}),
            state.get('edge_waypoints', {}),
            state.get('edge_label_offsets', {}),
            state.get('edge_data', {})
        )

    def delete_state(self, world_id: str) -> bool:
        """
        Delete graphical state for a given world_id.

        Args:
            world_id: Unique identifier for the ontology World instance

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self._get_state_file_path(world_id)

            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Deleted graphical state for world_id={world_id}")
                return True
            else:
                print(f"ℹ️ No graphical state to delete for world_id={world_id}")
                return True

        except Exception as e:
            print(f"❌ Error deleting graphical state: {e}")
            return False

    def list_all_states(self) -> List[Dict]:
        """
        List all stored graphical states.

        Returns:
            List of state metadata dicts
        """
        states = []

        try:
            # If using world_dir mode, only return the current world's state
            if self.world_dir:
                file_path = self._get_state_file_path()
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        state = json.load(f)

                    states.append({
                        'world_id': os.path.basename(self.world_dir).replace('world_', ''),
                        'last_updated': state.get('last_updated'),
                        'node_count': len(state.get('node_positions', {})),
                        'file_path': file_path
                    })
                return states

            # Legacy mode: list all graphical_state_*.json files
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            storage_dir = os.path.join(backend_dir, "received_data")

            if not os.path.exists(storage_dir):
                return []

            for filename in os.listdir(storage_dir):
                if filename.startswith("graphical_state_") and filename.endswith(".json"):
                    file_path = os.path.join(storage_dir, filename)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            state = json.load(f)

                        states.append({
                            'world_id': state.get('world_id'),
                            'last_updated': state.get('last_updated'),
                            'node_count': len(state.get('node_positions', {})),
                            'file_path': file_path
                        })
                    except Exception as e:
                        print(f"⚠️ Error reading {filename}: {e}")
                        continue

            return states

        except Exception as e:
            print(f"❌ Error listing graphical states: {e}")
            return []

    def cleanup_old_states(self, keep_latest: int = 5) -> int:
        """
        Clean up old graphical state files, keeping only the most recent ones.

        Args:
            keep_latest: Number of most recent states to keep

        Returns:
            Number of states deleted
        """
        try:
            states = self.list_all_states()

            if len(states) <= keep_latest:
                print(f"ℹ️ No cleanup needed, only {len(states)} states exist")
                return 0

            # Sort by last_updated (most recent first)
            states.sort(key=lambda s: s.get('last_updated', ''), reverse=True)

            # Delete older states
            deleted_count = 0
            for state in states[keep_latest:]:
                if os.path.exists(state['file_path']):
                    os.remove(state['file_path'])
                    deleted_count += 1
                    print(f"🗑️ Deleted old state: {state['world_id']}")

            print(f"✅ Cleanup complete: deleted {deleted_count} old states")
            return deleted_count

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return 0
