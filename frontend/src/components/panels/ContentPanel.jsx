import { useState } from "react";
import { useStore } from "../../store";
import { Plus, Minus } from "lucide-react";

const selector = (store) => ({
  ontoData: store.ontoData,
  caseData: store.caseData,
  ruleData: store.ruleData,
});

export default function ContentPanel() {
  const { ontoData, caseData, ruleData } = useStore(selector);
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("Rules");
  const tabs = ["Reasonning", "Rules", "Cases"];

  const isEmpty = (obj) => !obj || Object.keys(obj).length === 0;

  return (
    <div className="flex">
      <div
        className={`relative flex flex-col gap-3 p-4 shadow-md rounded-md bg-white border border-stone-400 max-w-sm overflow-hidden ${
          isOpen ? "h-full" : "w-10 h-10 flex items-center justify-center"
        }`}
      >
        <button
          className="absolute top-2 right-2 p-1 bg-gray-200 rounded-full"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <Minus size={16} /> : <Plus size={16} />}
        </button>
        {isOpen && (
          <>
            <div className="flex border-b border-gray-300">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  className={`px-4 py-2 ${
                    activeTab === tab
                      ? "border-b-2 border-blue-500 font-semibold"
                      : "text-gray-500"
                  }`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto max-h-60 p-2 border border-gray-300 rounded-md flex-1 text-sm text-gray-700">
              {activeTab === "Rules" && (
                <>
                  {isEmpty(ruleData) || isEmpty(ruleData.payload) ? (
                    <p className="text-gray-500 italic">
                      Es wurden noch keine Regeln angewendet.
                    </p>
                  ) : (
                    <>
                      <p className="text-xs italic mb-2 text-green-700">
                        {ruleData.message || "Regel erfolgreich abgerufen"}
                      </p>
                      {ruleData.payload &&
                        Object.entries(ruleData.payload).map(
                          ([key, violation], index) => (
                            <div key={index} className="mb-3">
                              <h2 className="font-semibold text-blue-600">
                                Regel {index + 1}
                              </h2>

                              {/* Dynamisch alle Key-Value Paare anzeigen */}
                              {Object.entries(violation).map(
                                ([violationKey, violationValue]) => (
                                  <div key={violationKey} className="mb-1">
                                    <strong>{violationKey}:</strong>
                                    {typeof violationValue === "object"
                                      ? JSON.stringify(violationValue)
                                      : violationValue}
                                  </div>
                                )
                              )}

                              <hr className="border-t border-gray-300 my-2" />
                            </div>
                          )
                        )}
                    </>
                  )}
                </>
              )}

              {activeTab === "Reasonning" && (
                <>
                  {isEmpty(ontoData) || isEmpty(ontoData.payload) ? (
                    <p className="text-orange-500 italic">
                      Es wurde noch kein Reasonning gestartet.
                    </p>
                  ) : (
                    <>
                      <p className="text-xs italic mb-2 text-green-700">
                        {ontoData.message}
                      </p>
                      {["AddRelation", "Equivalenting", "Reparenting"].map(
                        (key) => (
                          <div key={key} className="mb-4">
                            <h2 className="font-semibold text-blue-600">
                              {key}
                            </h2>
                            {ontoData.payload[key]?.length > 0 ? (
                              <ul className="list-disc pl-5">
                                {ontoData.payload[key].map((item, i) => (
                                  <li key={i}>{item}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="italic text-gray-400">
                                Keine Einträge
                              </p>
                            )}
                          </div>
                        )
                      )}
                      <div className="mb-4">
                        <h2 className="font-semibold text-blue-600">
                          Reasonning Time
                        </h2>
                        <p>{ontoData.payload.ReasonningTime} Sekunden</p>
                      </div>
                    </>
                  )}
                </>
              )}

              {activeTab === "Cases" && (
                <>
                  {isEmpty(caseData) || isEmpty(caseData.payload) ? (
                    <p className="text-orange-500 italic">
                      Es sind keine Fälle in der Falldatenbank.
                    </p>
                  ) : (
                    <>
                      <p className="text-xs italic mb-2 text-green-700">
                        {caseData.message || "Fälle erfolgreich abgerufen"}
                      </p>
                      {caseData.payload.map((caseItem, index) => (
                        <div key={index} className="mb-3">
                          <h2 className="font-semibold text-blue-600">
                            Fall {index + 1}
                          </h2>

                          {/* Dynamisch alle Key-Value Paare anzeigen */}
                          {Object.entries(caseItem).map(([key, value]) => (
                            <div key={key} className="mb-1">
                              <strong>{key}:</strong>{" "}
                              {typeof value === "object"
                                ? JSON.stringify(value)
                                : value}
                            </div>
                          ))}

                          <hr className="border-t border-gray-300 my-2" />
                        </div>
                      ))}
                    </>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
