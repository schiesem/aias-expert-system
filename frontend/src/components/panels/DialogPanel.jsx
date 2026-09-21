import { useState, useEffect } from "react";
import DialogButton from "./panelElements/DialogButton";

import { fetchData, sendStoreData } from "../../utils/httpUtils";

import { extractCategory, convertToKeyValuePair } from "../../utils/dataUtils";

import { useStore } from "../../store";

const selector = (store) => ({
  serverURL: store.serverURL,
  routes: store.routes,
  serverConfig: store.serverConfig,
  ontoConfig: store.ontoConfig,
  createBackendRoutes: store.createBackendRoutes,
  setServerConfig: store.setServerConfig,
  setOntoConfig: store.setOntoConfig,
  updateStore: store.updateStore,
});

export default function DialogPanel() {
  //const store = useStore(selector);
  const {
    serverURL,
    serverConfig,
    ontoConfig,
    routes,
    createBackendRoutes,
    setServerConfig,
    setOntoConfig,
    updateStore,
  } = useStore(selector);

  // Antworten die noch in den Store müssen
  const [loadingState, setLoadingState] = useState(false);
  const [loadingContext, setLoadingContext] = useState(null);
  const [buttonsDisabled, setButtonsDisabled] = useState(false);

  // Hochfahren des Frontends
  useEffect(() => {
    const fetchAllData = async () => {
      setLoadingState(true);
      setLoadingContext("Loading Server Configuration...");

      try {
        if (!serverConfig) {
          await fetchData({ url: serverURL, setFunction: setServerConfig });
        }
        if (!routes) {
          const newRoutes = await createBackendRoutes();
          updateStore("routes", newRoutes);
        }
      } catch (error) {
        console.error("Fehler beim Laden der Daten:", error);
      } finally {
        setLoadingState(false);
      }
    };

    fetchAllData();
  }, []);

  // Setzen der Ontologie-Config
  useEffect(() => {
    if (routes && !ontoConfig) {
      const fetchOntologyConfig = async () => {
        setLoadingState(true);
        setLoadingContext("Loading Ontology Configuration...");

        try {
          await fetchData({
            url: routes.ONTOLOGY_CONFIG,
            setFunction: setOntoConfig,
          });

          const newOntoConfig = useStore.getState().ontoConfig;

          const newFunctionsKeys = Object.keys(
            extractCategory(newOntoConfig, "Functions", "Function")
          );
          const newResourcesKeys = Object.keys(
            extractCategory(newOntoConfig, "Resources", "Resource")
          );
          const newRelationsKeys = Object.keys(
            extractCategory(newOntoConfig, "Relations", "Communication")
          );

          updateStore(
            "functionTyps",
            convertToKeyValuePair(newFunctionsKeys, "functionType")
          );
          updateStore(
            "communicationTyps",
            convertToKeyValuePair(newRelationsKeys, "communicationType")
          );
          updateStore(
            "resourceTyps",
            convertToKeyValuePair(newResourcesKeys, "resourceType")
          );
        } catch (error) {
          console.error(
            "Fehler beim Laden der Ontologie-Konfiguration:",
            error
          );
        } finally {
          setLoadingState(false);
        }
      };

      fetchOntologyConfig();
    }
  }, [routes, ontoConfig]);

  // Zeige das Lade-Feedback an, wenn Daten noch geladen werden
  if (loadingState) {
    return (
      <div className="flex max-h-60">
        <div className="flex flex-col gap-3 p-4 shadow-md rounded-md bg-white border border-stone-400 max-w-sm">
          <h1 className="text-lg font-semibold">Dialog Panel</h1>
          <p>{loadingContext}</p>
        </div>
      </div>
    );
  }

  // Zeige das Panel erst, wenn alle benötigten Daten geladen sind
  if (!serverConfig || !routes || !ontoConfig) {
    return null; // Verhindert das Rendern, bis alles bereit ist
  }

  return (
    <div className="flex max-h-60">
      <div className="flex flex-col gap-3 p-4 shadow-md rounded-md bg-white border border-stone-400 max-w-sm">
        <h1 className="text-lg font-semibold">Dialog Panel</h1>
        <DialogButton
          label="Reasonning"
          onClick={async () => {
            setButtonsDisabled(true);
            try {
              const result = await sendStoreData({
                url: routes.STORE,
                setLoading: setButtonsDisabled,
                keys: ["nodes", "edges"],
              });

              updateStore("ontoData", result); // Speichert das Backend-Ergebnis im Zustand
              console.log("Ontologie-Daten im Store gespeichert");
            } catch (error) {
              console.error("Fehler beim Senden des Modells:", error);
            } finally {
              setButtonsDisabled(false);
            }
          }}
          isDisabled={buttonsDisabled}
        />
        <DialogButton
          label="Rule Evaluation"
          onClick={async () => {
            setButtonsDisabled(true);
            try {
              const result = await sendStoreData({
                url: routes.RULE_BASE,
                setLoading: setButtonsDisabled,
                keys: ["nodes", "edges"],
              });

              updateStore("ruleData", result); // Ergebnis in den Store speichern
              console.log("Regelauswertung im Store gespeichert");
            } catch (error) {
              console.error("Fehler bei der Regelauswertung:", error);
            } finally {
              setButtonsDisabled(false);
            }
          }}
          isDisabled={buttonsDisabled}
        />
        <DialogButton
          label="Case Evaluation"
          onClick={async () => {
            setButtonsDisabled(true);
            try {
              const result = await sendStoreData({
                url: routes.CASE_BASE,
                setLoading: setButtonsDisabled,
                keys: ["nodes", "edges"],
              });

              // Zugriff auf die Antwort und Speicherung im Zustand
              updateStore("caseData", result);
              console.log("Fallauswertung im Store gespeichert");
            } catch (error) {
              console.error("Fehler bei der Fallauswertung:", error);
            } finally {
              setButtonsDisabled(false);
            }
          }}
          isDisabled={buttonsDisabled}
        />
      </div>
    </div>
  );
}