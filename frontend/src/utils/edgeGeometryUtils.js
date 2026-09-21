/**
 * Edge Geometry Utilities
 *
 * Functions for calculating edge intersections and building SVG paths
 * with jump arcs at crossing points.
 */

/**
 * Calculate intersection point of two line segments.
 * Segment 1: (p1, p2), Segment 2: (p3, p4)
 *
 * @param {Object} p1 - Start point of segment 1 {x, y}
 * @param {Object} p2 - End point of segment 1 {x, y}
 * @param {Object} p3 - Start point of segment 2 {x, y}
 * @param {Object} p4 - End point of segment 2 {x, y}
 * @returns {Object|null} Intersection point {x, y, t, u} or null if no intersection
 *   t = parameter along segment 1 (0-1 means intersection is within segment)
 *   u = parameter along segment 2 (0-1 means intersection is within segment)
 */
export function lineSegmentIntersection(p1, p2, p3, p4) {
  const denom = (p1.x - p2.x) * (p3.y - p4.y) - (p1.y - p2.y) * (p3.x - p4.x);

  // Parallel lines (or nearly parallel)
  if (Math.abs(denom) < 1e-10) return null;

  const t = ((p1.x - p3.x) * (p3.y - p4.y) - (p1.y - p3.y) * (p3.x - p4.x)) / denom;
  const u = -((p1.x - p2.x) * (p1.y - p3.y) - (p1.y - p2.y) * (p1.x - p3.x)) / denom;

  // Check if intersection is within both segments (with small margin to avoid edge cases)
  if (t > 0.02 && t < 0.98 && u > 0.02 && u < 0.98) {
    return {
      x: p1.x + t * (p2.x - p1.x),
      y: p1.y + t * (p2.y - p1.y),
      t,
      u
    };
  }

  return null;
}

/**
 * Find all intersection points between a "jumping" edge and all other edges.
 *
 * @param {Array} jumpingEdgePoints - Array of {x, y} points for the jumping edge
 * @param {Array} allOtherEdgesPoints - Array of arrays, each containing {x, y} points for other edges
 * @returns {Array} Array of intersection objects { x, y, segmentIndex, t } sorted by segmentIndex then t
 */
export function findAllIntersections(jumpingEdgePoints, allOtherEdgesPoints) {
  const intersections = [];

  // For each segment of the jumping edge
  for (let i = 0; i < jumpingEdgePoints.length - 1; i++) {
    const p1 = jumpingEdgePoints[i];
    const p2 = jumpingEdgePoints[i + 1];

    // Check against all segments of all other edges
    for (const otherEdgePoints of allOtherEdgesPoints) {
      for (let j = 0; j < otherEdgePoints.length - 1; j++) {
        const p3 = otherEdgePoints[j];
        const p4 = otherEdgePoints[j + 1];

        const intersection = lineSegmentIntersection(p1, p2, p3, p4);
        if (intersection) {
          intersections.push({
            x: intersection.x,
            y: intersection.y,
            segmentIndex: i,
            t: intersection.t
          });
        }
      }
    }
  }

  // Sort by segment index, then by t parameter (position along segment)
  intersections.sort((a, b) => {
    if (a.segmentIndex !== b.segmentIndex) {
      return a.segmentIndex - b.segmentIndex;
    }
    return a.t - b.t;
  });

  // Merge intersections that are too close together
  return mergeCloseIntersections(intersections, 16); // 2 * arcRadius
}

/**
 * Merge intersections that are too close together to prevent overlapping arcs.
 *
 * @param {Array} intersections - Sorted array of intersection objects
 * @param {number} minDistance - Minimum distance between intersections
 * @returns {Array} Filtered array with close intersections merged
 */
function mergeCloseIntersections(intersections, minDistance) {
  if (intersections.length <= 1) return intersections;

  const merged = [intersections[0]];

  for (let i = 1; i < intersections.length; i++) {
    const prev = merged[merged.length - 1];
    const curr = intersections[i];

    // Calculate distance between intersections
    const dx = curr.x - prev.x;
    const dy = curr.y - prev.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // Only add if far enough from previous intersection
    if (distance >= minDistance) {
      merged.push(curr);
    }
  }

  return merged;
}

/**
 * Build SVG path with jump arcs at intersection points.
 *
 * @param {Array} points - Array of {x, y} points (source -> waypoints -> target)
 * @param {Array} intersections - Array of intersection points with segmentIndex and t
 * @param {number} arcRadius - Radius of the jump arc (default: 8)
 * @returns {string} SVG path string
 */
export function buildPathWithJumps(points, intersections, arcRadius = 8) {
  if (intersections.length === 0 || points.length < 2) {
    // No intersections, return simple path
    let path = `M ${points[0].x},${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      path += ` L ${points[i].x},${points[i].y}`;
    }
    return path;
  }

  let path = `M ${points[0].x},${points[0].y}`;
  let currentIntersectionIdx = 0;

  for (let segIdx = 0; segIdx < points.length - 1; segIdx++) {
    const p1 = points[segIdx];
    const p2 = points[segIdx + 1];

    // Collect intersections for this segment
    const segmentIntersections = [];
    while (
      currentIntersectionIdx < intersections.length &&
      intersections[currentIntersectionIdx].segmentIndex === segIdx
    ) {
      segmentIntersections.push(intersections[currentIntersectionIdx]);
      currentIntersectionIdx++;
    }

    if (segmentIntersections.length === 0) {
      // No intersections on this segment - straight line
      path += ` L ${p2.x},${p2.y}`;
    } else {
      // Build segment with arcs at intersections
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const segmentLength = Math.sqrt(dx * dx + dy * dy);

      if (segmentLength < 1) {
        // Segment too short, just draw line
        path += ` L ${p2.x},${p2.y}`;
        continue;
      }

      // Unit vector along segment
      const ux = dx / segmentLength;
      const uy = dy / segmentLength;

      for (const inter of segmentIntersections) {
        // Calculate arc start and end points
        // Ensure we don't go past segment boundaries
        const distFromStart = inter.t * segmentLength;
        const distFromEnd = (1 - inter.t) * segmentLength;

        // Adjust arc radius if too close to segment ends
        const effectiveRadius = Math.min(
          arcRadius,
          distFromStart - 2,
          distFromEnd - 2
        );

        if (effectiveRadius < 3) {
          // Not enough space for arc, skip this intersection
          continue;
        }

        // Point just before intersection (arc start)
        const beforeX = inter.x - ux * effectiveRadius;
        const beforeY = inter.y - uy * effectiveRadius;

        // Point just after intersection (arc end)
        const afterX = inter.x + ux * effectiveRadius;
        const afterY = inter.y + uy * effectiveRadius;

        // Draw line to arc start point
        path += ` L ${beforeX},${beforeY}`;

        // Draw arc (semicircle jump)
        // A rx ry x-axis-rotation large-arc-flag sweep-flag x y
        // sweep-flag: 1 = clockwise (arc curves to the right of direction)
        path += ` A ${effectiveRadius} ${effectiveRadius} 0 0 1 ${afterX},${afterY}`;
      }

      // Line to end of segment
      path += ` L ${p2.x},${p2.y}`;
    }
  }

  return path;
}
