import { useStore } from "../../store";
import { CardInfo, Input, Select, ClassDefinitionDisplay } from "../ui";
import InformationPresenter from "./panelElements/InformationPresenter";
import { BASE_CLASS_DEFINITIONS } from "../../constants/baseClassDefinitions";

const selector = (store) => ({
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  updateNode: store.updateNode,
  resourceTyps: store.resourceTyps,
  showClassDefinitions: store.showClassDefinitions,
});

export default function ResourceNodePanel() {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();
  const element = store.getElementDataById(activeElementId);
  const TECHNICALRESOURCESTYPS = store.resourceTyps;

  if (!element) return null;

  // Find the description for the currently selected resource type
  const selectedResourceType = TECHNICALRESOURCESTYPS.find(
    (r) => r.resourceType === element.data.resourceType
  );

  return (
    <div className="node-panel">
      <CardInfo
        rows={[
          { label: 'Element ID', value: element.id },
          { label: 'Type', value: 'Resource Node' }
        ]}
      />
      {store.showClassDefinitions && (
        <ClassDefinitionDisplay definition={BASE_CLASS_DEFINITIONS.resource} />
      )}

      <div className="config-section">
        <label className="config-label">
          Resource Class
        </label>
        <Select
          value={element.data.resourceType}
          options={TECHNICALRESOURCESTYPS}
          optionValue="resourceType"
          optionKey="resourceType"
          onChange={(val) => store.updateNode(activeElementId, { resourceType: val })}
          placeholder="Select resource type..."
          disabled={TECHNICALRESOURCESTYPS.length === 0}
        />
        {store.showClassDefinitions && selectedResourceType && (
          <ClassDefinitionDisplay definition={selectedResourceType.description} />
        )}
      </div>

      <div className="config-section">
        <label className="config-label">
          Name
        </label>
        <Input
          value={element.data.name}
          onChange={(val) => store.updateNode(activeElementId, { name: val })}
          placeholder="Enter element name..."
        />
      </div>

      <div className="config-section">
        <InformationPresenter activeElementId={activeElementId} />
      </div>
    </div>
  );
}
