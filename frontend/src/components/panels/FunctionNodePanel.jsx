import { useStore } from "../../store";
import { CardInfo, Input, Select, ClassDefinitionDisplay } from "../ui";
import InformationPresenter from "./panelElements/InformationPresenter.jsx";
import { BASE_CLASS_DEFINITIONS } from "../../constants/baseClassDefinitions";

const selector = (store) => ({
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  updateNode: store.updateNode,
  functionTyps: store.functionTyps,
  showClassDefinitions: store.showClassDefinitions,
});

export default function FunctionNodePanel() {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();
  const element = store.getElementDataById(activeElementId);
  const FUNCTIONTYPS = store.functionTyps;

  if (!element) return null;

  // Find the description for the currently selected function type
  const selectedFunctionType = FUNCTIONTYPS.find(
    (f) => f.functionType === element.data.functionType
  );

  return (
    <div className="node-panel">
      <CardInfo
        rows={[
          { label: 'Element ID', value: element.id },
          { label: 'Type', value: 'Function Node' }
        ]}
      />
      {store.showClassDefinitions && (
        <ClassDefinitionDisplay definition={BASE_CLASS_DEFINITIONS.function} />
      )}

      <div className="config-section">
        <label className="config-label">
          Function Class
        </label>
        <Select
          value={element.data.functionType}
          options={FUNCTIONTYPS}
          optionValue="functionType"
          optionKey="functionType"
          onChange={(val) => store.updateNode(activeElementId, { functionType: val })}
          placeholder="Select function type..."
        />
        {store.showClassDefinitions && selectedFunctionType && (
          <ClassDefinitionDisplay definition={selectedFunctionType.description} />
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
