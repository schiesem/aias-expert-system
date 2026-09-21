import { useState } from "react";
import "./NavigationBar.css";

export default function NavigationBar({
  onOpenWorldSelector,
  onOpenExpertSystem,
  onOpenGraphVisualization,
  onSaveModel,
  isExpertSystemReady
}) {
  return (
    <div className="navigation-bar">
      <div className="navigation-content">
        <button
          className="nav-button"
          onClick={onOpenWorldSelector}
          title="Open World Selector"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
          <span>World Selector</span>
        </button>

        <button
          className="nav-button"
          onClick={onSaveModel}
          title="Save Model to Ontology"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          <span>Save</span>
        </button>

        <button
          className="nav-button"
          onClick={onOpenExpertSystem}
          disabled={!isExpertSystemReady}
          title={isExpertSystemReady ? "Open Expert System" : "Loading..."}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
          <span>Expert System</span>
        </button>

        <button
          className="nav-button"
          onClick={onOpenGraphVisualization}
          title="View Ontology Graph Visualization"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <circle cx="6" cy="6" r="2" />
            <circle cx="18" cy="6" r="2" />
            <circle cx="6" cy="18" r="2" />
            <circle cx="18" cy="18" r="2" />
            <line x1="8" y1="7" x2="10" y2="11" />
            <line x1="16" y1="7" x2="14" y2="11" />
            <line x1="8" y1="17" x2="10" y2="13" />
            <line x1="16" y1="17" x2="14" y2="13" />
          </svg>
          <span>Graph Visualization</span>
        </button>
      </div>
    </div>
  );
}
