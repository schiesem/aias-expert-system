import { useStore } from "../../store";
import { CardInfo, Input, ClassDefinitionDisplay } from "../ui";
import InformationPresenter from "./panelElements/InformationPresenter";
import { BASE_CLASS_DEFINITIONS } from "../../constants/baseClassDefinitions";

const selector = (store) => ({
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  updateEdge: store.updateEdge,
  nodes: store.nodes,
  showClassDefinitions: store.showClassDefinitions,
});

export default function AssignmentEdgePanel() {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();
  const element = store.getElementDataById(activeElementId);

  if (!element) return null;

  // Get source and target node names
  const sourceNode = store.nodes.find(n => n.id === element.source);
  const targetNode = store.nodes.find(n => n.id === element.target);

  return (
    <div className="edge-panel">
      <CardInfo
        rows={[
          { label: 'Edge ID', value: element.id },
          { label: 'Type', value: 'Assignment' },
          { label: 'Source', value: sourceNode?.data?.name || sourceNode?.id || 'N/A' },
          { label: 'Target', value: targetNode?.data?.name || targetNode?.id || 'N/A' }
        ]}
      />
      {store.showClassDefinitions && (
        <ClassDefinitionDisplay definition={BASE_CLASS_DEFINITIONS.assignment} />
      )}

      <div className="config-section">
        <label className="config-label">
          Name
        </label>
        <Input
          value={element.data.name}
          onChange={(val) => store.updateEdge(activeElementId, { name: val })}
          placeholder="Enter edge name..."
        />
      </div>

      <div className="config-section">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={element.data.showLabel ?? true}
            onChange={(e) => store.updateEdge(activeElementId, { showLabel: e.target.checked })}
            className="w-4 h-4"
          />
          <span className="text-sm">Show Edge Label</span>
        </label>
      </div>

      <div className="config-section">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={element.data.jumpOverCrossings || false}
            onChange={(e) => store.updateEdge(activeElementId, { jumpOverCrossings: e.target.checked })}
            className="w-4 h-4"
          />
          <span className="text-sm">Crossing Activated</span>
        </label>
      </div>

      <div className="config-section">
        <InformationPresenter activeElementId={activeElementId} />
      </div>
    </div>
  );
}
