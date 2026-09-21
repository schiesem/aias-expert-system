/**
 * Floating Edge Utilities
 *
 * Calculates the optimal connection points between two nodes
 * for floating edges that automatically adjust based on node positions.
 *
 * Based on ReactFlow's floating edges example:
 * https://reactflow.dev/examples/edges/floating-edges
 */

/**
 * Get the position on the node border where the edge should connect
 * @param {number} x - intersection x coordinate
 * @param {number} y - intersection y coordinate
 * @param {object} node - the node object with position and dimensions
 * @returns {object} - { x, y } coordinates on the node border
 */
function getNodeIntersection(node, targetNode) {
  // Get center points of both nodes
  const nodeWidth = node.width ?? 144;  // Default width
  const nodeHeight = node.height ?? 112; // Default height

  const targetWidth = targetNode.width ?? 144;
  const targetHeight = targetNode.height ?? 112;

  const centerA = {
    x: node.position.x + nodeWidth / 2,
    y: node.position.y + nodeHeight / 2,
  };

  const centerB = {
    x: targetNode.position.x + targetWidth / 2,
    y: targetNode.position.y + targetHeight / 2,
  };

  // Calculate the angle between the two centers
  const dx = centerB.x - centerA.x;
  const dy = centerB.y - centerA.y;

  // Determine which side of the node to connect to based on angle
  const angle = Math.atan2(dy, dx);

  let x, y;

  // Determine connection point based on angle
  // Right side: -45° to 45°
  if (angle > -Math.PI / 4 && angle <= Math.PI / 4) {
    x = node.position.x + nodeWidth;
    y = node.position.y + nodeHeight / 2;
  }
  // Bottom side: 45° to 135°
  else if (angle > Math.PI / 4 && angle <= (3 * Math.PI) / 4) {
    x = node.position.x + nodeWidth / 2;
    y = node.position.y + nodeHeight;
  }
  // Left side: 135° to -135°
  else if (angle > (3 * Math.PI) / 4 || angle <= -(3 * Math.PI) / 4) {
    x = node.position.x;
    y = node.position.y + nodeHeight / 2;
  }
  // Top side: -135° to -45°
  else {
    x = node.position.x + nodeWidth / 2;
    y = node.position.y;
  }

  return { x, y };
}

/**
 * Get ReactFlow Position enum from coordinates
 * @param {object} node - the node
 * @param {object} intersection - { x, y } intersection point
 * @returns {string} - 'top', 'right', 'bottom', or 'left'
 */
function getPositionFromCoords(node, intersection) {
  const nodeWidth = node.width ?? 144;
  const nodeHeight = node.height ?? 112;

  const centerX = node.position.x + nodeWidth / 2;
  const centerY = node.position.y + nodeHeight / 2;

  const dx = intersection.x - centerX;
  const dy = intersection.y - centerY;

  const angle = Math.atan2(dy, dx);

  // Same logic as getNodeIntersection but returns position string
  if (angle > -Math.PI / 4 && angle <= Math.PI / 4) {
    return 'right';
  } else if (angle > Math.PI / 4 && angle <= (3 * Math.PI) / 4) {
    return 'bottom';
  } else if (angle > (3 * Math.PI) / 4 || angle <= -(3 * Math.PI) / 4) {
    return 'left';
  } else {
    return 'top';
  }
}

/**
 * Apply offset to coordinates based on edge direction
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @param {number} offset - Offset value
 * @param {string} position - Position ('top', 'bottom', 'left', 'right')
 * @returns {object} - { x, y } adjusted coordinates
 */
function applyOffsetToCoords(x, y, offset, position) {
  if (!offset || offset === 0) {
    return { x, y };
  }

  // Apply offset perpendicular to connection direction
  switch (position) {
    case 'top':
    case 'bottom':
      // For vertical connections, offset horizontally
      return { x: x + offset, y };

    case 'left':
    case 'right':
      // For horizontal connections, offset vertically
      return { x, y: y + offset };

    default:
      return { x, y };
  }
}

/**
 * Get edge parameters for a floating edge with optional offset support
 * @param {object} sourceNode - source node
 * @param {object} targetNode - target node
 * @param {number} offset - optional offset for parallel edges
 * @returns {object} - { sx, sy, tx, ty, sourcePos, targetPos } coordinates and positions
 */
export function getEdgeParams(sourceNode, targetNode, offset = 0) {
  const sourceIntersection = getNodeIntersection(sourceNode, targetNode);
  const targetIntersection = getNodeIntersection(targetNode, sourceNode);

  // Determine which side we're connecting from/to for CommunicationEdge arrows
  const sourcePos = getPositionFromCoords(sourceNode, sourceIntersection);
  const targetPos = getPositionFromCoords(targetNode, targetIntersection);

  // Apply offset if provided
  const adjustedSource = applyOffsetToCoords(
    sourceIntersection.x,
    sourceIntersection.y,
    offset,
    sourcePos
  );

  const adjustedTarget = applyOffsetToCoords(
    targetIntersection.x,
    targetIntersection.y,
    offset,
    targetPos
  );

  return {
    sx: adjustedSource.x,
    sy: adjustedSource.y,
    tx: adjustedTarget.x,
    ty: adjustedTarget.y,
    sourcePos,
    targetPos,
  };
}
