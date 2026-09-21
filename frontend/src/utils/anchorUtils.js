/**
 * Utility functions for calculating anchor points on nodes
 * Anchor points are connection points on the node border where edges can attach
 */

/**
 * Calculate anchor points for a rectangular node (FunctionNode)
 * 5 points per side = 20 total points
 * @param {number} width - Node width
 * @param {number} height - Node height
 * @returns {Array} Array of {x, y, index} anchor points (relative to node center)
 */
export function getRectangleAnchorPoints(width, height) {
  const anchors = [];
  const halfW = width / 2;
  const halfH = height / 2;

  // Top side (5 points): index 0-4
  for (let i = 0; i < 5; i++) {
    const x = -halfW + (i + 1) * (width / 6); // Distribute evenly
    anchors.push({ x, y: -halfH, index: i });
  }

  // Right side (5 points): index 5-9
  for (let i = 0; i < 5; i++) {
    const y = -halfH + (i + 1) * (height / 6);
    anchors.push({ x: halfW, y, index: 5 + i });
  }

  // Bottom side (5 points): index 10-14
  for (let i = 0; i < 5; i++) {
    const x = halfW - (i + 1) * (width / 6);
    anchors.push({ x, y: halfH, index: 10 + i });
  }

  // Left side (5 points): index 15-19
  for (let i = 0; i < 5; i++) {
    const y = halfH - (i + 1) * (height / 6);
    anchors.push({ x: -halfW, y, index: 15 + i });
  }

  return anchors;
}

/**
 * Calculate anchor points for an elliptical node (ResourceNode)
 * 5 points per side = 20 total points
 * @param {number} width - Node width
 * @param {number} height - Node height
 * @returns {Array} Array of {x, y, index} anchor points (relative to node center)
 */
export function getEllipseAnchorPoints(width, height) {
  const anchors = [];
  const halfW = width / 2;
  const halfH = height / 2;

  // Distribute 20 points around the ellipse
  for (let i = 0; i < 20; i++) {
    const angle = (i * 18) * (Math.PI / 180); // 18° increments
    const x = halfW * Math.cos(angle);
    const y = halfH * Math.sin(angle);
    anchors.push({ x, y, index: i });
  }

  return anchors;
}

/**
 * Calculate anchor points for a circular node (ProductNode)
 * 10 points every 36° = 10 total points
 * @param {number} radius - Circle radius
 * @returns {Array} Array of {x, y, index} anchor points (relative to node center)
 */
export function getCircleAnchorPoints(radius) {
  const anchors = [];

  // Distribute 10 points around the circle
  for (let i = 0; i < 10; i++) {
    const angle = (i * 36) * (Math.PI / 180); // 36° increments
    const x = radius * Math.cos(angle);
    const y = radius * Math.sin(angle);
    anchors.push({ x, y, index: i });
  }

  return anchors;
}

/**
 * Find the closest anchor point to a given position
 * @param {Array} anchors - Array of anchor points
 * @param {Object} position - {x, y} position to check
 * @param {Object} nodePosition - {x, y} absolute position of the node
 * @returns {number} Index of the closest anchor point
 */
export function findClosestAnchor(anchors, position, nodePosition) {
  let minDist = Infinity;
  let closestIndex = 0;

  for (const anchor of anchors) {
    const anchorX = nodePosition.x + anchor.x;
    const anchorY = nodePosition.y + anchor.y;
    const dist = Math.sqrt(
      Math.pow(position.x - anchorX, 2) +
      Math.pow(position.y - anchorY, 2)
    );

    if (dist < minDist) {
      minDist = dist;
      closestIndex = anchor.index;
    }
  }

  return closestIndex;
}

/**
 * Get anchor point position by index for a node type
 * @param {string} nodeType - Type of node (FunctionNode, ResourceNode, ProductNode)
 * @param {number} index - Anchor point index
 * @param {Object} nodeDimensions - {width, height} or {radius}
 * @returns {Object} {x, y} relative position of anchor point
 */
export function getAnchorByIndex(nodeType, index, nodeDimensions) {
  let anchors;

  if (nodeType === 'FunctionNode') {
    anchors = getRectangleAnchorPoints(nodeDimensions.width, nodeDimensions.height);
  } else if (nodeType === 'ResourceNode') {
    anchors = getEllipseAnchorPoints(nodeDimensions.width, nodeDimensions.height);
  } else if (nodeType === 'ProductNode') {
    anchors = getCircleAnchorPoints(nodeDimensions.radius);
  }

  const anchor = anchors.find(a => a.index === index);
  return anchor ? { x: anchor.x, y: anchor.y } : { x: 0, y: 0 };
}
