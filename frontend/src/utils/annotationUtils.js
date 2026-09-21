/**
 * annotationUtils.js
 *
 * Utility functions for annotation operations.
 * Provides API calls to backend annotation endpoints.
 */

import { httpGet, httpPost, httpDelete } from './httpUtils';

// Backend API base URL - change this if your backend runs on a different host/port
const BACKEND_URL = 'http://localhost:5000';
const ANNOTATION_API_BASE = `${BACKEND_URL}/api/annotations`;

/**
 * Fetch available relations for a class.
 *
 * @param {string} className - Fully qualified class name (e.g., "ISO22989.Training" or "Training")
 * @param {number} maxLevel - Maximum relation depth (default 1)
 * @param {number} specificLevel - Get specific level only (optional)
 * @returns {Promise<Array>} Array of relation objects
 */
export async function fetchRelations(className, maxLevel = 1, specificLevel = null) {
  try {
    let url = `${ANNOTATION_API_BASE}/relations/${encodeURIComponent(className)}?max_level=${maxLevel}`;
    if (specificLevel !== null) {
      url += `&level=${specificLevel}`;
    }

    const response = await httpGet(url);

    if (response && response.success) {
      return response.relations || [];
    } else {
      console.error('fetchRelations failed:', response);
      throw new Error(response?.error || 'Failed to fetch relations');
    }
  } catch (error) {
    console.error('Error fetching relations:', error);
    throw error;
  }
}

/**
 * Fetch annotations for an element.
 *
 * @param {string} elementId - Element ID
 * @param {number} maxDepth - Maximum annotation graph depth (default 3)
 * @returns {Promise<Object>} Annotation object with nested structure
 */
export async function fetchAnnotations(elementId, maxDepth = 3) {
  try {
    const url = `${ANNOTATION_API_BASE}/${encodeURIComponent(elementId)}?max_depth=${maxDepth}`;
    const response = await httpGet(url);

    if (response && response.success) {
      return response.annotations || {};
    } else {
      console.error('fetchAnnotations failed:', response);
      throw new Error(response?.error || 'Failed to fetch annotations');
    }
  } catch (error) {
    console.error('Error fetching annotations:', error);
    throw error;
  }
}

/**
 * Create an annotation for an element.
 *
 * @param {string} elementId - Element ID
 * @param {string} elementClass - OWL class of the element (e.g., "Training")
 * @param {string} relationProperty - Property name (e.g., "isExecutedBy")
 * @param {string} targetClass - Target class name (e.g., "Model" or "ISO22989.Model")
 * @param {Object} instanceData - Instance data with 'name' and optional 'properties'
 * @param {string|null} parentInstanceName - Parent instance name for nested annotations (Level 2+)
 * @param {string} direction - "outgoing" (element --> new) or "incoming" (new --> element)
 * @returns {Promise<Object>} Created annotation object
 */
export async function createAnnotation(elementId, elementClass, relationProperty, targetClass, instanceData, parentInstanceName = null, direction = 'outgoing') {
  try {
    const url = `${ANNOTATION_API_BASE}/${encodeURIComponent(elementId)}`;

    const payload = {
      element_class: elementClass,
      relation_property: relationProperty,
      target_class: targetClass,
      instance_data: instanceData,
      parent_instance: parentInstanceName,  // Added: for nested annotations
      direction: direction  // Added: for incoming vs outgoing relations
    };

    const response = await httpPost(url, payload);

    if (response && response.success) {
      return response.annotation || {};
    } else {
      console.error('createAnnotation failed:', response);
      throw new Error(response?.error || 'Failed to create annotation');
    }
  } catch (error) {
    console.error('Error creating annotation:', error);
    throw error;
  }
}

/**
 * Delete an annotation from an element.
 *
 * @param {string} elementId - Element ID
 * @param {string} relationProperty - Property name
 * @param {string} annotationId - Random ID of the annotation to delete
 * @param {string} direction - "outgoing" (default) or "incoming"
 * @returns {Promise<boolean>} Success status
 */
export async function deleteAnnotation(elementId, relationProperty, annotationId, direction = 'outgoing') {
  try {
    let url = `${ANNOTATION_API_BASE}/${encodeURIComponent(elementId)}/${encodeURIComponent(relationProperty)}/${encodeURIComponent(annotationId)}`;

    // Add direction query param for incoming annotations
    if (direction === 'incoming') {
      url += '?direction=incoming';
    }

    const response = await httpDelete(url);

    if (response && response.success) {
      return true;
    } else {
      console.error('deleteAnnotation failed:', response);
      throw new Error(response?.error || 'Failed to delete annotation');
    }
  } catch (error) {
    console.error('Error deleting annotation:', error);
    throw error;
  }
}

/**
 * Fetch annotation count for an element.
 *
 * @param {string} elementId - Element ID
 * @returns {Promise<number>} Annotation count
 */
export async function fetchAnnotationCount(elementId) {
  try {
    const url = `${ANNOTATION_API_BASE}/${encodeURIComponent(elementId)}/count`;
    const response = await httpGet(url);

    if (response && response.success) {
      return response.count || 0;
    } else {
      console.error('fetchAnnotationCount failed:', response);
      return 0;
    }
  } catch (error) {
    console.error('Error fetching annotation count:', error);
    return 0;
  }
}

/**
 * Check if annotation service is healthy.
 *
 * @returns {Promise<boolean>} Health status
 */
export async function checkAnnotationHealth() {
  try {
    const url = `${ANNOTATION_API_BASE}/health`;
    const response = await httpGet(url);

    if (response && response.success) {
      return true;
    }
    return false;
  } catch (error) {
    console.error('Error checking annotation health:', error);
    return false;
  }
}

/**
 * Group relations by level.
 * Separates outgoing and incoming relations within each level.
 *
 * @param {Array} relations - Array of relation objects
 * @returns {Object} Relations grouped by level (level as key)
 */
export function groupRelationsByLevel(relations) {
  if (!relations || !Array.isArray(relations)) {
    return {};
  }

  return relations.reduce((acc, relation) => {
    const level = relation.level || 1;
    if (!acc[level]) {
      acc[level] = [];
    }
    // Ensure direction is set (default to outgoing for backwards compatibility)
    const relationWithDirection = {
      ...relation,
      direction: relation.direction || 'outgoing'
    };
    acc[level].push(relationWithDirection);
    return acc;
  }, {});
}

/**
 * Format cardinality for display.
 *
 * @param {string} cardinality - Cardinality string (e.g., "1..1", "0..*")
 * @returns {string} Human-readable cardinality
 */
export function formatCardinality(cardinality) {
  if (!cardinality) return 'Unknown';

  const cardMap = {
    '0..1': 'Optional (0 or 1)',
    '1..1': 'Required (exactly 1)',
    '0..*': 'Optional (any number)',
    '1..*': 'Required (at least 1)',
    '0..0': 'None'
  };

  return cardMap[cardinality] || cardinality;
}

/**
 * Extract short class name from fully qualified name.
 *
 * @param {string} fullClassName - Full class name (e.g., "ISO22989.Model")
 * @returns {string} Short class name (e.g., "Model")
 */
export function getShortClassName(fullClassName) {
  if (!fullClassName) return '';

  const parts = fullClassName.split('.');
  return parts[parts.length - 1];
}

/**
 * Validate instance data before creating annotation.
 *
 * @param {Object} instanceData - Instance data to validate
 * @returns {Object} Validation result {valid: boolean, error: string}
 */
export function validateInstanceData(instanceData) {
  if (!instanceData) {
    return { valid: false, error: 'Instance data is required' };
  }

  if (!instanceData.name || instanceData.name.trim() === '') {
    return { valid: false, error: 'Instance name is required' };
  }

  // Check for valid name (alphanumeric, underscore, hyphen)
  const namePattern = /^[a-zA-Z0-9_-]+$/;
  if (!namePattern.test(instanceData.name)) {
    return {
      valid: false,
      error: 'Instance name must contain only letters, numbers, underscore, or hyphen'
    };
  }

  return { valid: true, error: null };
}

/**
 * Format annotation data for display.
 * Flattens nested annotations (Level 1, Level 2, etc.) into a single array.
 * Handles both outgoing and incoming annotations.
 *
 * @param {Object} annotations - Annotations object from API
 * @returns {Array} Formatted array of annotations for display
 */
export function formatAnnotationsForDisplay(annotations) {
  if (!annotations || !annotations.annotations) {
    return [];
  }

  const result = [];

  // Recursive helper to process annotations at any level
  const processAnnotationLevel = (annotationData, parentInstanceName = null) => {
    for (const [propertyKey, values] of Object.entries(annotationData)) {
      if (Array.isArray(values)) {
        // Check if this is an incoming annotation (property key ends with __incoming)
        const isIncoming = propertyKey.endsWith('__incoming');
        const property = isIncoming ? propertyKey.replace('__incoming', '') : propertyKey;
        const direction = isIncoming ? 'incoming' : 'outgoing';

        values.forEach(value => {
          // Extract ID (OWL individual name) and displayName (hasName property)
          const id = value.name;  // This is now the random ID
          const displayName = value.properties?.hasName?.[0] || value.name;  // Use hasName if available, fallback to ID

          // Check if the value itself has a direction flag (from backend)
          const valueDirection = value.direction || direction;

          result.push({
            property,
            id,  // Random ID for deletion and identification
            displayName,  // User-friendly name for display
            name: displayName,  // Backward compatibility
            class: value.class,
            shortClass: getShortClassName(value.class),
            properties: value.properties || {},
            hasSubAnnotations: value.sub_annotations && Object.keys(value.sub_annotations).length > 0,
            parentInstance: parentInstanceName,  // Track which parent this belongs to
            direction: valueDirection  // Track if this is outgoing or incoming
          });

          // Recursively process sub-annotations (Level 2+)
          if (value.sub_annotations && Object.keys(value.sub_annotations).length > 0) {
            processAnnotationLevel(value.sub_annotations, value.name);
          }
        });
      }
    }
  };

  processAnnotationLevel(annotations.annotations);

  return result;
}

/**
 * Count total annotations recursively (including sub-annotations).
 *
 * @param {Object} annotations - Annotations object
 * @returns {number} Total count
 */
export function countAnnotationsRecursive(annotations) {
  if (!annotations || !annotations.annotations) {
    return 0;
  }

  let count = 0;
  const annotationData = annotations.annotations;

  for (const values of Object.values(annotationData)) {
    if (Array.isArray(values)) {
      count += values.length;

      // Count sub-annotations recursively
      values.forEach(value => {
        if (value.sub_annotations) {
          count += countAnnotationsRecursive({ annotations: value.sub_annotations });
        }
      });
    }
  }

  return count;
}

/**
 * Extract property description or create a default one.
 *
 * @param {Object} relation - Relation object
 * @returns {string} Description text
 */
export function getRelationDescription(relation) {
  if (relation.description && relation.description.trim() !== '') {
    return relation.description;
  }

  // Generate default description
  const shortTarget = getShortClassName(relation.target_class);
  return `Links to ${shortTarget} instance via ${relation.property}`;
}

/**
 * Check if a relation is required based on cardinality.
 *
 * @param {Object} relation - Relation object
 * @returns {boolean} True if required
 */
export function isRelationRequired(relation) {
  if (relation.is_required !== undefined) {
    return relation.is_required;
  }

  // Check cardinality
  if (relation.cardinality) {
    const parts = relation.cardinality.split('..');
    if (parts.length === 2) {
      const min = parseInt(parts[0]);
      return min > 0;
    }
  }

  return false;
}

/**
 * Sort relations by priority (required first, then alphabetically).
 *
 * @param {Array} relations - Array of relations
 * @returns {Array} Sorted relations
 */
export function sortRelations(relations) {
  if (!relations || !Array.isArray(relations)) {
    return [];
  }

  return [...relations].sort((a, b) => {
    // Required relations first
    const aRequired = isRelationRequired(a);
    const bRequired = isRelationRequired(b);

    if (aRequired && !bRequired) return -1;
    if (!aRequired && bRequired) return 1;

    // Then alphabetically by property name
    return a.property.localeCompare(b.property);
  });
}

/**
 * Synchronize the graphical model (nodes and edges) to the backend ontology.
 * This should be called automatically whenever the model changes.
 *
 * Uses the new unified /api/model/sync endpoint.
 *
 * @param {Array} nodes - ReactFlow nodes
 * @param {Array} edges - ReactFlow edges
 * @param {Object} viewport - Viewport state with x, y, zoom (optional)
 * @returns {Promise<Object>} Sync result with stats
 */
export async function syncModelToOntology(nodes, edges, viewport = null) {
  try {
    const MODEL_API_BASE = `${BACKEND_URL}/api/model`;

    // Build payload with viewport if provided
    const payload = {
      nodes,
      edges,
      viewport: viewport || { x: 0, y: 0, zoom: 1.0 }
    };

    const response = await httpPost(`${MODEL_API_BASE}/sync`, payload);

    if (!response.success) {
      throw new Error(response.error || 'Failed to sync model');
    }

    if (response.warnings && response.warnings.length > 0) {
      console.warn(
        `⚠️ ${response.warnings.length} Element(e) nicht in die Ontologie übernommen:`,
        response.warnings
      );
    }

    console.log('✅ Model synced to backend:', response.stats);
    return response;
  } catch (error) {
    console.error('❌ Error syncing model to backend:', error);
    throw error;
  }
}

/**
 * Load complete model state from backend (for initialization/refresh).
 *
 * @returns {Promise<Object>} Model object with nodes, edges, viewport, metadata
 */
export async function loadModelFromBackend() {
  try {
    const MODEL_API_BASE = `${BACKEND_URL}/api/model`;
    const response = await httpGet(`${MODEL_API_BASE}/load`);

    if (!response.success) {
      throw new Error(response.error || 'Failed to load model');
    }

    console.log('✅ Model loaded from backend:', {
      nodes: response.model.nodes.length,
      edges: response.model.edges.length,
      viewport: response.model.viewport
    });

    return response.model;
  } catch (error) {
    console.error('❌ Error loading model from backend:', error);
    throw error;
  }
}

// ============================================================================
// WORLD MANAGEMENT
// ============================================================================

const WORLD_API_BASE = `${BACKEND_URL}/api/worlds`;

/**
 * List all available worlds.
 *
 * @returns {Promise<Object>} Object with worlds array and current_world_id
 */
export async function listWorlds() {
  try {
    const response = await httpGet(WORLD_API_BASE);

    if (!response.success) {
      throw new Error(response.error || 'Failed to list worlds');
    }

    return {
      worlds: response.worlds || [],
      currentWorldId: response.current_world_id
    };
  } catch (error) {
    console.error('❌ Error listing worlds:', error);
    throw error;
  }
}

/**
 * Create a new world.
 *
 * @param {string} name - World name (optional)
 * @param {string} description - World description (optional)
 * @returns {Promise<Object>} Created world metadata
 */
export async function createWorld(name = null, description = null, projectName = null, dmmePhase = null, parentWorldId = null) {
  try {
    const payload = {};
    if (name) payload.name = name;
    if (description) payload.description = description;
    if (projectName) payload.project_name = projectName;
    if (dmmePhase) payload.dmme_phase = dmmePhase;
    if (parentWorldId) payload.parent_world_id = parentWorldId;

    const response = await httpPost(WORLD_API_BASE, payload);

    if (!response.success) {
      throw new Error(response.error || 'Failed to create world');
    }

    console.log('✅ World created:', response.world);
    return response.world;
  } catch (error) {
    console.error('❌ Error creating world:', error);
    throw error;
  }
}

/**
 * Get current world metadata.
 *
 * @returns {Promise<Object>} Current world metadata
 */
export async function getCurrentWorld() {
  try {
    const response = await httpGet(`${WORLD_API_BASE}/current`);

    if (!response.success) {
      throw new Error(response.error || 'Failed to get current world');
    }

    return response.world;
  } catch (error) {
    console.error('❌ Error getting current world:', error);
    throw error;
  }
}

/**
 * Switch to a different world.
 *
 * @param {string} worldId - World ID to activate
 * @returns {Promise<boolean>} Success status
 */
export async function activateWorld(worldId) {
  try {
    const response = await httpPost(`${WORLD_API_BASE}/${worldId}/activate`, {});

    if (!response.success) {
      throw new Error(response.error || 'Failed to activate world');
    }

    console.log('✅ World activated:', worldId);
    return true;
  } catch (error) {
    console.error('❌ Error activating world:', error);
    throw error;
  }
}

/**
 * Update world metadata.
 *
 * @param {string} worldId - World ID
 * @param {Object} updates - Fields to update (name, description)
 * @returns {Promise<Object>} Updated world metadata
 */
export async function updateWorld(worldId, updates) {
  try {
    const response = await httpPost(`${WORLD_API_BASE}/${worldId}`, updates);

    if (!response.success) {
      throw new Error(response.error || 'Failed to update world');
    }

    console.log('✅ World updated:', response.world);
    return response.world;
  } catch (error) {
    console.error('❌ Error updating world:', error);
    throw error;
  }
}

/**
 * Delete a world.
 *
 * WARNING: This cannot be undone!
 *
 * @param {string} worldId - World ID to delete
 * @returns {Promise<boolean>} Success status
 */
export async function deleteWorld(worldId) {
  try {
    const response = await httpDelete(`${WORLD_API_BASE}/${worldId}`);

    if (!response.success) {
      throw new Error(response.error || 'Failed to delete world');
    }

    console.log('✅ World deleted:', worldId);
    return true;
  } catch (error) {
    console.error('❌ Error deleting world:', error);
    throw error;
  }
}

// ==================== DMME Phase Versioning ====================

/**
 * DMME Phase constants
 */
export const DMME_PHASES = {
  2: { label: "Ist-Modell", name: "Technical Understanding" },
  3: { label: "Konzept-Modell", name: "Technical Realization" },
  8: { label: "Implementation-Modell", name: "Technical Implementation" },
  9: { label: "Deployment-Modell", name: "Deployment" }
};

export const PHASE_TRANSITIONS = {
  2: 3,
  3: 8,
  8: 9
};

// Default world constant (matches backend)
export const DEFAULT_WORLD_ID = "000000000000";

/**
 * Create next phase model from parent world.
 *
 * @param {string} parentWorldId - Parent world ID to copy from
 * @param {string} projectName - Project name for grouping
 * @param {boolean} autoSwitch - Auto-switch to new phase (default: true)
 * @param {string|null} customName - Optional custom name
 * @returns {Promise<Object>} New world metadata
 */
export async function createPhaseWorld(parentWorldId, projectName, autoSwitch = true, customName = null) {
  try {
    const response = await httpPost(
      `${WORLD_API_BASE}/${parentWorldId}/create-phase`,
      {
        project_name: projectName,
        phase_name: customName,
        auto_switch: autoSwitch
      }
    );

    if (!response.success) {
      throw new Error(response.error || 'Failed to create phase model');
    }

    console.log('✅ Phase world created:', response.world);
    return response.world;
  } catch (error) {
    console.error('❌ Error creating phase world:', error);
    throw error;
  }
}

/**
 * Get next phase number for a world.
 *
 * @param {Object} world - World metadata object
 * @returns {number|null} Next phase number or null if no transition exists
 */
export function getNextPhase(world) {
  if (!world.is_phase_model) return 2; // Start with Phase 2
  return PHASE_TRANSITIONS[world.dmme_phase] || null;
}

/**
 * Check if world can create next phase.
 *
 * @param {Object} world - World metadata object
 * @returns {boolean} True if next phase can be created
 */
export function canCreateNextPhase(world) {
  return getNextPhase(world) !== null;
}

/**
 * Group worlds by project.
 *
 * @param {Array} worlds - Array of world metadata objects
 * @returns {Object} {projects: {projectName: {projectName, worlds, lastModified}}, ungrouped: [worlds]}
 */
export function groupWorldsByProject(worlds) {
  const projects = {};
  const ungrouped = [];

  worlds.forEach(world => {
    if (world.project_name) {
      if (!projects[world.project_name]) {
        projects[world.project_name] = {
          projectName: world.project_name,
          worlds: [],
          lastModified: world.last_modified
        };
      }
      projects[world.project_name].worlds.push(world);

      // Update last_modified to most recent
      if (world.last_modified > projects[world.project_name].lastModified) {
        projects[world.project_name].lastModified = world.last_modified;
      }
    } else {
      ungrouped.push(world);
    }
  });

  // Sort worlds within each project by phase
  Object.values(projects).forEach(project => {
    project.worlds.sort((a, b) => (a.dmme_phase || 999) - (b.dmme_phase || 999));
  });

  return { projects, ungrouped };
}

/**
 * List all projects with summary info.
 *
 * @returns {Promise<Array>} Array of project summaries
 */
export async function listProjects() {
  try {
    const response = await httpGet(`${WORLD_API_BASE}/projects`);

    if (!response.success) {
      throw new Error(response.error || 'Failed to list projects');
    }

    return response.projects || [];
  } catch (error) {
    console.error('❌ Error listing projects:', error);
    throw error;
  }
}

/**
 * Get all worlds for a specific project.
 *
 * @param {string} projectName - Project name
 * @returns {Promise<Array>} Array of world metadata for the project
 */
export async function getProjectWorlds(projectName) {
  try {
    const response = await httpGet(`${WORLD_API_BASE}/project/${encodeURIComponent(projectName)}`);

    if (!response.success) {
      throw new Error(response.error || 'Failed to get project worlds');
    }

    return response.worlds || [];
  } catch (error) {
    console.error('❌ Error getting project worlds:', error);
    throw error;
  }
}

// ================================================================

/**
 * Get all existing instances of a specific ontology class.
 * Used for "Use Existing" dropdown in annotation UI.
 *
 * @param {string} className - Fully qualified class name (e.g., "ISO22989.Task")
 * @returns {Promise<Array>} Array of instance objects with id, display_name, class, properties
 */
export async function fetchInstancesByClass(className) {
  try {
    const url = `${ANNOTATION_API_BASE}/instances/${encodeURIComponent(className)}`;
    console.log(`📋 Fetching instances of class: ${className}`);

    const response = await httpGet(url);

    if (response && response.success) {
      console.log(`✅ Found ${response.instances.length} instances of ${className}`);
      return response.instances || [];
    } else {
      console.error('fetchInstancesByClass failed:', response);
      return [];
    }
  } catch (error) {
    console.error('Error fetching instances by class:', error);
    throw error;
  }
}

/**
 * Link an existing annotation instance to an element or parent annotation.
 * Used for "Use Existing" functionality in annotation UI.
 *
 * @param {string} elementId - Element ID or parent instance ID
 * @param {string} relationProperty - Property name (e.g., "fulfills")
 * @param {string} instanceId - Existing instance ID to link
 * @param {string|null} parentInstance - Parent instance ID (for Level 2+), null for Level 1
 * @param {string} direction - "outgoing" (element --> instance) or "incoming" (instance --> element)
 * @returns {Promise<boolean>} Success status
 */
export async function linkExistingAnnotation(
  elementId,
  relationProperty,
  instanceId,
  parentInstance = null,
  direction = 'outgoing'
) {
  try {
    const url = `${ANNOTATION_API_BASE}/${encodeURIComponent(elementId)}/link`;
    const payload = {
      relation_property: relationProperty,
      instance_id: instanceId,
      parent_instance: parentInstance,
      direction: direction
    };

    const linkDescription = direction === 'incoming'
      ? `${instanceId} --${relationProperty}--> ${elementId}`
      : `${elementId} --${relationProperty}--> ${instanceId}`;
    console.log(`🔗 Linking instance (${direction}): ${linkDescription}`);

    const response = await httpPost(url, payload);

    if (response && response.success) {
      console.log(`✅ Successfully linked instance: ${response.message}`);
      return true;
    } else {
      console.error('linkExistingAnnotation failed:', response);
      throw new Error(response?.error || 'Failed to link instance');
    }
  } catch (error) {
    console.error('Error linking annotation:', error);
    throw error;
  }
}
