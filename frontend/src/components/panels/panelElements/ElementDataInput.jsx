import { useStore } from "../../../store";

const selector = (store) => ({
  updateNode: store.updateNode,
  updateEdge: store.updateEdge,
  getElementDataById: store.getElementDataById,
});

// Get default name based on element type
function getDefaultName(element) {
  if (!element) return "";

  const type = element.type;

  // Edge default names
  if (type === "CommunicationEdge") return "Communication";
  if (type === "AssignmentEdge") return "Assignment";
  if (type === "FlowEdge") return "Flow";

  // Node default names
  if (type === "FunctionNode") return "Function";
  if (type === "ResourceNode") return "Resource";
  if (type === "ProductNode") return "Product";

  return "";
}

export default function ElementDataInput({ activeElementId }) {
  const store = useStore(selector);
  const element = store.getElementDataById(activeElementId);

  // Determine if this is a node or edge based on the element's type
  const isEdge = element?.type?.includes("Edge");

  // Get the current name or use default
  const currentName = element?.data?.name;
  const displayName = (currentName === "undefined" || !currentName || currentName.length === 0)
    ? getDefaultName(element)
    : currentName;

  return (
    <div>
      <input
        className="bg-stone-100 hover:bg-stone-200"
        type="text"
        value={displayName}
        onChange={(event) => {
          if (isEdge) {
            store.updateEdge(activeElementId, { name: event.target.value });
          } else {
            store.updateNode(activeElementId, { name: event.target.value });
          }
        }}
      />
    </div>
  );
}
