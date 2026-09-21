/**
 * Edge Offset Utilities
 *
 * Calculates offsets for parallel edges to prevent visual overlap.
 * This is purely for visualization - the backend receives clean edge data without offsets.
 */

const EDGE_SPACING = 20; // Pixel spacing between parallel edges

/**
 * Group edges by node pairs (source-target combination)
 * @param {Array} edges - Array of edge objects
 * @returns {Object} - Grouped edges by node pair key
 */
function groupParallelEdges(edges) {
  const groups = {};

  edges.forEach(edge => {
    // Create a unique key for this node pair
    // We DON'T sort here because edges are directional
    // A->B should be grouped separately from B->A
    const key = `${edge.source}-${edge.target}`;

    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(edge);
  });

  console.log('[edgeOffsetUtils] Grouped edges:', groups);
  return groups;
}

/**
 * Calculate offset for each edge in a group
 * @param {Array} edgeGroup - Array of parallel edges
 * @returns {Array} - Edges with offset data added
 */
function calculateOffsetsForGroup(edgeGroup) {
  const count = edgeGroup.length;

  // If only one edge, no offset needed
  if (count === 1) {
    return edgeGroup.map(edge => ({
      ...edge,
      data: {
        ...edge.data,
        offset: 0,
        totalParallel: 1,
      }
    }));
  }

  // Calculate symmetric offsets around center
  // For 3 edges: [-1, 0, 1] * EDGE_SPACING = [-20, 0, 20]
  // For 2 edges: [-0.5, 0.5] * EDGE_SPACING = [-10, 10]
  return edgeGroup.map((edge, index) => {
    const offset = (index - (count - 1) / 2) * EDGE_SPACING;

    return {
      ...edge,
      data: {
        ...edge.data,
        offset: offset,
        totalParallel: count,
        edgeIndex: index,
      }
    };
  });
}

/**
 * Add visual offsets to all edges
 * This is called before rendering edges in ReactFlow
 * @param {Array} edges - Array of edge objects from store
 * @returns {Array} - Edges with offset data for visualization
 */
export function addVisualOffsets(edges) {
  if (!edges || edges.length === 0) {
    return edges;
  }

  // Group edges by node pairs
  const groups = groupParallelEdges(edges);

  // Calculate offsets for each group
  const edgesWithOffsets = [];
  Object.values(groups).forEach(group => {
    const processedGroup = calculateOffsetsForGroup(group);
    edgesWithOffsets.push(...processedGroup);
  });

  return edgesWithOffsets;
}

/**
 * Remove visual data from edges before sending to backend
 * This ensures the backend only receives semantic data
 * @param {Array} edges - Array of edge objects with visual data
 * @returns {Array} - Clean edges without visual metadata
 */
export function removeVisualData(edges) {
  return edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: edge.type,
    data: {
      // Keep only semantic data, remove offset, totalParallel, edgeIndex
      name: edge.data?.name,
      edgeType: edge.data?.edgeType,
      classField: edge.data?.classField,
      // Explicitly exclude: offset, totalParallel, edgeIndex
    }
  }));
}

/**
 * Get offset-adjusted coordinates for edge connection point
 * @param {number} baseX - Base X coordinate
 * @param {number} baseY - Base Y coordinate
 * @param {number} offset - Offset value (positive or negative)
 * @param {string} direction - Connection direction ('top', 'bottom', 'left', 'right')
 * @returns {Object} - { x, y } adjusted coordinates
 */
export function applyOffset(baseX, baseY, offset, direction) {
  if (!offset || offset === 0) {
    return { x: baseX, y: baseY };
  }

  // Apply offset perpendicular to edge direction
  switch (direction) {
    case 'top':
    case 'bottom':
      // For vertical edges, offset horizontally
      return { x: baseX + offset, y: baseY };

    case 'left':
    case 'right':
      // For horizontal edges, offset vertically
      return { x: baseX, y: baseY + offset };

    default:
      return { x: baseX, y: baseY };
  }
}
