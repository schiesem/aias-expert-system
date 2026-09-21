// Funktion zum Extrahieren eines spezifischen Teils aus der JSON-Struktur
export const extractCategory = (obj, ...keys) => {
  return keys.reduce((acc, key) => acc?.[key], obj) || null;
};

export const convertToKeyValuePair = (array, keyName) => {
  return array.map((item) => ({ [keyName]: `${item}` }));
};

export const sliceData = ({ data, keys, overwrite = false }) => {
  if (!data || typeof data !== "object") {
    console.error("Ungültiges Datenobjekt übergeben.");
    return null;
  }

  const removeKeys = (obj, keysToRemove) => {
    if (Array.isArray(obj)) {
      return obj.map((item) => removeKeys(item, keysToRemove));
    } else if (obj !== null && typeof obj === "object") {
      return Object.fromEntries(
        Object.entries(obj)
          .filter(([key]) => !keysToRemove.includes(key))
          .map(([key, value]) => [key, removeKeys(value, keysToRemove)])
      );
    }
    return obj;
  };

  const cleanedData = removeKeys(data, keys);

  if (overwrite) {
    Object.keys(data).forEach((key) => delete data[key]); // Original-Objekt leeren
    Object.assign(data, cleanedData); // Bereinigte Daten in das Original-Objekt schreiben
  }

  return overwrite ? data : cleanedData;
};
