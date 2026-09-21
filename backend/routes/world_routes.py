# routes/world_routes.py

"""
World Management Routes

API endpoints for managing modeling worlds (isolated sessions).
Each world has its own:
- AIAS-instance.owl (semantic model)
- AIAS-inferred.owl (reasoning results)
- graphical_state.json (UI state)
- metadata.json (world metadata)
"""

from flask import Blueprint, jsonify, request
from app_globals import (
    get_world_manager,
    get_current_world_id,
    set_current_world_id,
    reset_singletons
)
from expert_system.modules.world_manager import DEFAULT_WORLD_ID

world_bp = Blueprint("world_bp", __name__, url_prefix="/api/worlds")


@world_bp.route("", methods=["GET"], strict_slashes=False)
def list_worlds():
    """
    Get list of all available worlds.

    Returns:
        JSON: {
            success: bool,
            worlds: [
                {
                    world_id: str,
                    name: str,
                    description: str,
                    created_at: str,
                    last_modified: str,
                    node_count: int,
                    edge_count: int,
                    annotation_count: int
                }
            ],
            current_world_id: str
        }
    """
    try:
        world_mgr = get_world_manager()
        worlds = world_mgr.list_worlds()
        current_id = get_current_world_id()

        return jsonify({
            "success": True,
            "worlds": worlds,
            "current_world_id": current_id
        }), 200

    except Exception as e:
        print(f"❌ Error listing worlds: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("", methods=["POST"], strict_slashes=False)
def create_world():
    """
    Create a new world.

    Request body:
        {
            name: str (optional),
            description: str (optional),
            project_name: str (optional),
            dmme_phase: int (optional, 2/3/8/9),
            parent_world_id: str (optional)
        }

    Returns:
        JSON: {
            success: bool,
            world: {world metadata},
            message: str
        }
    """
    try:
        data = request.get_json() or {}
        name = data.get("name")
        description = data.get("description")
        project_name = data.get("project_name")
        dmme_phase = data.get("dmme_phase")
        parent_world_id = data.get("parent_world_id")

        world_mgr = get_world_manager()
        metadata = world_mgr.create_world(
            name=name,
            description=description,
            project_name=project_name,
            dmme_phase=dmme_phase,
            parent_world_id=parent_world_id
        )

        return jsonify({
            "success": True,
            "world": metadata,
            "message": f"Created world: {metadata['name']}"
        }), 201

    except Exception as e:
        print(f"❌ Error creating world: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/current", methods=["GET"], strict_slashes=False)
def get_current_world():
    """
    Get the currently active world.

    Returns:
        JSON: {
            success: bool,
            world: {world metadata},
            world_id: str
        }
    """
    try:
        world_mgr = get_world_manager()
        world_id = get_current_world_id()
        metadata = world_mgr.get_world_metadata(world_id)

        if not metadata:
            return jsonify({
                "success": False,
                "error": f"World {world_id} not found"
            }), 404

        return jsonify({
            "success": True,
            "world": metadata,
            "world_id": world_id
        }), 200

    except Exception as e:
        print(f"❌ Error getting current world: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/<world_id>", methods=["GET"], strict_slashes=False)
def get_world(world_id):
    """
    Get metadata for a specific world.

    Args:
        world_id: World ID

    Returns:
        JSON: {
            success: bool,
            world: {world metadata}
        }
    """
    try:
        world_mgr = get_world_manager()
        metadata = world_mgr.get_world_metadata(world_id)

        if not metadata:
            return jsonify({
                "success": False,
                "error": f"World {world_id} not found"
            }), 404

        return jsonify({
            "success": True,
            "world": metadata
        }), 200

    except Exception as e:
        print(f"❌ Error getting world {world_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/<world_id>/activate", methods=["POST"], strict_slashes=False)
def activate_world(world_id):
    """
    Switch to a different world.

    This will:
    - Verify the world exists
    - Set it as current
    - Reset all singletons to reload with new world

    Args:
        world_id: World ID to activate

    Returns:
        JSON: {
            success: bool,
            world_id: str,
            message: str
        }
    """
    try:
        if set_current_world_id(world_id):
            return jsonify({
                "success": True,
                "world_id": world_id,
                "message": f"Switched to world: {world_id}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to activate world {world_id}"
            }), 400

    except Exception as e:
        print(f"❌ Error activating world {world_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/<world_id>", methods=["PUT"], strict_slashes=False)
def update_world(world_id):
    """
    Update world metadata.

    Request body:
        {
            name: str (optional),
            description: str (optional)
        }

    Args:
        world_id: World ID

    Returns:
        JSON: {
            success: bool,
            world: {updated metadata},
            message: str
        }
    """
    try:
        data = request.get_json() or {}

        world_mgr = get_world_manager()

        # Update metadata
        updates = {}
        if "name" in data:
            updates["name"] = data["name"]
        if "description" in data:
            updates["description"] = data["description"]

        if not world_mgr.update_world_metadata(world_id, updates):
            return jsonify({
                "success": False,
                "error": f"World {world_id} not found"
            }), 404

        # Get updated metadata
        metadata = world_mgr.get_world_metadata(world_id)

        return jsonify({
            "success": True,
            "world": metadata,
            "message": f"Updated world: {world_id}"
        }), 200

    except Exception as e:
        print(f"❌ Error updating world {world_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/<world_id>", methods=["DELETE"], strict_slashes=False)
def delete_world(world_id):
    """
    Delete a world and all its data.

    WARNING: This cannot be undone!

    Args:
        world_id: World ID to delete

    Returns:
        JSON: {
            success: bool,
            message: str
        }
    """
    try:
        world_mgr = get_world_manager()

        # Don't allow deleting default world
        if world_id == DEFAULT_WORLD_ID:
            return jsonify({
                "success": False,
                "error": "Cannot delete the permanent default world."
            }), 400

        # Don't allow deleting current world
        current_id = get_current_world_id()
        if world_id == current_id:
            return jsonify({
                "success": False,
                "error": "Cannot delete the currently active world. Switch to another world first."
            }), 400

        if world_mgr.delete_world(world_id):
            return jsonify({
                "success": True,
                "message": f"Deleted world: {world_id}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"World {world_id} not found"
            }), 404

    except Exception as e:
        print(f"❌ Error deleting world {world_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/<world_id>/export", methods=["GET"], strict_slashes=False)
def export_world(world_id):
    """
    Export a world to a zip file.

    Args:
        world_id: World ID to export

    Returns:
        Zip file download
    """
    try:
        import tempfile
        import os
        from flask import send_file

        world_mgr = get_world_manager()

        # Create temporary export path
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            export_path = tmp.name

        if not world_mgr.export_world(world_id, export_path):
            return jsonify({
                "success": False,
                "error": f"World {world_id} not found"
            }), 404

        # Get world metadata for filename
        metadata = world_mgr.get_world_metadata(world_id)
        filename = f"{metadata.get('name', world_id).replace(' ', '_')}.zip"

        return send_file(
            export_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )

    except Exception as e:
        print(f"❌ Error exporting world {world_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/import", methods=["POST"], strict_slashes=False)
def import_world():
    """
    Import a world from a zip file.

    Request:
        Multipart form data with 'file' field

    Request body (JSON):
        {
            name: str (optional - new name for imported world)
        }

    Returns:
        JSON: {
            success: bool,
            world: {world metadata},
            message: str
        }
    """
    try:
        import tempfile
        import os

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file uploaded"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400

        # Get optional new name
        new_name = request.form.get('name')

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            file.save(tmp.name)
            zip_path = tmp.name

        try:
            world_mgr = get_world_manager()
            world_id = world_mgr.import_world(zip_path, new_name=new_name)

            if not world_id:
                return jsonify({
                    "success": False,
                    "error": "Failed to import world"
                }), 500

            # Get imported world metadata
            metadata = world_mgr.get_world_metadata(world_id)

            return jsonify({
                "success": True,
                "world": metadata,
                "message": f"Imported world: {metadata['name']}"
            }), 201

        finally:
            # Clean up temporary file
            os.unlink(zip_path)

    except Exception as e:
        print(f"❌ Error importing world: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/<world_id>/create-phase", methods=["POST"], strict_slashes=False)
def create_phase_from_world(world_id):
    """
    Create next phase model from current world.

    Request body:
        {
            project_name: str (required),
            phase_name: str (optional),
            auto_switch: bool (optional, default: true)
        }

    Args:
        world_id: Parent world ID

    Returns:
        JSON: {
            success: bool,
            world: {new world metadata},
            phase_info: {
                phase_number: int,
                phase_label: str,
                parent_world_id: str
            },
            message: str
        }
    """
    try:
        data = request.get_json() or {}

        # Validate required fields
        project_name = data.get("project_name")
        if not project_name:
            return jsonify({
                "success": False,
                "error": "project_name is required"
            }), 400

        phase_name = data.get("phase_name")
        auto_switch = data.get("auto_switch", True)

        world_mgr = get_world_manager()

        # Create phase world
        new_world = world_mgr.create_phase_world(
            parent_world_id=world_id,
            project_name=project_name,
            custom_name=phase_name
        )

        # Auto-switch if requested
        if auto_switch:
            set_current_world_id(new_world["world_id"])
            reset_singletons()

        return jsonify({
            "success": True,
            "world": new_world,
            "phase_info": {
                "phase_number": new_world["dmme_phase"],
                "phase_label": new_world["phase_label"],
                "parent_world_id": world_id
            },
            "message": f"Created {new_world['phase_label']} from {world_id}"
        }), 201

    except ValueError as e:
        # Validation errors
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        print(f"❌ Error creating phase world: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/projects", methods=["GET"], strict_slashes=False)
def list_projects():
    """
    Get list of all projects with summary info.

    Returns:
        JSON: {
            success: bool,
            projects: [
                {
                    project_name: str,
                    world_count: int,
                    phases: [int],
                    last_modified: str
                }
            ]
        }
    """
    try:
        world_mgr = get_world_manager()
        projects = world_mgr.list_projects()

        return jsonify({
            "success": True,
            "projects": projects
        }), 200

    except Exception as e:
        print(f"❌ Error listing projects: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@world_bp.route("/project/<project_name>", methods=["GET"], strict_slashes=False)
def get_project_worlds(project_name):
    """
    Get all worlds for a specific project.

    Args:
        project_name: Project name

    Returns:
        JSON: {
            success: bool,
            project_name: str,
            worlds: [world metadata]
        }
    """
    try:
        world_mgr = get_world_manager()
        worlds = world_mgr.get_project_worlds(project_name)

        return jsonify({
            "success": True,
            "project_name": project_name,
            "worlds": worlds
        }), 200

    except Exception as e:
        print(f"❌ Error getting project worlds: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
