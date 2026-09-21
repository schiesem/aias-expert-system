import { useStore } from "../../../store";

const selector = (store) => ({
  createNode: store.createNode,
});

export default function CreateButton({ nodeType, color, children }) {
  const store = useStore(selector);

  const handleClick = () => {
    store.createNode(nodeType);
  };

  return (
    <button
      className="create-button"
      onClick={handleClick}
      style={{ '--node-color': color }}
      title={`Create ${children} Node`}
    >
      <span className="create-button-label">{children}</span>
    </button>
  );
}
