import { useStore } from "../../store";
import { useRef } from "react";
import EditableEdgePath from "./EditableEdgePath";

export default function AssignmentEdge({
  id,
  data,
  source,
  target,
  sourceHandle,
  targetHandle,
  selected,
}) {
  // Get global edge label visibility setting
  const showEdgeLabels = useStore((state) => state.showEdgeLabels);
  const updateEdge = useStore((state) => state.updateEdge);

  // Get local edge label visibility (default to true if not set)
  const showLocalLabel = data?.showLabel ?? true;

  // Show label only if BOTH global AND local settings are true
  const shouldShowLabel = showEdgeLabels && showLocalLabel;

  // Use custom name if defined, otherwise show default "Assignment"
  const displayName = (data?.name && data.name !== "undefined" && data.name.length > 0)
    ? data.name
    : "Assignment";

  // Get label offset from data (default to {x: 0, y: 0})
  const labelOffset = data?.labelOffset || { x: 0, y: 0 };

  // Drag state
  const dragRef = useRef({ isDragging: false, startX: 0, startY: 0, offsetX: 0, offsetY: 0 });

  const handleMouseDown = (e) => {
    e.stopPropagation();
    e.preventDefault();

    dragRef.current = {
      isDragging: true,
      startX: e.clientX,
      startY: e.clientY,
      offsetX: labelOffset.x,
      offsetY: labelOffset.y
    };

    document.addEventListener('mousemove', handleMouseMove, { capture: true });
    document.addEventListener('mouseup', handleMouseUp, { capture: true });
  };

  const handleMouseMove = (e) => {
    if (!dragRef.current.isDragging) return;

    e.stopPropagation();
    e.preventDefault();

    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;

    const newOffset = {
      x: dragRef.current.offsetX + dx,
      y: dragRef.current.offsetY + dy
    };

    updateEdge(id, { labelOffset: newOffset });
  };

  const handleMouseUp = (e) => {
    if (dragRef.current.isDragging) {
      e.stopPropagation();
      e.preventDefault();
    }

    dragRef.current.isDragging = false;
    document.removeEventListener('mousemove', handleMouseMove, { capture: true });
    document.removeEventListener('mouseup', handleMouseUp, { capture: true });
  };

  return (
    <EditableEdgePath
      id={id}
      data={data}
      source={source}
      target={target}
      sourceHandle={sourceHandle}
      targetHandle={targetHandle}
      selected={selected}
      edgeColor="#808080"
      edgeWidth={4}
      edgeDashArray={8}
      showArrowForward={false}
      showArrowBackward={false}
    >
      {shouldShowLabel && (
        <div
          style={{
            border: selected ? '3px solid #2196F3' : '1px solid #a8a29e',
            boxShadow: selected ? '0 0 0 3px rgba(33, 150, 243, 0.3)' : undefined,
            position: 'relative'
          }}
          className="text-center text-xs px-4 py-4 shadow-md rounded-md bg-stone-100/60"
        >
          {/* Drag Handle - only visible when edge is selected */}
          {selected && (
            <div
              onMouseDown={handleMouseDown}
              style={{
                position: 'absolute',
                top: '-6px',
                left: '-6px',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#2196F3',
                border: '2px solid white',
                cursor: 'move',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                zIndex: 10
              }}
              title="Drag to reposition label"
            />
          )}
          <p className="text-base">{displayName}</p>
          <p className="text-xs italic">{id}</p>
        </div>
      )}
    </EditableEdgePath>
  );
}