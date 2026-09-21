import { useStore } from "../../../store";
import { getShortClassName } from "../../../utils/annotationUtils";

const selector = (store) => ({
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  setNodeType: store.updateNode,
  setEdgeType: store.updateEdge,
});

export default function DropDown({ typeElements, typeKey }) {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();

  return (
    <select
      className="nodrag bg-stone-100 hover:bg-stone-200"
      onChange={(event) => {
        if (typeKey === "communicationType") {
          store.setEdgeType(activeElementId, { [typeKey]: event.target.value });
        } else if (typeKey === "functionType" || typeKey === "resourceType") {
          store.setNodeType(activeElementId, { [typeKey]: event.target.value });
        }
      }}
      value={
        store.getElementDataById(activeElementId)?.data[typeKey] || "undefined"
      }
    >
      <option value="undefined" disabled hidden>
        Choose here
      </option>
      {typeElements.map((element) => (
        <option key={element[typeKey]} value={element[typeKey]}>
          {getShortClassName(element[typeKey])}
        </option>
      ))}
    </select>
  );
}
