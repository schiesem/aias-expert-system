import { useStore } from "../../../store";
import { nanoid } from "nanoid";

const selector = (store) => ({
  getElementDataById: store.getElementDataById,
});

export default function InformationPresenter({ activeElementId }) {
  const store = useStore(selector);
  const data = store.getElementDataById(activeElementId).data;

  function objectDataMapper(obj) {
    const objectArray = Object.keys(obj).map((key) => [key, obj[key]]);
    const listItems = objectArray.map((element) => {
      // Format value: if it's an object/array, stringify it; otherwise use as-is
      const value = typeof element[1] === 'object' && element[1] !== null
        ? JSON.stringify(element[1])
        : element[1];

      return (
        <li key={nanoid(4)}>
          {element[0]}: {value}
        </li>
      );
    });
    return listItems;
  }

  return (
    <>

      <div className="text-xs italic">
      <p className="text-sm underline">Selected Element Informations:</p>
        <p>ActiveElementID: {activeElementId}</p>
        <ul>{objectDataMapper(data)}</ul>
      </div>

      <ul></ul>
    </>
  );
}
