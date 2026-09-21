import { useState, useEffect } from "react";
import { Button } from "../ui";
import "./GraphVisualizationModal.css";

export default function GraphVisualizationModal({ isOpen, onClose }) {
  const [graphType, setGraphType] = useState("instance"); // "instance" or "inferred"
  const [instanceGraphUrl, setInstanceGraphUrl] = useState(null);
  const [inferredGraphUrl, setInferredGraphUrl] = useState(null);
  const [hasInferredGraph, setHasInferredGraph] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  // Load graph URLs when modal opens
  useEffect(() => {
    if (isOpen) {
      loadGraphUrls();
    }
  }, [isOpen]);

  const loadGraphUrls = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check if graphs exist and get URLs
      const response = await fetch("http://127.0.0.1:5000/api/graph/check");
      const data = await response.json();

      if (data.success) {
        if (data.instance_exists) {
          setInstanceGraphUrl(`http://127.0.0.1:5000/api/graph/instance?t=${Date.now()}`);
        }
        if (data.inferred_exists) {
          setInferredGraphUrl(`http://127.0.0.1:5000/api/graph/inferred?t=${Date.now()}`);
          setHasInferredGraph(true);
        } else {
          setHasInferredGraph(false);
          // If currently viewing inferred but it doesn't exist, switch to instance
          if (graphType === "inferred") {
            setGraphType("instance");
          }
        }
      } else {
        setError("Failed to load graph visualizations");
      }
    } catch (err) {
      console.error("Error loading graphs:", err);
      setError("Failed to load graph visualizations");
    } finally {
      setIsLoading(false);
    }
  };

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Download graph as PDF
  const downloadGraphAsPDF = async () => {
    if (!currentGraphUrl) {
      console.error("No graph to export");
      return;
    }

    setIsExporting(true);
    setError(null);

    try {
      console.log(`📥 Requesting PDF export for ${graphType} graph...`);

      const response = await fetch(`http://127.0.0.1:5000/api/graph/export-pdf/${graphType}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate PDF');
      }

      // Get the PDF blob
      const blob = await response.blob();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ontology_graph_${graphType}.pdf`;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log(`✅ PDF downloaded: ontology_graph_${graphType}.pdf`);
    } catch (error) {
      console.error("❌ Error downloading PDF:", error);
      setError(`Failed to download PDF: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  if (!isOpen) return null;

  const currentGraphUrl = graphType === "instance" ? instanceGraphUrl : inferredGraphUrl;

  return (
    <div className="graph-modal-backdrop" onClick={onClose}>
      <div className="graph-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="graph-modal-header">
          <h2>Ontology Graph Visualization</h2>
          <button className="graph-modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Toggle */}
        <div className="graph-modal-controls">
          <div className="graph-toggle">
            <button
              className={`graph-toggle-button ${graphType === "instance" ? "active" : ""}`}
              onClick={() => setGraphType("instance")}
            >
              Instance Graph
            </button>
            <button
              className={`graph-toggle-button ${graphType === "inferred" ? "active" : ""}`}
              onClick={() => setGraphType("inferred")}
              disabled={!hasInferredGraph}
              title={!hasInferredGraph ? "No inferred graph available. Run reasoning first." : ""}
            >
              Inferred Graph
            </button>
          </div>
          <div className="graph-actions">
            <Button
              variant="secondary"
              onClick={loadGraphUrls}
              disabled={isLoading || isExporting}
              title="Reload graph visualization"
            >
              Reload
            </Button>
            <Button
              variant="primary"
              onClick={downloadGraphAsPDF}
              disabled={!currentGraphUrl || isLoading || isExporting}
              title="Download graph as PDF"
            >
              {isExporting ? "Generating PDF..." : "Download PDF"}
            </Button>
          </div>
        </div>

        {/* Graph Content */}
        <div className="graph-modal-content">
          {isLoading && (
            <div className="graph-loading">Loading graph...</div>
          )}

          {error && (
            <div className="graph-error">{error}</div>
          )}

          {!isLoading && !error && currentGraphUrl && (
            <iframe
              src={currentGraphUrl}
              className="graph-iframe"
              title={`${graphType} graph visualization`}
              frameBorder="0"
            />
          )}

          {!isLoading && !error && !currentGraphUrl && (
            <div className="graph-empty">
              No {graphType} graph available.
              {graphType === "inferred" && " Run reasoning to generate the inferred graph."}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="graph-modal-footer">
          <Button variant="secondary" onClick={onClose}>
            Dismiss
          </Button>
        </div>
      </div>
    </div>
  );
}
