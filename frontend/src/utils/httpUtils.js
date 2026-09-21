import { sliceData } from "./dataUtils";

export const fetchData = async ({
  url,
  setFunction,
  setLoading,
  method = "GET",
  body = null,
}) => {
  if (setLoading) setLoading(true);

  try {
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : null,
    });

    if (!response.ok) throw new Error(`Fehler beim Abrufen von ${url}`);

    const data = await response.json();
    console.log(`Antwort des Servers zu fetchData-Funktion:`, data);

    if (setFunction) setFunction(data);
    else return data;
  } catch (error) {
    console.error("Fehler:", error);
  } finally {
    if (setLoading) setLoading(false);
  }
};

export const sendStoreData = async ({ url, setLoading, keys = null }) => {
  if (setLoading) setLoading(true); // Ladezustand setzen, falls definiert

  let sessionStorageData = {};

  // Gesamten sessionStorage abrufen
  const fullStorage = {};
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    const value = sessionStorage.getItem(key);
    try {
      fullStorage[key] = JSON.parse(value);
    } catch {
      fullStorage[key] = value;
    }
  }

  // Falls Keys angegeben sind, nur die Werte unter "storage.state" extrahieren
  if (keys && keys.length > 0) {
    if (fullStorage.storage?.state) {
      keys.forEach((key) => {
        if (fullStorage.storage.state.hasOwnProperty(key)) {
          sessionStorageData[key] = fullStorage.storage.state[key];
        }
      });
    }
  } else {
    // Falls keine Keys angegeben sind, den gesamten Storage senden
    sessionStorageData = fullStorage;
  }

  // originale objekt zuschneiden
  const SLICEKEYS = ["position", "height", "position", "height", "width", "selected", "dragging", "positionAbsolute"]
  sliceData({ data:sessionStorageData, keys: SLICEKEYS, overwrite: true });

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sessionStorageData),
    });

    if (!response.ok) throw new Error("Fehler beim Senden der Daten");

    const result = await response.json();
    console.log("Antwort des Servers zu sendStoreData-Funktion:", result); // Consolen Logging falls benötigt
    return result; // Antwort zurückgeben, falls benötigt
  } catch (error) {
    console.error("Fehler:", error);
  } finally {
    if (setLoading) setLoading(false); // Ladezustand zurücksetzen
  }
};

/**
 * Simple HTTP GET request.
 * @param {string} url - The URL to fetch
 * @returns {Promise<any>} The JSON response
 */
export const httpGet = async (url) => {
  const response = await fetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" }
  });

  if (!response.ok) {
    throw new Error(`HTTP GET failed: ${response.status} ${response.statusText}`);
  }

  return await response.json();
};

/**
 * Simple HTTP POST request.
 * @param {string} url - The URL to post to
 * @param {object} data - The data to send
 * @returns {Promise<any>} The JSON response
 */
export const httpPost = async (url, data) => {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`HTTP POST failed: ${response.status} ${response.statusText}`);
  }

  return await response.json();
};

/**
 * Simple HTTP DELETE request.
 * @param {string} url - The URL to delete
 * @returns {Promise<any>} The JSON response
 */
export const httpDelete = async (url) => {
  const response = await fetch(url, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" }
  });

  if (!response.ok) {
    throw new Error(`HTTP DELETE failed: ${response.status} ${response.statusText}`);
  }

  return await response.json();
};