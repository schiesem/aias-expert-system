import { useState, useEffect } from "react";
import { useStore } from "../../store";
import "./RuleCatalog.css";

const selector = (store) => ({
  routes: store.routes,
});

export default function RuleCatalog({
  readOnly = false,
  ruleType = "notes",
  title = "Regelkatalog"
}) {
  const store = useStore(selector);
  const [rules, setRules] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load rules catalog
  useEffect(() => {
    loadRulesCatalog();
  }, [ruleType]);

  const loadRulesCatalog = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Determine endpoint based on rule type
      let endpoint;
      if (ruleType === "consistency") {
        endpoint = `${store.routes.VALIDATION}rules/catalog/consistency`;
      } else if (ruleType === "swrl") {
        endpoint = `${store.routes.VALIDATION}rules/catalog/swrl`;
      } else {
        endpoint = `${store.routes.VALIDATION}rules/catalog`;
      }

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch rules catalog: ${response.status}`);
      }

      const result = await response.json();

      if (result.status === "success") {
        setRules(result.rules);
      } else {
        setError(result.message || "Failed to load rules catalog");
      }
    } catch (err) {
      console.error("Error loading rules catalog:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRule = async (ruleId, currentEnabled) => {
    const newEnabled = !currentEnabled;

    try {
      const response = await fetch(`${store.routes.VALIDATION}rules/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rule_id: ruleId,
          enabled: newEnabled
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to toggle rule: ${response.status}`);
      }

      const result = await response.json();

      if (result.status === "success") {
        // Update local state
        setRules(prevRules =>
          prevRules.map(rule =>
            rule.id === ruleId ? { ...rule, enabled: newEnabled } : rule
          )
        );
      } else {
        throw new Error(result.message || "Failed to toggle rule");
      }
    } catch (err) {
      console.error("Error toggling rule:", err);
      alert(`Error toggling rule: ${err.message}`);

      // Reload catalog to reset state
      loadRulesCatalog();
    }
  };

  // Group rules by type
  const groupedRules = rules.reduce((acc, rule) => {
    let category;
    if (rule.type === "shacl") {
      category = "SHACL Rules";
    } else if (rule.type === "sparql_absence") {
      category = "Absence Check Rules";
    } else if (rule.type === "sparql_complex") {
      category = "Complex Rules";
    } else if (rule.type === "sparql_regulation") {
      category = "Regulation Rules (EU AI Act)";
    } else if (rule.type === "shacl_consistency") {
      category = "Consistency Rules";
    } else if (rule.type === "swrl") {
      category = "SWRL Rules";
    } else {
      category = "Other Rules";
    }

    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(rule);
    return acc;
  }, {});

  return (
    <div className="rule-catalog">
      <h3
        className="catalog-header"
        onClick={() => setIsExpanded(!isExpanded)}
        title="Click to expand/collapse rule catalog"
      >
        <span className="expand-icon">{isExpanded ? "−" : "+"}</span>
        {title} ({rules.length} rules)
      </h3>

      {isExpanded && (
        <div className="catalog-content">
          {isLoading && (
            <div className="catalog-loading">Loading rules...</div>
          )}

          {error && (
            <div className="catalog-error">
              Error: {error}
              <button onClick={loadRulesCatalog} className="retry-button">
                Retry
              </button>
            </div>
          )}

          {!isLoading && !error && rules.length === 0 && (
            <div className="catalog-empty">No rules found</div>
          )}

          {!isLoading && !error && rules.length > 0 && (
            <div className="catalog-rules">
              {Object.entries(groupedRules).map(([category, categoryRules]) => (
                <div key={category} className="rule-category">
                  <h4 className="category-header">{category}</h4>
                  {categoryRules.map((rule) => (
                    <div key={rule.id} className="rule-item">
                      {readOnly ? (
                        // Read-only display without checkbox
                        <div className="rule-toggle">
                          <span className="rule-name">{rule.name}</span>
                        </div>
                      ) : (
                        // Toggleable display with checkbox
                        <label className="rule-toggle">
                          <input
                            type="checkbox"
                            checked={rule.enabled}
                            onChange={() => toggleRule(rule.id, rule.enabled)}
                            className="rule-checkbox"
                          />
                          <span className="rule-name">{rule.name}</span>
                        </label>
                      )}
                      {rule.message && (
                        <div className="rule-message">{rule.message}</div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}

          <div className="catalog-footer">
            <button onClick={loadRulesCatalog} className="refresh-button">
              Refresh Catalog
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
