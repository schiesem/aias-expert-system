import { Handle, Position } from "reactflow";
import { useStore } from "../../store";
import { getRectangleAnchorPoints } from "../../utils/anchorUtils";
import { getShortClassName } from "../../utils/annotationUtils";

const selector = (store) => ({
  showNodeId: store.showNodeId,
  showNodeType: store.showNodeType,
  showAnchorPoints: store.showAnchorPoints,
});

const NODE_WIDTH = 144; // w-36 = 144px
const NODE_HEIGHT = 112; // h-28 = 112px

export default function FunctionNode({ id, type, data, selected }) {
  const store = useStore(selector);

  // Calculate anchor points
  const anchorPoints = getRectangleAnchorPoints(NODE_WIDTH, NODE_HEIGHT);
  return (
    <div
      className="w-36 h-28 shrink-0 grow-0 rounded-none text-center shadow-lg bg-lime-200 border-3 relative"
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
          {data.name === undefined || data.name === "undefined" || data.name.length === 0 ? "Function": data.name}
        </h1>
        <div className="text-xs italic" style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
          <p>{data.functionType === "undefined" ? "no class selected":getShortClassName(data.functionType)}</p>
          {store.showNodeId && <p>{id}</p>}
          {store.showNodeType && <p>{type}</p>}
        </div>
      </div>
    </div>
  );
}
