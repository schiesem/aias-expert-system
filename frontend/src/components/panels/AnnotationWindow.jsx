/**
 * AnnotationWindow.jsx
 *
 * Main annotation interface modal window.
 * Opens on double-click of nodes/edges to manage semantic annotations.
 * Displays relations at multiple levels and allows creating/viewing annotations.
 */

import React, { useState, useEffect } from 'react';
import {
  fetchRelations,
  fetchAnnotations,
  groupRelationsByLevel,
  formatAnnotationsForDisplay,
  countAnnotationsRecursive
} from '../../utils/annotationUtils';
import { useStore } from '../../store';
import RelationLevelSection from './RelationLevelSection';
import LoadingSpinner from './LoadingSpinner';
import './AnnotationWindow.css';

const AnnotationWindow = ({ element, onClose }) => {
  // Get refresh function from store
  const refreshAnnotationCounts = useStore((state) => state.refreshAnnotationCounts);
  // State
  const [relations, setRelations] = useState({});
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [maxLevel, setMaxLevel] = useState(1);  // Default to Level 1 for faster loading
  const [annotationCount, setAnnotationCount] = useState(0);

  // Load relations and annotations on mount and when element changes
  useEffect(() => {
    if (element && element.class) {
      loadData();
    }
  }, [element]);

  /**
   * Load relations and annotations from backend.
   */
  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch relations for the element's class
      const relationsData = await fetchRelations(element.class, maxLevel);
      console.log('📊 AnnotationWindow - Raw relations data:', relationsData);
      const groupedRelations = groupRelationsByLevel(relationsData);
      console.log('📊 AnnotationWindow - Grouped relations:', groupedRelations);
      setRelations(groupedRelations);

      // Fetch existing annotations for this element
      const annotationsData = await fetchAnnotations(element.id, maxLevel);
      console.log('📦 Raw annotations data:', annotationsData);

      const formattedAnnotations = formatAnnotationsForDisplay(annotationsData);
      console.log('📦 Formatted annotations:', formattedAnnotations);
      setAnnotations(formattedAnnotations);

      // Count annotations
      const count = countAnnotationsRecursive(annotationsData);
      setAnnotationCount(count);

    } catch (err) {
      console.error('Error loading annotation data:', err);
      setError(err.message || 'Failed to load annotation data');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Refresh data from backend.
   */
  const handleRefresh = () => {
    loadData();
  };

  /**
   * Handle successful annotation creation.
   * Refresh data to show the new annotation.
   */
  const handleAnnotationCreated = () => {
    loadData();
    // Trigger refresh of annotation counts in all nodes
    refreshAnnotationCounts();
  };

  /**
   * Handle annotation deletion.
   * Refresh data to remove the deleted annotation.
   */
  const handleAnnotationDeleted = () => {
    loadData();
    // Trigger refresh of annotation counts in all nodes
    refreshAnnotationCounts();
  };

  /**
   * Get annotations at specific level (for parent dropdowns).
   */
  const getLevel1Annotations = () => {
    return annotations.filter(ann => !ann.parentInstance);
  };

  const getLevel2Annotations = () => {
    const level1Ids = getLevel1Annotations().map(a => a.id);
    return annotations.filter(ann => level1Ids.includes(ann.parentInstance));
  };

  const getLevel3Annotations = () => {
    const level2Ids = getLevel2Annotations().map(a => a.id);
    return annotations.filter(ann => level2Ids.includes(ann.parentInstance));
  };

  const getLevel4Annotations = () => {
    const level3Ids = getLevel3Annotations().map(a => a.id);
    return annotations.filter(ann => level3Ids.includes(ann.parentInstance));
  };

  // Don't render if no element
  if (!element) {
    return null;
  }

  return (
    <div className="annotation-window-overlay" onClick={onClose}>
      <div className="annotation-window" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="annotation-window-header">
          <div className="annotation-window-title">
            <h2>Semantic Annotations</h2>
            <span className="annotation-count-badge">{annotationCount}</span>
          </div>
          <button
            className="annotation-window-close"
            onClick={onClose}
            title="Close"
          >
            ×
          </button>
        </div>

        {/* Element Info */}
        <div className="annotation-element-info">
          <div className="element-info-row">
            <span className="element-info-label">Element ID:</span>
            <span className="element-info-value">{element.id}</span>
          </div>
          <div className="element-info-row">
            <span className="element-info-label">Class:</span>
            <span className="element-info-value">{element.class}</span>
          </div>
          {element.label && (
            <div className="element-info-row">
              <span className="element-info-label">Label:</span>
              <span className="element-info-value">{element.label}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="annotation-actions">
          <button
            className="annotation-btn annotation-btn-refresh"
            onClick={handleRefresh}
            disabled={loading}
          >
            🔄 Refresh
          </button>
          <div className="annotation-level-selector">
            <label htmlFor="max-level">Max Level:</label>
            <select
              id="max-level"
              value={maxLevel}
              onChange={(e) => {
                setMaxLevel(parseInt(e.target.value));
                // Will trigger useEffect to reload data
              }}
            >
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
            </select>
          </div>
        </div>

        {/* Content */}
        <div className="annotation-window-content">
          {loading && <LoadingSpinner message="Loading relations and annotations..." />}

          {error && (
            <div className="annotation-error">
              <span className="error-icon">⚠</span>
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && Object.keys(relations).length === 0 && (
            <div className="annotation-empty">
              <p>No relations found for class <strong>{element.class}</strong>.</p>
              <p>Make sure the ontology is loaded correctly.</p>
            </div>
          )}

          {!loading && !error && Object.keys(relations).length > 0 && (
            <div className="annotation-relations-container">
              {/* Render Level 1 */}
              {relations['1'] && relations['1'].length > 0 && (
                <RelationLevelSection
                  level={1}
                  relations={relations['1']}
                  element={element}
                  allAnnotations={annotations}
                  parentLevelAnnotations={[]}  // No parents for Level 1
                  onAnnotationCreated={handleAnnotationCreated}
                  onAnnotationDeleted={handleAnnotationDeleted}
                />
              )}

              {/* Render Level 2 */}
              {relations['2'] && relations['2'].length > 0 && maxLevel >= 2 && (
                <RelationLevelSection
                  level={2}
                  relations={relations['2']}
                  element={element}
                  allAnnotations={annotations}
                  parentLevelAnnotations={getLevel1Annotations()}  // Level 1 instances
                  onAnnotationCreated={handleAnnotationCreated}
                  onAnnotationDeleted={handleAnnotationDeleted}
                />
              )}

              {/* Render Level 3 */}
              {relations['3'] && relations['3'].length > 0 && maxLevel >= 3 && (
                <RelationLevelSection
                  level={3}
                  relations={relations['3']}
                  element={element}
                  allAnnotations={annotations}
                  parentLevelAnnotations={getLevel2Annotations()}  // Level 2 instances
                  onAnnotationCreated={handleAnnotationCreated}
                  onAnnotationDeleted={handleAnnotationDeleted}
                />
              )}

              {/* Render Level 4 */}
              {relations['4'] && relations['4'].length > 0 && maxLevel >= 4 && (
                <RelationLevelSection
                  level={4}
                  relations={relations['4']}
                  element={element}
                  allAnnotations={annotations}
                  parentLevelAnnotations={getLevel3Annotations()}
                  onAnnotationCreated={handleAnnotationCreated}
                  onAnnotationDeleted={handleAnnotationDeleted}
                />
              )}

              {/* Render Level 5 */}
              {relations['5'] && relations['5'].length > 0 && maxLevel >= 5 && (
                <RelationLevelSection
                  level={5}
                  relations={relations['5']}
                  element={element}
                  allAnnotations={annotations}
                  parentLevelAnnotations={getLevel4Annotations()}
                  onAnnotationCreated={handleAnnotationCreated}
                  onAnnotationDeleted={handleAnnotationDeleted}
                />
              )}

              {Object.keys(relations).length === 0 && (
                <div className="annotation-empty">No relations found.</div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="annotation-window-footer">
          <p className="annotation-hint">
            💡 Click on a relation to create an annotation. Expand levels to discover more relations.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AnnotationWindow;
