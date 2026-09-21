import { useStore } from "../../store";
import { CardInfo, Input, Select, ClassDefinitionDisplay } from "../ui";
import InformationPresenter from "./panelElements/InformationPresenter";
import { BASE_CLASS_DEFINITIONS } from "../../constants/baseClassDefinitions";

const selector = (store) => ({
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  communicationTyps: store.communicationTyps,
  updateEdge: store.updateEdge,
  nodes: store.nodes,
  showClassDefinitions: store.showClassDefinitions,
});

export default function CommunicationEdgePanel() {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();
  const COMMUNICATIONTYPS = store.communicationTyps;
  const element = store.getElementDataById(activeElementId);

  if (!element) return null;

  // Get source and target node names
  const sourceNode = store.nodes.find(n => n.id === element.source);
  const targetNode = store.nodes.find(n => n.id === element.target);

  // Find the description for the currently selected communication type
  const selectedCommunicationType = COMMUNICATIONTYPS.find(
    (c) => c.communicationType === element.data.communicationType
  );

  const handleArrowForwardChange = (event) => {
    store.updateEdge(activeElementId, { arrowForward: event.target.checked });
  };

  const handleArrowBackwardChange = (event) => {
    store.updateEdge(activeElementId, { arrowBackward: event.target.checked });
  };

  return (
    <div className="edge-panel">
      <CardInfo
        rows={[
          { label: 'Edge ID', value: element.id },
          { label: 'Type', value: 'Communication' },
          { label: 'Source', value: sourceNode?.data?.name || sourceNode?.id || 'N/A' },
          { label: 'Target', value: targetNode?.data?.name || targetNode?.id || 'N/A' }
        ]}
      />
      {store.showClassDefinitions && (
        <ClassDefinitionDisplay definition={BASE_CLASS_DEFINITIONS.communication} />
      )}

      <div className="config-section">
        <label className="config-label">
          Communication Type
        </label>
        <Select
          value={element.data.communicationType}
          options={COMMUNICATIONTYPS}
          optionValue="communicationType"
          optionKey="communicationType"
          onChange={(val) => store.updateEdge(activeElementId, { communicationType: val })}
          placeholder="Select communication type..."
        />
        {store.showClassDefinitions && selectedCommunicationType && (
          <ClassDefinitionDisplay definition={selectedCommunicationType.description} />
        )}
      </div>

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
        <label className="config-label">
          Direction
        </label>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={element.data.arrowBackward || false}
              onChange={handleArrowBackwardChange}
            />
            <span>Forward (Source → Target)</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={element.data.arrowForward || false}
              onChange={handleArrowForwardChange}
            />
            <span>Backward (Target → Source)</span>
          </label>
        </div>
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
