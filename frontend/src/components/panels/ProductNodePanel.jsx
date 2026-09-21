import { useStore } from "../../store";
import { CardInfo, Input, ClassDefinitionDisplay } from "../ui";
import InformationPresenter from "./panelElements/InformationPresenter";
import { BASE_CLASS_DEFINITIONS } from "../../constants/baseClassDefinitions";

const selector = (store) => ({
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  updateNode: store.updateNode,
  showClassDefinitions: store.showClassDefinitions,
});

export default function ProductNodePanel() {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();
  const element = store.getElementDataById(activeElementId);

  if (!element) return null;

  return (
    <div className="node-panel">
      <CardInfo
        rows={[
          { label: 'Element ID', value: element.id },
          { label: 'Type', value: 'Product Node' }
        ]}
      />
      {store.showClassDefinitions && (
        <ClassDefinitionDisplay definition={BASE_CLASS_DEFINITIONS.product} />
      )}

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
