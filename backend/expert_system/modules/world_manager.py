"""
World Manager

Manages modeling worlds - isolated sessions with their own ontology and graphical state.
Each world has its own folder containing:
- AIAS-instance.owl (semantic model)
- AIAS-inferred.owl (reasoning results)
- graphical_state.json (UI state)
- metadata.json (world metadata)
"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import hashlib


# Default world constant
DEFAULT_WORLD_ID = "000000000000"


# DMME Phase definitions
DMME_PHASES = {
    2: {
        "label": "Ist-Modell",
        "name": "Technical Understanding",
        "description": "Current state analysis and understanding"
    },
    3: {
        "label": "Konzept-Modell",
        "name": "Technical Realization",
        "description": "Conceptual design and architecture"
    },
    8: {
        "label": "Implementation-Modell",
        "name": "Technical Implementation",
        "description": "Detailed implementation model"
    },
    9: {
        "label": "Deployment-Modell",
        "name": "Deployment",
        "description": "Deployment and rollout model"
    }
}

# Valid phase transitions (strict lineage)
PHASE_TRANSITIONS = {
    2: 3,  # Ist → Konzept
    3: 8,  # Konzept → Implementation
    8: 9   # Implementation → Deployment
}


class WorldManager:
    """
    Manages modeling worlds with isolated storage.

    Each world is a complete modeling session with its own:
    - Ontology instance
    - Graphical state
    - Reasoning results
    - Metadata
    """

    def __init__(self, base_dir: str = None):
        """
        Initialize the world manager.

        Args:
            base_dir: Base directory for storing worlds.
                     Defaults to backend/modeling-worlds/
        """
        if base_dir is None:
            # Default to modeling-worlds directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            base_dir = os.path.join(backend_dir, "modeling-worlds")

        self.base_dir = base_dir
        self.current_world_file = os.path.join(base_dir, ".current_world")

        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)

        # Ensure default world exists
        self.ensure_default_world()

    def ensure_default_world(self) -> str:
        """
        Ensure the permanent default world exists.
        Creates it if missing. Always sets it as current if no other world is active.

        Returns:
            Default world ID (always "000000000000")
        """
        world_id = DEFAULT_WORLD_ID
        world_dir = self._get_world_dir(world_id)
        metadata_path = os.path.join(world_dir, "metadata.json")

        # Check if default world already exists
        if os.path.exists(metadata_path):
            # Default world exists, ensure it's active if no current world
            current_id = self.get_current_world_id()
            if not current_id or not self.get_world_metadata(current_id):
                self.set_current_world(world_id)
            return world_id

        # Create default world with fixed ID
        os.makedirs(world_dir, exist_ok=True)

        metadata = {
            "world_id": world_id,
            "name": "Default World",
            "description": "Permanent default workspace for testing and scratch work",
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "node_count": 0,
            "edge_count": 0,
            "annotation_count": 0,
            # Not part of any project
            "project_name": None,
            "dmme_phase": None,
            "phase_label": None,
            "parent_world_id": None,
            "child_world_ids": [],
            "phase_created_at": None,
            "is_phase_model": False,
            "is_default": True  # Special marker
        }

        # Save metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"🌍 Created permanent default world: {world_id}")

        # Copy rule files to world directory
        self._copy_rules_to_world(world_id)

        # Set as current world if no other world is active
        current_id = self.get_current_world_id()
        if not current_id or not self.get_world_metadata(current_id):
            self.set_current_world(world_id)

        return world_id

    def _get_world_dir(self, world_id: str) -> str:
        """Get the directory path for a world."""
        return os.path.join(self.base_dir, f"world_{world_id}")

    def _generate_world_id(self, name: str = None) -> str:
        """
        Generate a unique world ID.

        Args:
            name: Optional name to include in hash

        Returns:
            Unique world ID
        """
        if name:
            # Use hash of name + timestamp for reproducibility with uniqueness
            content = f"{name}_{datetime.now().isoformat()}"
            hash_obj = hashlib.sha256(content.encode())
            return hash_obj.hexdigest()[:16]
        else:
            # Use timestamp-based ID
            return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _update_aisystem_name(self, owl_file_path: str, new_name: str, new_world_id: str = None) -> bool:
        """
        Update the AISystem node's hasName property and optionally its ID in an OWL file.

        Args:
            owl_file_path: Path to the AIAS-instance.owl file
            new_name: New name for the AISystem node
            new_world_id: New world ID to update the individual's rdf:about (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            import re

            # Read the OWL file
            with open(owl_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Pattern to find AISystem node and its hasName property
            # Matches: <hasName rdf:datatype="...">OLD_NAME</hasName>
            # within an AISystem individual
            pattern = r'(<owl:NamedIndividual[^>]*>[\s\S]*?<rdf:type rdf:resource="http://www\.semanticweb\.org/schieseck/ISO22989#AISystem"/>[\s\S]*?<hasName[^>]*>)([^<]+)(</hasName>[\s\S]*?</owl:NamedIndividual>)'

            # Replace the hasName value
            def replace_name(match):
                return match.group(1) + new_name + match.group(3)

            updated_content = re.sub(pattern, replace_name, content)

            # Also update the AISystem individual's ID (rdf:about) if new_world_id is provided
            if new_world_id:
                # Pattern to find the AISystem individual's rdf:about attribute
                # Matches: <owl:NamedIndividual rdf:about="#world_OLDID">
                # followed by AISystem type declaration
                id_pattern = r'(<owl:NamedIndividual rdf:about="#)(world_[a-zA-Z0-9_]+)(">[\s\S]*?<rdf:type rdf:resource="http://www\.semanticweb\.org/schieseck/ISO22989#AISystem"/>)'

                def replace_world_id(match):
                    return match.group(1) + f"world_{new_world_id}" + match.group(3)

                updated_content = re.sub(id_pattern, replace_world_id, updated_content)
                print(f"    → AISystem ID updated: world_{new_world_id}")

            # Write back to file
            with open(owl_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print(f"    → AISystem name updated: {new_name}")
            return True

        except Exception as e:
            print(f"    ⚠️ Failed to update AISystem name: {e}")
            return False

    def create_world(self, name: str = None, description: str = None,
                     project_name: str = None, dmme_phase: int = None,
                     parent_world_id: str = None) -> Dict:
        """
        Create a new modeling world.

        Args:
            name: Optional world name
            description: Optional world description
            project_name: Optional project name for grouping phase models
            dmme_phase: Optional DMME phase number (2, 3, 8, 9)
            parent_world_id: Optional parent world ID (for phase lineage)

        Returns:
            World metadata dict
        """
        # Generate unique ID
        world_id = self._generate_world_id(name)
        world_dir = self._get_world_dir(world_id)

        # Create world directory
        os.makedirs(world_dir, exist_ok=True)

        # Create metadata with phase information
        metadata = {
            "world_id": world_id,
            "name": name or f"World {world_id}",
            "description": description or "",
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "node_count": 0,
            "edge_count": 0,
            "annotation_count": 0,
            # Phase versioning fields
            "project_name": project_name,
            "dmme_phase": dmme_phase,
            "phase_label": DMME_PHASES[dmme_phase]["label"] if dmme_phase in DMME_PHASES else None,
            "parent_world_id": parent_world_id,
            "child_world_ids": [],
            "phase_created_at": datetime.now().isoformat() if dmme_phase else None,
            "is_phase_model": dmme_phase is not None
        }

        # Save metadata
        metadata_path = os.path.join(world_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        phase_info = f" [Phase {dmme_phase}: {metadata['phase_label']}]" if dmme_phase else ""
        print(f"🌍 Created new world: {world_id} ({metadata['name']}){phase_info}")

        # Copy rule files to world directory
        self._copy_rules_to_world(world_id)

        return metadata

    def get_world_metadata(self, world_id: str) -> Optional[Dict]:
        """
        Get metadata for a world.

        Args:
            world_id: World ID

        Returns:
            Metadata dict or None if not found
        """
        world_dir = self._get_world_dir(world_id)
        metadata_path = os.path.join(world_dir, "metadata.json")

        if not os.path.exists(metadata_path):
            return None

        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def update_world_metadata(self, world_id: str, updates: Dict) -> bool:
        """
        Update world metadata.

        Args:
            world_id: World ID
            updates: Dict of fields to update

        Returns:
            True if successful
        """
        metadata = self.get_world_metadata(world_id)
        if not metadata:
            return False

        # Update fields
        metadata.update(updates)
        metadata["last_modified"] = datetime.now().isoformat()

        # Save
        world_dir = self._get_world_dir(world_id)
        metadata_path = os.path.join(world_dir, "metadata.json")

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return True

    def list_worlds(self) -> List[Dict]:
        """
        List all available worlds.

        Returns:
            List of world metadata dicts
        """
        worlds = []

        try:
            for item in os.listdir(self.base_dir):
                if item.startswith("world_") and os.path.isdir(os.path.join(self.base_dir, item)):
                    world_id = item.replace("world_", "")
                    metadata = self.get_world_metadata(world_id)
                    if metadata:
                        worlds.append(metadata)

            # Sort by last modified (most recent first)
            worlds.sort(key=lambda w: w.get("last_modified", ""), reverse=True)

            return worlds

        except Exception as e:
            print(f"❌ Error listing worlds: {e}")
            return []

    def delete_world(self, world_id: str) -> bool:
        """
        Delete a world and all its data.

        Args:
            world_id: World ID to delete

        Returns:
            True if successful
        """
        # Prevent deletion of default world
        if world_id == DEFAULT_WORLD_ID:
            print(f"🚫 Cannot delete the permanent default world")
            return False

        world_dir = self._get_world_dir(world_id)

        if not os.path.exists(world_dir):
            print(f"⚠️ World {world_id} not found")
            return False

        try:
            shutil.rmtree(world_dir)
            print(f"🗑️ Deleted world: {world_id}")

            # If this was the current world, clear it
            if self.get_current_world_id() == world_id:
                self.clear_current_world()

            return True

        except Exception as e:
            print(f"❌ Error deleting world {world_id}: {e}")
            return False

    def get_current_world_id(self) -> Optional[str]:
        """
        Get the currently active world ID.

        Returns:
            World ID or None
        """
        if not os.path.exists(self.current_world_file):
            return None

        try:
            with open(self.current_world_file, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"❌ Error reading current world: {e}")
            return None

    def set_current_world(self, world_id: str) -> bool:
        """
        Set the currently active world.

        Args:
            world_id: World ID to set as current

        Returns:
            True if successful
        """
        # Verify world exists
        if not self.get_world_metadata(world_id):
            print(f"❌ World {world_id} not found")
            return False

        try:
            with open(self.current_world_file, 'w') as f:
                f.write(world_id)

            print(f"✅ Set current world to: {world_id}")
            return True

        except Exception as e:
            print(f"❌ Error setting current world: {e}")
            return False

    def clear_current_world(self):
        """Clear the current world setting."""
        if os.path.exists(self.current_world_file):
            os.remove(self.current_world_file)
            print("🔄 Cleared current world")

    def get_or_create_default_world(self) -> str:
        """
        Get current world or create a default one.

        Returns:
            World ID
        """
        # Check if there's a current world
        current_id = self.get_current_world_id()
        if current_id and self.get_world_metadata(current_id):
            return current_id

        # Check if any worlds exist
        worlds = self.list_worlds()
        if worlds:
            # Use the most recent world
            world_id = worlds[0]["world_id"]
            self.set_current_world(world_id)
            return world_id

        # Create a new default world
        metadata = self.create_world(name="Default World", description="Automatically created default world")
        world_id = metadata["world_id"]
        self.set_current_world(world_id)
        return world_id

    def get_world_paths(self, world_id: str) -> Dict[str, str]:
        """
        Get file paths for a world.

        Args:
            world_id: World ID

        Returns:
            Dict with paths to instance_owl, inferred_owl, graphical_state, metadata, rules
        """
        world_dir = self._get_world_dir(world_id)
        rules_dir = os.path.join(world_dir, "rules")

        return {
            "world_dir": world_dir,
            "instance_owl": os.path.join(world_dir, "AIAS-instance.owl"),
            "inferred_owl": os.path.join(world_dir, "AIAS-inferred.owl"),
            "graphical_state": os.path.join(world_dir, "graphical_state.json"),
            "metadata": os.path.join(world_dir, "metadata.json"),
            "rules_dir": rules_dir,
            "shacl_consistency": os.path.join(rules_dir, "shacl_rules_consistency.ttl"),
            "shacl_notes": os.path.join(rules_dir, "shacl_rules_notes.ttl"),
            "sparql_notes": os.path.join(rules_dir, "sparql_rules_notes.json"),
            "swrl_rules": os.path.join(rules_dir, "swrl_rules.txt")
        }

    def world_exists(self, world_id: str) -> bool:
        """Check if a world exists."""
        return os.path.exists(self._get_world_dir(world_id))

    def export_world(self, world_id: str, export_path: str) -> bool:
        """
        Export a world to a zip file.

        Args:
            world_id: World ID to export
            export_path: Path to save zip file

        Returns:
            True if successful
        """
        world_dir = self._get_world_dir(world_id)

        if not os.path.exists(world_dir):
            return False

        try:
            shutil.make_archive(
                export_path.replace('.zip', ''),
                'zip',
                world_dir
            )
            print(f"📦 Exported world {world_id} to {export_path}")
            return True

        except Exception as e:
            print(f"❌ Error exporting world: {e}")
            return False

    def import_world(self, zip_path: str, new_name: str = None) -> Optional[str]:
        """
        Import a world from a zip file.

        Args:
            zip_path: Path to zip file
            new_name: Optional new name for imported world

        Returns:
            New world ID or None if failed
        """
        try:
            # Create new world
            metadata = self.create_world(name=new_name or "Imported World")
            world_id = metadata["world_id"]
            world_dir = self._get_world_dir(world_id)

            # Extract zip
            shutil.unpack_archive(zip_path, world_dir, 'zip')

            print(f"📥 Imported world as {world_id}")
            return world_id

        except Exception as e:
            print(f"❌ Error importing world: {e}")
            return None

    def create_phase_world(self, parent_world_id: str, project_name: str,
                          custom_name: str = None) -> Dict:
        """
        Create a new phase model by copying from parent world.

        Workflow:
        1. Get parent metadata and determine next phase
        2. Validate phase transition
        3. Create new world with phase metadata
        4. Copy critical files (AIAS-instance.owl, graphical_state.json)
        5. Update parent's child_world_ids list

        Args:
            parent_world_id: Source world to copy from
            project_name: Project name for grouping
            custom_name: Optional custom name (default: "{project}_{phase_label}")

        Returns:
            New world metadata dict

        Raises:
            ValueError: If parent doesn't exist or invalid phase transition
        """
        # Get parent metadata
        parent_metadata = self.get_world_metadata(parent_world_id)
        if not parent_metadata:
            raise ValueError(f"Parent world {parent_world_id} not found")

        parent_dir = self._get_world_dir(parent_world_id)

        # Determine next phase
        parent_phase = parent_metadata.get("dmme_phase")
        if parent_phase is None:
            # Non-phase world can become Phase 2 (start of lineage)
            next_phase = 2
        else:
            # Get next phase from transitions
            next_phase = PHASE_TRANSITIONS.get(parent_phase)
            if next_phase is None:
                raise ValueError(f"No valid phase transition from Phase {parent_phase}")

        # Validate transition
        is_valid, error_msg = self.validate_phase_transition(parent_world_id, next_phase)
        if not is_valid:
            raise ValueError(error_msg)

        # Generate name
        phase_label = DMME_PHASES[next_phase]["label"]
        if custom_name:
            new_name = custom_name
        else:
            new_name = f"{project_name}_{phase_label}"

        # Create new world with phase metadata
        new_metadata = self.create_world(
            name=new_name,
            description=f"Phase {next_phase} model derived from {parent_metadata['name']}",
            project_name=project_name,
            dmme_phase=next_phase,
            parent_world_id=parent_world_id
        )

        new_world_id = new_metadata["world_id"]
        new_dir = self._get_world_dir(new_world_id)

        # Copy critical files from parent
        try:
            # Copy AIAS-instance.owl (the semantic model)
            parent_instance = os.path.join(parent_dir, "AIAS-instance.owl")
            new_instance = os.path.join(new_dir, "AIAS-instance.owl")
            if os.path.exists(parent_instance):
                shutil.copy2(parent_instance, new_instance)
                print(f"  ✓ Copied AIAS-instance.owl")

                # Update AISystem node name AND ID in the copied OWL file
                self._update_aisystem_name(new_instance, new_name, new_world_id)
                print(f"  ✓ Updated AISystem node name and ID")

            # Copy graphical_state.json (UI state)
            parent_graphical = os.path.join(parent_dir, "graphical_state.json")
            new_graphical = os.path.join(new_dir, "graphical_state.json")
            if os.path.exists(parent_graphical):
                shutil.copy2(parent_graphical, new_graphical)
                print(f"  ✓ Copied graphical_state.json")

            # Copy rules from parent world (maintaining parent's rule configuration)
            parent_rules_dir = os.path.join(parent_dir, "rules")
            new_rules_dir = os.path.join(new_dir, "rules")
            if os.path.exists(parent_rules_dir):
                # Copy entire rules directory from parent
                if os.path.exists(new_rules_dir):
                    shutil.rmtree(new_rules_dir)
                shutil.copytree(parent_rules_dir, new_rules_dir)
                print(f"  ✓ Copied rules from parent")

            # Update parent metadata: add to child_world_ids
            parent_children = parent_metadata.get("child_world_ids", [])
            if new_world_id not in parent_children:
                parent_children.append(new_world_id)
                self.update_world_metadata(parent_world_id, {
                    "child_world_ids": parent_children
                })

            print(f"🔗 Created Phase {next_phase} model from {parent_world_id}")
            print(f"   Parent: {parent_metadata['name']}")
            print(f"   Child:  {new_metadata['name']}")

            return new_metadata

        except Exception as e:
            # Clean up on error
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
            raise ValueError(f"Failed to copy phase world: {e}")

    def validate_phase_transition(self, parent_world_id: str,
                                  target_phase: int) -> Tuple[bool, str]:
        """
        Validate if phase transition is allowed.

        Args:
            parent_world_id: Parent world ID
            target_phase: Target phase number

        Returns:
            (is_valid, error_message)
        """
        # Check if target phase exists
        if target_phase not in DMME_PHASES:
            return False, f"Invalid phase number: {target_phase}"

        # Get parent metadata
        parent_metadata = self.get_world_metadata(parent_world_id)
        if not parent_metadata:
            return False, f"Parent world {parent_world_id} not found"

        parent_phase = parent_metadata.get("dmme_phase")

        # Non-phase world can start Phase 2
        if parent_phase is None and target_phase == 2:
            return True, ""

        # Check valid transition
        if parent_phase in PHASE_TRANSITIONS:
            expected_next = PHASE_TRANSITIONS[parent_phase]
            if target_phase == expected_next:
                return True, ""
            else:
                return False, f"Phase {target_phase} can only be created from Phase {expected_next - 1}, not Phase {parent_phase}"

        return False, f"No valid transition from Phase {parent_phase}"

    def get_project_worlds(self, project_name: str) -> List[Dict]:
        """
        Get all worlds belonging to a project, sorted by phase.

        Args:
            project_name: Project name

        Returns:
            List of world metadata dicts sorted by phase
        """
        all_worlds = self.list_worlds()
        project_worlds = [
            w for w in all_worlds
            if w.get("project_name") == project_name
        ]

        # Sort by phase (2 → 3 → 8 → 9 → non-phase)
        project_worlds.sort(key=lambda w: w.get("dmme_phase") or 999)

        return project_worlds

    def list_projects(self) -> List[Dict]:
        """
        Get list of all projects with summary info.

        Returns:
            List of project summaries
        """
        all_worlds = self.list_worlds()
        projects = {}

        for world in all_worlds:
            project_name = world.get("project_name")
            if project_name:
                if project_name not in projects:
                    projects[project_name] = {
                        "project_name": project_name,
                        "world_count": 0,
                        "phases": [],
                        "last_modified": world.get("last_modified")
                    }

                projects[project_name]["world_count"] += 1
                phase = world.get("dmme_phase")
                if phase and phase not in projects[project_name]["phases"]:
                    projects[project_name]["phases"].append(phase)

                # Update last_modified to most recent
                if world.get("last_modified") > projects[project_name]["last_modified"]:
                    projects[project_name]["last_modified"] = world.get("last_modified")

        # Sort phases within each project
        for project in projects.values():
            project["phases"].sort()

        # Return as list sorted by last_modified
        return sorted(projects.values(),
                     key=lambda p: p["last_modified"],
                     reverse=True)

    def _copy_rules_to_world(self, world_id: str) -> bool:
        """
        Copy rule files from global rule base to world-specific rules directory.

        Args:
            world_id: World ID

        Returns:
            True if successful
        """
        try:
            # Get global rule base directory
            from expert_system.rule_base import get_rule_base_path
            global_rule_dir = get_rule_base_path()

            # Get world-specific rules directory
            world_paths = self.get_world_paths(world_id)
            world_rule_dir = world_paths["rules_dir"]

            # Create rules directory in world folder
            os.makedirs(world_rule_dir, exist_ok=True)

            # List of rule files to copy
            rule_files = [
                "shacl_rules_consistency.ttl",
                "shacl_rules_notes.ttl",
                "sparql_rules_notes.json",
                "swrl_rules.txt"
            ]

            # Copy each rule file
            for rule_file in rule_files:
                src = os.path.join(global_rule_dir, rule_file)
                dst = os.path.join(world_rule_dir, rule_file)

                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    print(f"  ✓ Copied {rule_file}")
                else:
                    print(f"  ⚠️ Rule file not found: {rule_file}")

            print(f"📋 Copied rules to world {world_id}")
            return True

        except Exception as e:
            print(f"❌ Error copying rules to world {world_id}: {e}")
            return False
