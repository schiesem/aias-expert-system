import React, { useState, useCallback, useRef, useMemo } from "react";
import { BaseEdge, EdgeLabelRenderer, useNodes, useReactFlow } from "reactflow";
import { getEdgeParams } from "./utils";
import { useStore } from "../../store";
import { getRectangleAnchorPoints, getEllipseAnchorPoints, getCircleAnchorPoints } from "../../utils/anchorUtils";
import { findAllIntersections, buildPathWithJumps } from "../../utils/edgeGeometryUtils";

/**
 * Editable Edge Path Component
 *
 * Renders an edge with draggable waypoint handles (small white dots)
 * to allow manual adjustment of edge paths to avoid overlaps.
 *
 * Waypoints are stored in edge.data.waypoints as [{x, y}, {x, y}, ...]
 */
const selector = (store) => ({
  updateEdge: store.updateEdge,
  showEdgeLabels: store.showEdgeLabels,
  edges: store.edges,
});

export default function EditableEdgePath({
  id,
  data,
  source,
  target,
  sourceHandle,
  targetHandle,
  selected,
  edgeColor = "#808080",
  edgeWidth = 4,
  edgeDashArray = null,
  showArrowForward = false,
  showArrowBackward = false,
  children, // For edge label
}) {
  const nodes = useNodes();
  const { screenToFlowPosition, getEdge } = useReactFlow();
  const store = useStore(selector);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedWaypointIndex, setDraggedWaypointIndex] = useState(null);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 });
  const [isDraggingAnchor, setIsDraggingAnchor] = useState(false);
  const [draggedAnchorType, setDraggedAnchorType] = useState(null); // 'source' or 'target'

  // Use refs to track current dragging state for event handlers
  const isDraggingAnchorRef = React.useRef(false);
  const draggedAnchorTypeRef = React.useRef(null);
  const currentAnchorIndexRef = React.useRef(null); // Track current anchor to avoid redundant updates

  const sourceNode = nodes.find((n) => n.id === source);
  const targetNode = nodes.find((n) => n.id === target);

  if (!sourceNode || !targetNode) {
    return null;
  }

  // ReactFlow stores handle IDs in the edge object itself
  const edge = getEdge(id);

  // Use handle IDs from edge object, fallback to props
  const actualSourceHandle = edge?.sourceHandle || sourceHandle;
  const actualTargetHandle = edge?.targetHandle || targetHandle;

  // Calculate anchor point positions and directions if handles are specified
  const getAnchorInfo = (node, handleId) => {
    // Get node center position
    const nodeCenterX = node.position.x + (node.width || 100) / 2;
    const nodeCenterY = node.position.y + (node.height || 100) / 2;

    if (!handleId || !handleId.startsWith('anchor-')) {
      // Fallback to center if no anchor handle
      return {
        x: nodeCenterX,
        y: nodeCenterY,
        offsetX: 0,
        offsetY: 0
      };
    }

    const anchorIndex = parseInt(handleId.replace('anchor-', ''));
    const nodeType = node.type;

    // Get node dimensions based on type
    let anchorOffset = { x: 0, y: 0 };

    if (nodeType === 'FunctionNode') {
      const width = 144, height = 112;
      const anchors = getRectangleAnchorPoints(width, height);
      const anchor = anchors.find(a => a.index === anchorIndex);
      if (anchor) {
        anchorOffset = { x: anchor.x, y: anchor.y };
      }
    } else if (nodeType === 'ResourceNode') {
      const width = 176, height = 112;
      const anchors = getEllipseAnchorPoints(width, height);
      const anchor = anchors.find(a => a.index === anchorIndex);
      if (anchor) {
        anchorOffset = { x: anchor.x, y: anchor.y };
      }
    } else if (nodeType === 'ProductNode') {
      const radius = 56;
      const anchors = getCircleAnchorPoints(radius);
      const anchor = anchors.find(a => a.index === anchorIndex);
      if (anchor) {
        anchorOffset = { x: anchor.x, y: anchor.y };
      }
    }

    return {
      x: nodeCenterX + anchorOffset.x,
      y: nodeCenterY + anchorOffset.y,
      offsetX: anchorOffset.x,
      offsetY: anchorOffset.y
    };
  };

  const sourceAnchorInfo = getAnchorInfo(sourceNode, actualSourceHandle);
  const targetAnchorInfo = getAnchorInfo(targetNode, actualTargetHandle);

  const sx = sourceAnchorInfo.x;
  const sy = sourceAnchorInfo.y;
  const tx = targetAnchorInfo.x;
  const ty = targetAnchorInfo.y;

  // Calculate position/direction for arrows
  const getPositionFromAngle = (dx, dy) => {
    const angle = Math.atan2(dy, dx) * (180 / Math.PI);
    if (angle >= -45 && angle < 45) return 'right';
    if (angle >= 45 && angle < 135) return 'bottom';
    if (angle >= 135 || angle < -135) return 'left';
    return 'top';
  };

  const sourcePos = getPositionFromAngle(tx - sx, ty - sy);
  const targetPos = getPositionFromAngle(sx - tx, sy - ty);

  // Get waypoints from data, or use default (empty array for direct line)
  const waypoints = data?.waypoints || [];

  // Check if this edge should jump over crossings
  const jumpOverCrossings = data?.jumpOverCrossings || false;

  // Get all edges for intersection calculation (only when jumping is enabled)
  const allEdges = store.edges;

  // Helper function to get edge points for intersection calculation
  const getEdgePoints = useCallback((otherEdge) => {
    const sNode = nodes.find(n => n.id === otherEdge.source);
    const tNode = nodes.find(n => n.id === otherEdge.target);
    if (!sNode || !tNode) return null;

    const sAnchor = getAnchorInfo(sNode, otherEdge.sourceHandle);
    const tAnchor = getAnchorInfo(tNode, otherEdge.targetHandle);

    const points = [{ x: sAnchor.x, y: sAnchor.y }];

    if (otherEdge.data?.waypoints) {
      points.push(...otherEdge.data.waypoints);
    }

    points.push({ x: tAnchor.x, y: tAnchor.y });

    return points;
  }, [nodes, getAnchorInfo]);

  // Calculate intersections with other edges (memoized for performance)
  const edgePath = useMemo(() => {
    // Build points array for this edge
    const points = [
      { x: sx, y: sy },
      ...waypoints,
      { x: tx, y: ty }
    ];

    if (!jumpOverCrossings) {
      // Default: simple path without jumps
      let pathSegments = [`M ${sx},${sy}`];
      waypoints.forEach((wp) => {
        pathSegments.push(`L ${wp.x},${wp.y}`);
      });
      pathSegments.push(`L ${tx},${ty}`);
      return pathSegments.join(" ");
    }

    // Get all other edges' points (excluding this edge)
    const otherEdgesPoints = allEdges
      .filter(e => e.id !== id)
      .map(e => getEdgePoints(e))
      .filter(Boolean);

    // Find intersections
    const intersections = findAllIntersections(points, otherEdgesPoints);

    // Build path with jump arcs (radius = 8 pixels)
    return buildPathWithJumps(points, intersections, 8);
  }, [sx, sy, tx, ty, waypoints, jumpOverCrossings, allEdges, id, getEdgePoints]);

  // Calculate label position (middle of path)
  const baseLabelX = waypoints.length > 0
    ? waypoints[Math.floor(waypoints.length / 2)].x
    : (sx + tx) / 2;
  const baseLabelY = waypoints.length > 0
    ? waypoints[Math.floor(waypoints.length / 2)].y
    : (sy + ty) / 2;

  // Apply label offset from data (for drag & drop positioning)
  const labelOffset = data?.labelOffset || { x: 0, y: 0 };
  const labelX = baseLabelX + labelOffset.x;
  const labelY = baseLabelY + labelOffset.y;

  // Handle waypoint right-click to delete
  const handleWaypointContextMenu = (index, event) => {
    event.preventDefault();
    event.stopPropagation();

    const updatedWaypoints = [...(data?.waypoints || [])];
    updatedWaypoints.splice(index, 1);

    store.updateEdge(id, {
      waypoints: updatedWaypoints,
    });
  };

  // Handle waypoint drag
  const handleWaypointMouseDown = (index, event) => {
    event.stopPropagation();
    setIsDragging(true);
    setDraggedWaypointIndex(index);
  };

  const handleWaypointDrag = useCallback((event) => {
    if (!isDragging || draggedWaypointIndex === null) return;

    // Convert screen coordinates to flow coordinates
    const flowPosition = screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    const updatedWaypoints = [...(data?.waypoints || [])];
    updatedWaypoints[draggedWaypointIndex] = {
      x: flowPosition.x,
      y: flowPosition.y,
    };

    store.updateEdge(id, {
      waypoints: updatedWaypoints,
    });
  }, [isDragging, draggedWaypointIndex, id, data?.waypoints, store, screenToFlowPosition]);

  // Handle anchor point drag (source/target reconnection)
  const handleAnchorMouseDown = (anchorType, event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDraggingAnchor(true);
    setDraggedAnchorType(anchorType);
    isDraggingAnchorRef.current = true;
    draggedAnchorTypeRef.current = anchorType;

    // Initialize current anchor index from the edge's current handle
    const currentHandle = anchorType === 'source' ? actualSourceHandle : actualTargetHandle;
    if (currentHandle && currentHandle.startsWith('anchor-')) {
      const currentIndex = parseInt(currentHandle.replace('anchor-', ''), 10);
      currentAnchorIndexRef.current = currentIndex;
    } else {
      currentAnchorIndexRef.current = null;
    }
  };

  const handleAnchorDrag = useCallback((event) => {
    if (!isDraggingAnchorRef.current || !draggedAnchorTypeRef.current) {
      return;
    }

    // Convert screen coordinates to flow coordinates
    const flowPosition = screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    // Find which node we're hovering over
    const hoveredNode = draggedAnchorTypeRef.current === 'source' ? sourceNode : targetNode;

    // Calculate which anchor point is closest to the mouse
    const nodeCenterX = hoveredNode.position.x + (hoveredNode.width || 100) / 2;
    const nodeCenterY = hoveredNode.position.y + (hoveredNode.height || 100) / 2;

    let anchors = [];
    if (hoveredNode.type === 'FunctionNode') {
      anchors = getRectangleAnchorPoints(144, 112);
    } else if (hoveredNode.type === 'ResourceNode') {
      anchors = getEllipseAnchorPoints(176, 112);
    } else if (hoveredNode.type === 'ProductNode') {
      anchors = getCircleAnchorPoints(56);
    }

    // Find closest anchor to mouse position
    let closestAnchor = null;
    let minDistance = Infinity;

    anchors.forEach((anchor) => {
      const anchorX = nodeCenterX + anchor.x;
      const anchorY = nodeCenterY + anchor.y;
      const distance = Math.sqrt(
        Math.pow(flowPosition.x - anchorX, 2) +
        Math.pow(flowPosition.y - anchorY, 2)
      );

      if (distance < minDistance) {
        minDistance = distance;
        closestAnchor = anchor;
      }
    });

    // Update edge handle ONLY if anchor index has changed
    if (closestAnchor !== null && closestAnchor.index !== currentAnchorIndexRef.current) {
      const newHandleId = `anchor-${closestAnchor.index}`;

      // Update the ref to track current anchor
      currentAnchorIndexRef.current = closestAnchor.index;

      if (draggedAnchorTypeRef.current === 'source') {
        store.updateEdge(id, {
          sourceHandle: newHandleId,
        });
      } else {
        store.updateEdge(id, {
          targetHandle: newHandleId,
        });
      }
    }
  }, [id, sourceNode, targetNode, store, screenToFlowPosition]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setDraggedWaypointIndex(null);
    setIsDraggingAnchor(false);
    setDraggedAnchorType(null);
    isDraggingAnchorRef.current = false;
    draggedAnchorTypeRef.current = null;
    currentAnchorIndexRef.current = null; // Reset current anchor index
  }, []);

  // Combined mouse move handler that checks refs
  const handleMouseMove = useCallback((event) => {
    if (isDragging) {
      handleWaypointDrag(event);
    } else if (isDraggingAnchorRef.current) {
      handleAnchorDrag(event);
    }
  }, [isDragging, handleWaypointDrag, handleAnchorDrag]);

  // Attach global mouse event listeners when dragging
  React.useEffect(() => {
    if (isDragging || isDraggingAnchor) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      return () => {
        window.removeEventListener("mousemove", handleMouseMove);
        window.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isDragging, isDraggingAnchor, handleMouseMove, handleMouseUp]);

  // Calculate arrow position and rotation based on incoming edge direction
  const arrowOffset = 4; // Offset from anchor point to make arrow fully visible

  // For forward arrow (at target): direction from last waypoint (or source) to target
  let forwardDirX, forwardDirY;
  if (waypoints.length > 0) {
    const lastWaypoint = waypoints[waypoints.length - 1];
    forwardDirX = tx - lastWaypoint.x;
    forwardDirY = ty - lastWaypoint.y;
  } else {
    forwardDirX = tx - sx;
    forwardDirY = ty - sy;
  }
  const forwardDirLength = Math.sqrt(forwardDirX ** 2 + forwardDirY ** 2);
  const forwardUnitX = forwardDirLength > 0 ? forwardDirX / forwardDirLength : 0;
  const forwardUnitY = forwardDirLength > 0 ? forwardDirY / forwardDirLength : 0;

  const forwardArrowX = tx + forwardUnitX * arrowOffset;
  const forwardArrowY = ty + forwardUnitY * arrowOffset;
  const forwardRotation = Math.atan2(forwardDirY, forwardDirX) * (180 / Math.PI);

  // For backward arrow (at source): direction from first waypoint (or target) to source
  let backwardDirX, backwardDirY;
  if (waypoints.length > 0) {
    const firstWaypoint = waypoints[0];
    backwardDirX = sx - firstWaypoint.x;
    backwardDirY = sy - firstWaypoint.y;
  } else {
    backwardDirX = sx - tx;
    backwardDirY = sy - ty;
  }
  const backwardDirLength = Math.sqrt(backwardDirX ** 2 + backwardDirY ** 2);
  const backwardUnitX = backwardDirLength > 0 ? backwardDirX / backwardDirLength : 0;
  const backwardUnitY = backwardDirLength > 0 ? backwardDirY / backwardDirLength : 0;

  const backwardArrowX = sx + backwardUnitX * arrowOffset;
  const backwardArrowY = sy + backwardUnitY * arrowOffset;
  const backwardRotation = Math.atan2(backwardDirY, backwardDirX) * (180 / Math.PI);

  return (
    <>
      {/* Invisible clickable thick edge for interaction */}
      <path
        d={edgePath}
        stroke="transparent"
        strokeWidth={20}
        fill="none"
        style={{ cursor: "context-menu" }}
      />

      {/* Selection glow - only visible when selected */}
      {selected && (
        <path
          d={edgePath}
          stroke="#2196F3"
          strokeWidth={edgeWidth + 6}
          fill="none"
          strokeDasharray={edgeDashArray}
          style={{
            opacity: 0.3,
            pointerEvents: "none",
          }}
        />
      )}

      {/* Visible edge */}
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: selected ? "#2196F3" : edgeColor,
          strokeWidth: edgeWidth,
          strokeDasharray: edgeDashArray,
          pointerEvents: "none", // Don't block clicks, use invisible edge instead
        }}
      />

      {/* Forward arrow - larger and offset from node */}
      {showArrowForward && (
        <g transform={`translate(${forwardArrowX}, ${forwardArrowY})`}>
          <polygon
            points="-12,-8 0,0 -12,8"
            fill={edgeColor}
            transform={`rotate(${forwardRotation})`}
          />
        </g>
      )}

      {/* Backward arrow - larger and offset from node */}
      {showArrowBackward && (
        <g transform={`translate(${backwardArrowX}, ${backwardArrowY})`}>
          <polygon
            points="-12,-8 0,0 -12,8"
            fill={edgeColor}
            transform={`rotate(${backwardRotation})`}
          />
        </g>
      )}

      {/* Draggable waypoint handles - large when selected, small preview when not */}
      {waypoints.map((wp, index) => (
        <EdgeLabelRenderer key={`waypoint-${index}`}>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${wp.x}px, ${wp.y}px)`,
              width: selected ? "12px" : "6px",
              height: selected ? "12px" : "6px",
              borderRadius: "50%",
              backgroundColor: "white",
              border: selected ? `2px solid ${edgeColor}` : `1px solid ${edgeColor}`,
              cursor: selected ? "move" : "default",
              pointerEvents: selected ? "all" : "none",
              opacity: selected ? 1 : 0.5,
              zIndex: 1000,
            }}
            onMouseDown={(e) => handleWaypointMouseDown(index, e)}
            onContextMenu={(e) => handleWaypointContextMenu(index, e)}
          />
        </EdgeLabelRenderer>
      ))}

      {/* Draggable anchor handles - only visible when edge is selected */}
      {selected && (
        <>
          {/* Source anchor handle */}
          <EdgeLabelRenderer key="source-anchor-handle">
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${sx}px, ${sy}px)`,
                width: "14px",
                height: "14px",
                borderRadius: "50%",
                backgroundColor: "#4CAF50",
                border: "2px solid white",
                cursor: "move",
                pointerEvents: "all",
                zIndex: 1001,
                boxShadow: "0 0 5px rgba(0,0,0,0.3)",
              }}
              onMouseDown={(e) => handleAnchorMouseDown('source', e)}
              title="Drag to change source anchor point"
            />
          </EdgeLabelRenderer>

          {/* Target anchor handle */}
          <EdgeLabelRenderer key="target-anchor-handle">
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${tx}px, ${ty}px)`,
                width: "14px",
                height: "14px",
                borderRadius: "50%",
                backgroundColor: "#f44336",
                border: "2px solid white",
                cursor: "move",
                pointerEvents: "all",
                zIndex: 1001,
                boxShadow: "0 0 5px rgba(0,0,0,0.3)",
              }}
              onMouseDown={(e) => handleAnchorMouseDown('target', e)}
              title="Drag to change target anchor point"
            />
          </EdgeLabelRenderer>
        </>
      )}

      {/* Edge label renderer - controlled by global setting */}
      {children && store.showEdgeLabels && (
        <EdgeLabelRenderer>
          {React.cloneElement(children, {
            style: {
              ...children.props.style,
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all", // Label is clickable for selection
              zIndex: 1002, // Above edges (1000) and anchor handles (1001)
            }
          })}
        </EdgeLabelRenderer>
      )}
    </>
  );
}
