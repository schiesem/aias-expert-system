"""
app_globals.py

Global singleton instances for the Flask application.
Ensures single OntologyManager World across all requests.

This module provides application-level singleton accessors for:
- WorldManager: Manages modeling worlds (isolated sessions)
- OntologyManager: Core ontology lifecycle management
- AnnotationManager: Semantic annotation management
- GraphicalStateManager: Viewport and node position storage

All managers share the same world context, ensuring consistent
state across all backend operations.
"""

from expert_system.modules.world_manager import WorldManager
from expert_system.modules.ontology_manager import OntologyManager
from expert_system.modules.annotation_manager import AnnotationManager
from expert_system.modules.graphical_state_manager import GraphicalStateManager

# Global singleton instances
_world_manager = None
_ontology_manager = None
_annotation_manager = None
_graphical_state_manager = None
_current_world_id = None


def get_world_manager() -> WorldManager:
    """
    Get or create the global WorldManager singleton.

    Returns:
        WorldManager: Global singleton instance
    """
    global _world_manager

    if _world_manager is None:
        print("🔧 Initializing global WorldManager...")
        _world_manager = WorldManager()
        print("✅ Global WorldManager initialized")

    return _world_manager


def get_current_world_id() -> str:
    """
    Get or create the current world ID.

    On first access, this will either:
    - Use existing current world from .current_world file
    - Use most recent world if available
    - Create new default world if none exist

    Returns:
        str: Current world ID
    """
    global _current_world_id

    if _current_world_id is None:
        world_mgr = get_world_manager()
        _current_world_id = world_mgr.get_or_create_default_world()
        print(f"🌍 Current world: {_current_world_id}")

    return _current_world_id


def set_current_world_id(world_id: str) -> bool:
    """
    Switch to a different world.

    This resets all singletons to force reload with the new world.

    Args:
        world_id: World ID to switch to

    Returns:
        bool: True if successful
    """
    global _current_world_id

    world_mgr = get_world_manager()

    # Verify world exists
    if not world_mgr.world_exists(world_id):
        print(f"❌ World {world_id} does not exist")
        return False

    # Save current ontology before switching (to preserve any unsaved annotations/relationships)
    if _ontology_manager:
        try:
            print("💾 Saving current ontology before world switch...")
            _ontology_manager.save_ontology()
            print("✅ Ontology saved successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not save ontology before switch: {e}")

    # Set as current world
    if not world_mgr.set_current_world(world_id):
        return False

    # Reset all singletons to force reload with new world
    reset_singletons()
    _current_world_id = world_id

    print(f"✅ Switched to world: {world_id}")
    return True


def get_ontology_manager() -> OntologyManager:
    """
    Get or create the global OntologyManager singleton.

    The singleton is initialized on first access and reused for all
    subsequent requests. This ensures:
    - Single owlready2 World instance across all operations
    - Annotations persist across model synchronizations
    - No duplicate loading of ontology files

    Returns:
        OntologyManager: Global singleton instance
    """
    global _ontology_manager

    if _ontology_manager is None:
        print("🔧 Initializing global OntologyManager...")

        # Get current world paths
        world_mgr = get_world_manager()
        world_id = get_current_world_id()
        paths = world_mgr.get_world_paths(world_id)

        # Initialize with world directory
        _ontology_manager = OntologyManager(world_dir=paths['world_dir'])

        # Load from EXISTING working copy (never overwrite!)
        # This preserves annotations and existing model state
        _ontology_manager.load_from_working_copy()
        print(f"✅ Global OntologyManager initialized for world {world_id}")

    return _ontology_manager


def get_annotation_manager() -> AnnotationManager:
    """
    Get or create the global AnnotationManager singleton.

    Uses the global OntologyManager to ensure annotations are
    stored in the same World as graphical elements.

    Returns:
        AnnotationManager: Global singleton instance
    """
    global _annotation_manager

    if _annotation_manager is None:
        onto_mgr = get_ontology_manager()
        _annotation_manager = AnnotationManager(onto_mgr)
        world_id = get_current_world_id()
        print(f"✅ Global AnnotationManager initialized for world {world_id}")

    return _annotation_manager


def get_graphical_state_manager() -> GraphicalStateManager:
    """
    Get or create the global GraphicalStateManager singleton.

    Returns:
        GraphicalStateManager: Global singleton instance
    """
    global _graphical_state_manager

    if _graphical_state_manager is None:
        # Get current world paths
        world_mgr = get_world_manager()
        world_id = get_current_world_id()
        paths = world_mgr.get_world_paths(world_id)

        # Initialize with world directory
        _graphical_state_manager = GraphicalStateManager(world_dir=paths['world_dir'])
        print(f"✅ Global GraphicalStateManager initialized for world {world_id}")

    return _graphical_state_manager


def reset_singletons():
    """
    Reset global singletons (for testing or world switching).

    WARNING: Only call this when switching worlds or starting fresh.
    This will:
    - Unload the current ontology World
    - Clear all in-memory state
    - Force reinitialization on next access

    Use cases:
    - Unit testing (clean state between tests)
    - Switching to a different world
    - Recovering from corrupted state
    """
    global _ontology_manager, _annotation_manager, _graphical_state_manager

    if _ontology_manager:
        _ontology_manager.unload_ontologie()
        _ontology_manager = None

    _annotation_manager = None
    _graphical_state_manager = None
    print("🔄 Global singletons reset")


def get_singleton_status() -> dict:
    """
    Get current status of global singletons.

    Returns:
        dict: Status information including:
            - world_manager_initialized: bool
            - ontology_manager_initialized: bool
            - annotation_manager_initialized: bool
            - graphical_state_manager_initialized: bool
            - current_world_id: str
            - ontology_loaded: bool
            - owlready_world_id: str (memory address of World instance)
            - individuals_count: int (if ontology loaded)
    """
    status = {
        'world_manager_initialized': _world_manager is not None,
        'ontology_manager_initialized': _ontology_manager is not None,
        'annotation_manager_initialized': _annotation_manager is not None,
        'graphical_state_manager_initialized': _graphical_state_manager is not None,
        'current_world_id': _current_world_id,
        'ontology_loaded': False,
        'owlready_world_id': None,
        'individuals_count': 0
    }

    if _ontology_manager and _ontology_manager.world:
        status['owlready_world_id'] = str(id(_ontology_manager.world))

        if _ontology_manager.ontology:
            status['ontology_loaded'] = True
            status['individuals_count'] = len(list(_ontology_manager.ontology.individuals()))

    return status
