import { Handle, Position } from "reactflow";
import { useStore } from "../../store";
import { getCircleAnchorPoints } from "../../utils/anchorUtils";

const selector = (store) => ({
  showNodeId: store.showNodeId,
  showNodeType: store.showNodeType,
  showAnchorPoints: store.showAnchorPoints,
});

const NODE_RADIUS = 56; // w-28 = 112px diameter, so 56px radius

export default function ProductNode({ id, type, data, selected }) {
  const store = useStore(selector);

  // Calculate anchor points
  const anchorPoints = getCircleAnchorPoints(NODE_RADIUS);
  return (
    <div
      className="w-28 h-28 shrink-0 grow-0 rounded-full text-center shadow-lg bg-rose-200 relative"
      style={{
        border: selected ? '3px solid #2196F3' : '1px solid #a8a29e',
        boxShadow: selected ? '0 0 0 3px rgba(33, 150, 243, 0.3)' : undefined
      }}
    >
      {/* Anchor points as connection handles - small white dots on the border */}
      {anchorPoints.map((anchor) => (
        <Handle
          key={`anchor-${anchor.index}`}
          type="source"
          position={Position.Top}
          id={`anchor-${anchor.index}`}
          isConnectable={true}
          style={{
            position: 'absolute',
            left: `calc(50% + ${anchor.x}px)`,
            top: `calc(50% + ${anchor.y}px)`,
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: 'white',
            border: '2px solid #666',
            transform: 'translate(-50%, -50%)',
            zIndex: 10,
            cursor: 'crosshair',
            opacity: store.showAnchorPoints ? 1 : 0,
            pointerEvents: store.showAnchorPoints ? 'all' : 'none',
          }}
        />
      ))}

      {/* Content - can be dragged from outer edges */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        pointerEvents: 'none',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        height: '100%'
      }}>
        <h1 className="text-lg" style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
          {data.name === undefined || data.name === "undefined" || data.name.length === 0 ? "Product": data.name}
        </h1>
        <div className="text-xs italic" style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
          {store.showNodeId && <p>{id}</p>}
          {store.showNodeType && <p>{type}</p>}
        </div>
      </div>
    </div>
  );
}
