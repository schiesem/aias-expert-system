import { useState, useEffect } from "react";
import { useStore } from "../../store";
import { Button } from "../ui";
import {
  listWorlds,
  createWorld,
  activateWorld,
  deleteWorld,
  getCurrentWorld,
  createPhaseWorld,
  groupWorldsByProject,
  getNextPhase,
  canCreateNextPhase,
  DMME_PHASES,
  DEFAULT_WORLD_ID
} from "../../utils/annotationUtils";
import "./StoragePanel.css";

const selector = (store) => ({
  nodes: store.nodes,
  edges: store.edges,
  initializeFromBackend: store.initializeFromBackend,
  setNodes: store.setNodes,
  setEdges: store.setEdges,
  openAnnotationWindow: store.openAnnotationWindow,
});

export default function StoragePanel({ isOpen, onOpenChange }) {
  const store = useStore(selector);
  const [worlds, setWorlds] = useState([]);
  const [currentWorldId, setCurrentWorldId] = useState(null);
  const [currentWorld, setCurrentWorld] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Create project dialog (always creates Phase 2)
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newWorldName, setNewWorldName] = useState("");

  // Create phase dialog
  const [showCreatePhaseDialog, setShowCreatePhaseDialog] = useState(false);
  const [selectedParentWorld, setSelectedParentWorld] = useState(null);
  const [phaseAutoSwitch, setPhaseAutoSwitch] = useState(true);

  // Project grouping
  const [projectGroups, setProjectGroups] = useState({ projects: {}, ungrouped: [] });
  const [expandedProjects, setExpandedProjects] = useState({});
  const [defaultWorld, setDefaultWorld] = useState(null);

  // Load worlds on mount and when drawer opens
  useEffect(() => {
    if (isOpen) {
      loadWorldsList();
      loadCurrentWorld();
    }
  }, [isOpen]);

  // Update project groups when worlds change
  useEffect(() => {
    // Separate default world from other worlds
    const defaultW = worlds.find(w => w.world_id === DEFAULT_WORLD_ID);
    const otherWorlds = worlds.filter(w => w.world_id !== DEFAULT_WORLD_ID);

    setDefaultWorld(defaultW);

    const grouped = groupWorldsByProject(otherWorlds);
    setProjectGroups(grouped);

    // Auto-expand all projects on first load
    const expanded = {};
    Object.keys(grouped.projects).forEach(projectName => {
      expanded[projectName] = true;
    });
    expanded['_ungrouped'] = true;
    setExpandedProjects(expanded);
  }, [worlds]);

  const loadWorldsList = async () => {
    try {
      const result = await listWorlds();
      setWorlds(result.worlds);
      setCurrentWorldId(result.currentWorldId);
    } catch (error) {
      console.error("Failed to load worlds list:", error);
    }
  };

  const loadCurrentWorld = async () => {
    try {
      const world = await getCurrentWorld();
      setCurrentWorld(world);
    } catch (error) {
      console.error("Failed to load current world:", error);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      alert("Please enter a project name");
      return;
    }

    setIsLoading(true);
    try {
      // Always create Phase 2 (Ist-Modell) as the starting phase
      const worldName = newWorldName.trim() || `${newProjectName}_Ist-Modell`;

      await createWorld(
        worldName,
        `Phase 2 model for ${newProjectName}`,
        newProjectName,  // project_name
        2,               // dmme_phase (always Phase 2)
        null             // parent_world_id
      );

      setNewProjectName("");
      setNewWorldName("");
      setShowCreateDialog(false);
      await loadWorldsList();
    } catch (error) {
      alert(`Failed to create project: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSwitchWorld = async (worldId) => {
    if (worldId === currentWorldId) {
      return;
    }

    const confirmSwitch = window.confirm(
      "Switching worlds will reload the model. Any unsaved changes will be synced first. Continue?"
    );

    if (!confirmSwitch) return;

    setIsLoading(true);
    try {
      await activateWorld(worldId);
      await store.initializeFromBackend();
      await loadWorldsList();
      await loadCurrentWorld();
      window.location.reload();
    } catch (error) {
      alert(`Failed to switch world: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteWorld = async (worldId) => {
    if (worldId === currentWorldId) {
      alert("Cannot delete the currently active world. Switch to another world first.");
      return;
    }

    const world = worlds.find(w => w.world_id === worldId);
    const confirmDelete = window.confirm(
      `Are you sure you want to delete "${world?.name}"? This cannot be undone!`
    );

    if (!confirmDelete) return;

    setIsLoading(true);
    try {
      await deleteWorld(worldId);
      await loadWorldsList();
    } catch (error) {
      alert(`Failed to delete world: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePhaseClick = (world) => {
    setSelectedParentWorld(world);
    setPhaseAutoSwitch(true);
    setShowCreatePhaseDialog(true);
  };

  const handleCreatePhaseConfirm = async () => {
    setIsLoading(true);
    try {
      // Project name is inherited from parent world
      const projectName = selectedParentWorld.project_name;
      const nextPhase = getNextPhase(selectedParentWorld);
      const phaseLabel = DMME_PHASES[nextPhase].label;

      // Auto-generate name based on project and phase
      const customName = `${projectName}_${phaseLabel}`;

      await createPhaseWorld(
        selectedParentWorld.world_id,
        projectName,  // Inherited project name
        phaseAutoSwitch,
        customName
      );

      setShowCreatePhaseDialog(false);
      setSelectedParentWorld(null);

      // Reload if not auto-switching
      if (!phaseAutoSwitch) {
        await loadWorldsList();
      } else {
        // Auto-switch will reload the page
        window.location.reload();
      }
    } catch (error) {
      alert(`Failed to create phase model: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleProject = (projectName) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectName]: !prev[projectName]
    }));
  };

  /**
   * Handle double-click on current world to open AISystem annotation window.
   */
  const handleCurrentWorldDoubleClick = () => {
    if (!currentWorld) {
      return;
    }

    // Create element data for the AISystem instance
    const aiSystemElement = {
      id: currentWorld.world_id,  // AISystem instance ID is the same as world_id
      class: "ISO22989.AISystem",  // Use 'class' instead of 'className' to match AnnotationWindow expectations
      label: currentWorld.name  // Human-readable name from metadata
    };

    console.log('🤖 Opening annotation window for AISystem:', aiSystemElement);
    store.openAnnotationWindow(aiSystemElement);
  };

  const renderWorldItem = (world) => {
    const nextPhase = getNextPhase(world);
    const canCreatePhase = canCreateNextPhase(world);
    const isDefaultWorld = world.world_id === DEFAULT_WORLD_ID;

    return (
      <div
        key={world.world_id}
        className={`world-item ${world.world_id === currentWorldId ? 'active' : ''}`}
      >
        {/* Phase Badge */}
        {world.is_phase_model && (
          <div className={`phase-badge phase-${world.dmme_phase}`}>
            Phase {world.dmme_phase}: {world.phase_label}
          </div>
        )}

        <div className="world-info">
          <div className="world-name">
            {world.name}
            {world.world_id === currentWorldId && (
              <span className="current-badge">ACTIVE</span>
            )}
          </div>
          <div className="world-meta">
            {world.node_count} nodes • {world.edge_count} edges
          </div>
        </div>

        <div className="world-actions-inline">
          {/* Create Next Phase Button - Not for default world */}
          {canCreatePhase && !isDefaultWorld && (
            <button
              onClick={() => handleCreatePhaseClick(world)}
              disabled={isLoading}
              className="world-action-btn create-phase"
              title={`Create Phase ${nextPhase} model`}
            >
              → P{nextPhase}
            </button>
          )}

          {/* Switch Button */}
          {world.world_id !== currentWorldId && (
            <button
              onClick={() => handleSwitchWorld(world.world_id)}
              disabled={isLoading}
              className="world-action-btn switch"
              title="Switch to this world"
            >
              ↻
            </button>
          )}

          {/* Delete Button */}
          {world.world_id !== currentWorldId && world.world_id !== DEFAULT_WORLD_ID && (
            <button
              onClick={() => handleDeleteWorld(world.world_id)}
              disabled={isLoading}
              className="world-action-btn delete"
              title="Delete world"
            >
              🗑
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="world-drawer-backdrop"
          onClick={() => onOpenChange(false)}
        />
      )}

      {/* Drawer */}
      <div className={`world-drawer ${isOpen ? 'world-drawer-open' : ''}`}>
        {/* Close Button - Only visible when open */}
        {isOpen && (
          <button
            onClick={() => onOpenChange(false)}
            className="world-drawer-close-button"
            title="Close"
          >
            ×
          </button>
        )}

        {/* Drawer Content */}
        <div className="world-drawer-content">
          <div className="world-drawer-header">
            <h2>World Selector</h2>
          </div>

          <div className="world-drawer-body">
            {/* Current World Info */}
            {currentWorld && (
              <div
                className="current-world-info"
                onDoubleClick={handleCurrentWorldDoubleClick}
                title="Double-click to annotate AISystem"
                style={{ cursor: 'pointer' }}
              >
                <div className="info-label">Current World</div>
                <div className="info-value">{currentWorld.name}</div>
                {currentWorld.is_phase_model && (
                  <div className={`info-phase phase-${currentWorld.dmme_phase}`}>
                    Phase {currentWorld.dmme_phase}: {currentWorld.phase_label}
                  </div>
                )}
                <div className="info-stats">
                  {store.nodes.length} nodes • {store.edges.length} edges
                </div>
                <div className="info-meta">
                  Last modified: {new Date(currentWorld.last_modified).toLocaleString()}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="world-actions">
              <Button
                variant="secondary"
                onClick={() => setShowCreateDialog(!showCreateDialog)}
                disabled={isLoading}
              >
                {showCreateDialog ? "Cancel" : "New Project"}
              </Button>
            </div>

            {/* Create Project Dialog */}
            {showCreateDialog && (
              <div className="create-world-dialog">
                <div className="dialog-header">
                  <strong>Create New Project (Phase 2)</strong>
                  <p className="dialog-subtitle">Start with Ist-Modell (Technical Understanding)</p>
                </div>
                <input
                  type="text"
                  placeholder="Project name (required, e.g., 'Smart Factory AI')..."
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="world-name-input"
                  disabled={isLoading}
                  required
                />
                <input
                  type="text"
                  placeholder={`Model name (optional, default: ${newProjectName ? newProjectName + '_Ist-Modell' : 'ProjectName_Ist-Modell'})...`}
                  value={newWorldName}
                  onChange={(e) => setNewWorldName(e.target.value)}
                  className="world-name-input"
                  disabled={isLoading}
                />
                <Button
                  variant="secondary"
                  onClick={handleCreateProject}
                  disabled={isLoading || !newProjectName.trim()}
                >
                  Create Project
                </Button>
              </div>
            )}

            {/* Create Phase Dialog */}
            {showCreatePhaseDialog && selectedParentWorld && (
              <div className="create-phase-dialog">
                <h3>Create Phase {getNextPhase(selectedParentWorld)} Model</h3>
                <p className="phase-dialog-info">
                  <strong>Project:</strong> {selectedParentWorld.project_name}
                  <br />
                  <strong>From:</strong> {selectedParentWorld.phase_label} ({selectedParentWorld.name})
                  <br />
                  <strong>Create:</strong> {DMME_PHASES[getNextPhase(selectedParentWorld)].label}
                  <br />
                  <strong>New model name:</strong> {selectedParentWorld.project_name}_{DMME_PHASES[getNextPhase(selectedParentWorld)].label}
                </p>

                <label className="phase-checkbox">
                  <input
                    type="checkbox"
                    checked={phaseAutoSwitch}
                    onChange={(e) => setPhaseAutoSwitch(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>Automatically switch to new phase model</span>
                </label>

                <div className="phase-dialog-actions">
                  <Button
                    variant="secondary"
                    onClick={handleCreatePhaseConfirm}
                    disabled={isLoading}
                  >
                    Create Phase {getNextPhase(selectedParentWorld)} Model
                  </Button>
                  <button
                    onClick={() => setShowCreatePhaseDialog(false)}
                    disabled={isLoading}
                    className="cancel-btn"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Default World - Always at top */}
            {defaultWorld && (
              <div className="default-world-section">
                <div className="default-world-label">Default World</div>
                <div className="default-world-container">
                  {renderWorldItem(defaultWorld)}
                </div>
              </div>
            )}

            {/* Worlds List - Hierarchical by Project */}
            <div className="worlds-list">
              <div className="worlds-list-header">Projects</div>

              {Object.keys(projectGroups.projects).length === 0 ? (
                <div className="no-worlds">
                  No projects yet. Click "New Project" to get started!
                </div>
              ) : (
                <>
                  {/* Project Folders */}
                  {Object.entries(projectGroups.projects).map(([projectName, project]) => (
                    <div key={projectName} className="project-folder">
                      <div
                        className="project-header"
                        onClick={() => toggleProject(projectName)}
                      >
                        <span className="expand-icon">
                          {expandedProjects[projectName] ? '▼' : '▶'}
                        </span>
                        <span className="project-name">{projectName}</span>
                        <span className="project-meta">
                          {project.worlds.length} model{project.worlds.length !== 1 ? 's' : ''}
                        </span>
                      </div>

                      {expandedProjects[projectName] && (
                        <div className="project-worlds">
                          {project.worlds.map(world => renderWorldItem(world))}
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}
            </div>

            {isLoading && (
              <div className="loading-overlay">
                <div className="loading-spinner">Loading...</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
