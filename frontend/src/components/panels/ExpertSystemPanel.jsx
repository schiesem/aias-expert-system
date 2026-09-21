import { useState, useEffect } from "react";
import { Button, EmptyState } from "../ui";
import RuleCatalog from "../expert/RuleCatalog";
import { useStore } from "../../store";
import { fetchData, sendStoreData } from "../../utils/httpUtils";
import { extractCategory, convertToKeyValuePair } from "../../utils/dataUtils";
import "./ExpertSystemPanel.css";

const selector = (store) => ({
  serverURL: store.serverURL,
  routes: store.routes,
  serverConfig: store.serverConfig,
  ontoData: store.ontoData,
  consistencyData: store.consistencyData,
  notesData: store.notesData,
  caseData: store.caseData,
  ruleData: store.ruleData,
  createBackendRoutes: store.createBackendRoutes,
  setServerConfig: store.setServerConfig,
  updateStore: store.updateStore,
});

export default function ExpertSystemPanel({ isOpen, onOpenChange }) {
  const store = useStore(selector);
  const [activeTab, setActiveTab] = useState("actions");
  const [loadingState, setLoadingState] = useState(false);
  const [loadingContext, setLoadingContext] = useState(null);
  const [buttonsDisabled, setButtonsDisabled] = useState(false);
  const [filterState, setFilterState] = useState(null);
  const [filterCriteria, setFilterCriteria] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [filtersExpanded, setFiltersExpanded] = useState(true);

  const tabs = [
    { id: "actions", label: "Actions" },
    { id: "reasoning", label: "Reasoning" },
    { id: "consistency", label: "Consistency" },
    { id: "notes", label: "Notes" },
    { id: "cases", label: "Cases" },
  ];

  // Initialization is now handled by App.jsx on mount
  // ExpertSystemPanel just waits for data to be available

  const handleReasoning = async () => {
    setButtonsDisabled(true);
    try {
      // First, save the current model to the instance ontology
      await sendStoreData({
        url: store.routes.STORE,
        setLoading: () => {}, // Don't disable buttons yet
        keys: ["nodes", "edges"],
      });

      // Then run reasoning on the inferred ontology
      const response = await fetch(`${store.routes.REASONING}run_reasoner`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();

      if (result.status === "success") {
        store.updateStore("ontoData", {
          message: result.message,
          payload: result.inferences,
        });
        setActiveTab("reasoning");
      } else {
        console.error("Reasoning failed:", result.message);
        alert(`Reasoning failed: ${result.message}`);
      }
    } catch (error) {
      console.error("Error during reasoning:", error);
      alert(`Error during reasoning: ${error.message}`);
    } finally {
      setButtonsDisabled(false);
    }
  };

  const handleConsistencyCheck = async () => {
    setButtonsDisabled(true);
    try {
      // First, save current model to instance ontology
      await sendStoreData({
        url: store.routes.STORE,
        setLoading: () => {},
        keys: ["nodes", "edges"],
      });

      // Then run SHACL validation on instance ontology
      const response = await fetch(`${store.routes.VALIDATION}consistency`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      const result = await response.json();

      if (result.status === "success") {
        store.updateStore("consistencyData", {
          message: result.message,
          conforms: result.conforms,
          payload: result.violations,
        });
        setActiveTab("consistency");
      } else {
        console.error("Consistency check failed:", result.message);
        alert(`Consistency check failed: ${result.message}`);
      }
    } catch (error) {
      console.error("Error during consistency check:", error);
      alert(`Error during consistency check: ${error.message}`);
    } finally {
      setButtonsDisabled(false);
    }
  };

  const handleNotesEvaluation = async () => {
    setButtonsDisabled(true);
    try {
      // First, save current model to instance ontology
      await sendStoreData({
        url: store.routes.STORE,
        setLoading: () => {},
        keys: ["nodes", "edges"],
      });

      // Then run SWRL evaluation
      const response = await fetch(`${store.routes.VALIDATION}notes`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      const result = await response.json();

      if (result.status === "success") {
        store.updateStore("notesData", {
          message: result.message,
          conforms: result.conforms,
          payload: result.violations,
        });
        setActiveTab("notes");
      } else {
        console.error("Notes evaluation failed:", result.message);
        alert(`Notes evaluation failed: ${result.message}`);
      }
    } catch (error) {
      console.error("Error during notes evaluation:", error);
      alert(`Error during notes evaluation: ${error.message}`);
    } finally {
      setButtonsDisabled(false);
    }
  };

  const handleFindSimilarCases = async () => {
    setButtonsDisabled(true);
    try {
      // Save current model first
      await sendStoreData({
        url: store.routes.STORE,
        setLoading: () => {},
        keys: ["nodes", "edges"],
      });

      // Call analyze API to get initial filter state
      const response = await fetch(`${store.routes.CASE_FILTER}analyze`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      // Check if response is OK before parsing
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend returned ${response.status}: ${errorText}`);
      }

      const result = await response.json();

      if (result.status === "success") {
        // Initialize filter state with current model data
        const analysis = result.analysis;
        const initialFilters = {
          components: {},
          architecture: analysis.architecture,
          functions: {}
        };

        // Pre-fill components with ±1 tolerance, enable only non-zero components
        Object.entries(analysis.components).forEach(([name, count]) => {
          initialFilters.components[name] = {
            current: count,
            enabled: count > 0,
            tolerance: count > 0 ? 1 : 0,
            min: Math.max(0, count - (count > 0 ? 1 : 0)),
            max: count + (count > 0 ? 1 : 0)
          };
        });

        // Pre-fill functions with ±1 tolerance, enable only non-zero functions
        Object.entries(analysis.functions).forEach(([name, count]) => {
          initialFilters.functions[name] = {
            current: count,
            enabled: count > 0,
            tolerance: count > 0 ? 1 : 0,
            min: Math.max(0, count - (count > 0 ? 1 : 0)),
            max: count + (count > 0 ? 1 : 0)
          };
        });

        setFilterState(initialFilters);
        setFilterCriteria(initialFilters);
        setSearchResults([]);
        setActiveTab("cases");
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (error) {
      console.error("Error analyzing model:", error);
      alert(`Error analyzing model: ${error.message}`);
    } finally {
      setButtonsDisabled(false);
    }
  };

  const handleApplyFilters = async () => {
    try {
      const response = await fetch(`${store.routes.CASE_FILTER}search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filterCriteria)
      });

      // Check if response is OK before parsing
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend returned ${response.status}: ${errorText}`);
      }

      const result = await response.json();

      if (result.status === "success") {
        setSearchResults(result.cases);
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (error) {
      console.error("Error searching cases:", error);
      alert(`Error searching cases: ${error.message}`);
    }
  };

  const handleResetFilters = () => {
    setFilterCriteria(filterState);
    setSearchResults([]);
  };

  const updateFilter = (category, name, field, value) => {
    setFilterCriteria(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [name]: {
          ...prev[category][name],
          [field]: value,
          // Recalculate min/max when tolerance changes
          ...(field === 'tolerance' && {
            min: Math.max(0, prev[category][name].current - value),
            max: prev[category][name].current + value
          })
        }
      }
    }));
  };

  const isEmpty = (obj) => !obj || Object.keys(obj).length === 0;

  const isDataLoaded = store.serverConfig && store.routes;

  return (
    <>
      {/* Backdrop */}
      {isOpen && isDataLoaded && (
        <div
          className="drawer-backdrop"
          onClick={() => onOpenChange(false)}
        />
      )}

      {/* Drawer */}
      {isDataLoaded && (
        <div className={`drawer ${isOpen ? 'drawer-open' : ''}`}>
          {/* Close Button - Only visible when open */}
          {isOpen && (
            <button
              onClick={() => onOpenChange(false)}
              className="drawer-close-button"
              title="Close"
            >
              ×
            </button>
          )}

          {/* Drawer Content */}
          <div className="drawer-content">
            <div className="drawer-header">
              <h2>Expert System</h2>
            </div>

            {loadingState ? (
              <div className="loading-state">
                <p>{loadingContext}</p>
              </div>
            ) : (
            <div className="expert-tabs">
            <div className="tab-list">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`tab-button ${
                    activeTab === tab.id ? "tab-active" : ""
                  }`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="tab-content">
              {activeTab === "actions" && (
                <div className="actions-panel">
                  <Button
                    variant="secondary"
                    onClick={handleReasoning}
                    disabled={buttonsDisabled}
                  >
                    Run Reasoning
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={handleConsistencyCheck}
                    disabled={buttonsDisabled}
                  >
                    Evaluate Consistency Rules
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={handleNotesEvaluation}
                    disabled={buttonsDisabled}
                  >
                    Evaluate Note Rules
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={handleFindSimilarCases}
                    disabled={buttonsDisabled}
                  >
                    Find Similar Cases
                  </Button>
                </div>
              )}

              {activeTab === "reasoning" && (
                <div className="results-panel">
                  {isEmpty(store.ontoData) || isEmpty(store.ontoData.payload) ? (
                    <>
                      <EmptyState
                        message="No reasoning results yet"
                        submessage="Click 'Run Reasoning' in Actions tab"
                      />
                      <RuleCatalog readOnly={true} ruleType="swrl" title="SWRL-Regeln" />
                    </>
                  ) : (
                    <>
                      <div className="result-message success">
                        {store.ontoData.message}
                      </div>
                      {["AddRelation", "Equivalenting", "Reparenting"].map(
                        (key) => (
                          <div key={key} className="result-section">
                            <h3 className="result-heading">{key}</h3>
                            {store.ontoData.payload[key]?.length > 0 ? (
                              <ul className="result-list">
                                {store.ontoData.payload[key].map((item, i) => (
                                  <li key={i}>{item}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="result-empty">No entries</p>
                            )}
                          </div>
                        )
                      )}
                      <div className="result-section">
                        <h3 className="result-heading">Reasoning Time</h3>
                        <p>{store.ontoData.payload.ReasonningTime} seconds</p>
                      </div>

                      <RuleCatalog readOnly={true} ruleType="swrl" title="SWRL-Regeln" />
                    </>
                  )}
                </div>
              )}

              {activeTab === "consistency" && (
                <div className="results-panel">
                  {isEmpty(store.consistencyData) || isEmpty(store.consistencyData.payload) ? (
                    <>
                      <EmptyState
                        message="No consistency check results yet"
                        submessage="Click 'Evaluate Consistency Rules' in Actions tab"
                      />
                      <RuleCatalog readOnly={true} ruleType="consistency" title="Konsistenzregeln" />
                    </>
                  ) : (
                    <>
                      <div className={`result-message ${store.consistencyData.conforms ? 'success' : 'warning'}`}>
                        {store.consistencyData.message}
                      </div>
                      {store.consistencyData.payload.length === 0 ? (
                        <div className="result-section">
                          <p className="result-empty">All consistency checks passed!</p>
                        </div>
                      ) : (
                        store.consistencyData.payload.map((violation, index) => (
                          <div key={index} className="result-section violation">
                            <h3 className="result-heading">Violation {index + 1}</h3>
                            <div className="result-row">
                              <strong>Severity:</strong> {violation.severity}
                            </div>
                            <div className="result-row">
                              <strong>Message:</strong> {violation.message}
                            </div>
                            <div className="result-row">
                              <strong>Focus Node:</strong> {violation.focusNode}
                            </div>
                            <div className="result-row">
                              <strong>Path:</strong> {violation.resultPath}
                            </div>
                          </div>
                        ))
                      )}

                      <RuleCatalog readOnly={true} ruleType="consistency" title="Konsistenzregeln" />
                    </>
                  )}
                </div>
              )}

              {activeTab === "notes" && (
                <div className="results-panel">
                  {isEmpty(store.notesData) || store.notesData.payload === undefined ? (
                    <>
                      <EmptyState
                        message="No note evaluation results yet"
                        submessage="Click 'Evaluate Note Rules' in Actions tab"
                      />
                      <RuleCatalog />
                    </>
                  ) : (
                    <>
                      <div className={`result-message ${store.notesData.conforms ? 'success' : 'info'}`}>
                        {store.notesData.message}
                      </div>
                      {store.notesData.payload.length === 0 ? (
                        <div className="result-section">
                          <p className="result-empty">No notes - all advisory checks passed!</p>
                        </div>
                      ) : (
                        store.notesData.payload.map((note, index) => (
                          <div key={index} className="result-section note">
                            <h3 className="result-heading">Note {index + 1}</h3>
                            <div className="result-row">
                              <strong>Message:</strong> {note.message}
                            </div>
                            <div className="result-row">
                              <strong>Focus Node:</strong> {note.focusNode}
                            </div>
                            {note.resultPath && note.resultPath !== "Unknown" && (
                              <div className="result-row">
                                <strong>Path:</strong> {note.resultPath}
                              </div>
                            )}
                          </div>
                        ))
                      )}

                      <RuleCatalog />
                    </>
                  )}
                </div>
              )}

              {activeTab === "cases" && (
                <div className="cases-panel">
                  {!filterCriteria ? (
                    <EmptyState message="Click 'Find Similar Cases' in Actions tab to start filtering." />
                  ) : (
                    <>
                      <div className="filter-section">
                        <h3 onClick={() => setFiltersExpanded(!filtersExpanded)} className="filter-header">
                          <span className="expand-icon">{filtersExpanded ? '−' : '+'}</span>
                          Filter Cases
                        </h3>

                        {filtersExpanded && (
                        <>
                        <div className="filter-group">
                          <h4>Components</h4>
                          {Object.entries(filterCriteria.components).map(([name, config]) => (
                            <div key={name} className="filter-row">
                              <input
                                type="checkbox"
                                checked={config.enabled}
                                onChange={(e) => updateFilter('components', name, 'enabled', e.target.checked)}
                              />
                              <label>{name}:</label>
                              <span className="current-value">Current [{config.current}]</span>
                              <span>±</span>
                              <input
                                type="number"
                                min="0"
                                value={config.tolerance}
                                onChange={(e) => updateFilter('components', name, 'tolerance', parseInt(e.target.value) || 0)}
                                disabled={!config.enabled}
                                className="tolerance-input"
                              />
                              <span className="range-display">→ Range [{config.min}-{config.max}]</span>
                            </div>
                          ))}
                        </div>

                        <div className="filter-group">
                          <h4>Architecture</h4>
                          {['edge', 'cloud', 'hybrid', 'all'].map(arch => (
                            <div key={arch} className="filter-radio">
                              <input
                                type="radio"
                                name="architecture"
                                value={arch}
                                checked={filterCriteria.architecture === arch}
                                onChange={(e) => setFilterCriteria(prev => ({...prev, architecture: e.target.value}))}
                              />
                              <label>
                                {arch.charAt(0).toUpperCase() + arch.slice(1)}
                                {filterState && filterState.architecture === arch && " (detected)"}
                              </label>
                            </div>
                          ))}
                        </div>

                        <div className="filter-group">
                          <h4>Functions</h4>
                          {Object.entries(filterCriteria.functions).map(([name, config]) => (
                            <div key={name} className="filter-row">
                              <input
                                type="checkbox"
                                checked={config.enabled}
                                onChange={(e) => updateFilter('functions', name, 'enabled', e.target.checked)}
                              />
                              <label>{name}:</label>
                              <span className="current-value">Current [{config.current}]</span>
                              <span>±</span>
                              <input
                                type="number"
                                min="0"
                                value={config.tolerance}
                                onChange={(e) => updateFilter('functions', name, 'tolerance', parseInt(e.target.value) || 0)}
                                disabled={!config.enabled}
                                className="tolerance-input"
                              />
                              <span className="range-display">→ Range [{config.min}-{config.max}]</span>
                            </div>
                          ))}
                        </div>

                        <div className="filter-actions">
                          <Button variant="secondary" onClick={handleApplyFilters}>
                            Apply Filters
                          </Button>
                          <Button variant="secondary" onClick={handleResetFilters}>
                            Reset to Current Model
                          </Button>
                          <span className="result-count">{searchResults.length} cases found</span>
                        </div>
                        </>
                        )}
                      </div>

                      <div className="results-section">
                        <h3>Search Results (sorted by best match)</h3>
                        {searchResults.length === 0 ? (
                          <EmptyState message="No matching cases. Try adjusting your filters." />
                        ) : (
                          searchResults.map((caseItem, index) => (
                            <div key={index} className="case-result">
                              <div className="case-header">
                                <strong>Case:</strong> {caseItem.case_name}
                                <span className="match-score">Match Score: {caseItem.match_score}</span>
                              </div>
                              <div className="case-matches">
                                {Object.entries(caseItem.match_details).map(([key, status]) => {
                                  if (status === "match") {
                                    const value = caseItem.components[key] || caseItem.functions[key] || caseItem.architecture;
                                    return (
                                      <span key={key} className="match-indicator match">
                                        {key}: {value} ✓
                                      </span>
                                    );
                                  } else if (status === "out_of_range" || status === "miss") {
                                    const value = caseItem.components[key] || caseItem.functions[key] || caseItem.architecture;
                                    return (
                                      <span key={key} className="match-indicator miss">
                                        {key}: {value} ✗
                                      </span>
                                    );
                                  }
                                  return null;
                                })}
                                <span className="architecture-indicator">
                                  Architecture: {caseItem.architecture} {caseItem.match_details.architecture === "match" ? "✓" : "~"}
                                </span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
          )}
        </div>
        </div>
      )}
    </>
  );
}
