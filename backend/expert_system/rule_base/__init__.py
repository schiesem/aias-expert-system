import os

def get_rule_base_path():
    """Get the global rule base path (for templates/fallback)."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR)

def get_world_rule_path(world_id: str = None):
    """
    Get the rule path for a specific world.

    Args:
        world_id: World ID. If None, uses current world from app_globals.

    Returns:
        Path to world-specific rules directory
    """
    if world_id is None:
        # Import here to avoid circular dependency
        from app_globals import get_current_world_id, get_world_manager
        world_id = get_current_world_id()

    from app_globals import get_world_manager
    world_manager = get_world_manager()
    world_paths = world_manager.get_world_paths(world_id)

    return world_paths["rules_dir"]