/**
 * AnnotationInstanceCard.jsx
 *
 * Displays a single annotation instance with:
 * - Display name, class, properties
 * - Delete button
 * - Expand/collapse button for sub-relations
 * - Nested AnnotationRelationRow for Level N+1 relations
 *
 * This component creates the nested tree structure for annotations.
 */

import React, { useState, useEffect } from 'react';
import { deleteAnnotation, fetchRelations } from '../../utils/annotationUtils';
import './AnnotationInstanceCard.css';

const AnnotationInstanceCard = ({
  annotation,
  element,
  currentLevel,
  maxLevel,
  allAnnotations,
  allRelations = {},
  onAnnotationDeleted,
  onAnnotationCreated
}) => {
  const [expanded, setExpanded] = useState(false);
  const [subRelations, setSubRelations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Load sub-relations when expanded
  useEffect(() => {
    if (expanded && currentLevel < maxLevel) {
      loadSubRelations();
    }
  }, [expanded, currentLevel, maxLevel]);

  /**
   * Load relations for the next level (based on this instance's class).
   */
  const loadSubRelations = async () => {
    setLoading(true);
    try {
      // Fetch relations for this annotation's class at the next level
      const relationsData = await fetchRelations(annotation.class, 1, currentLevel + 1);
      console.log(`📋 Loaded ${relationsData.length} sub-relations for ${annotation.displayName} (Level ${currentLevel + 1})`);
      setSubRelations(relationsData);
    } catch (error) {
      console.error('Error loading sub-relations:', error);
      setSubRelations([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle delete button click.
   */
  const handleDelete = async () => {
    if (!confirm(`Delete annotation "${annotation.displayName}"?`)) {
      return;
    }

    setDeleting(true);
    try {
      // Get direction from annotation (default to outgoing)
      const direction = annotation.direction || 'outgoing';
      await deleteAnnotation(element.id, annotation.property, annotation.id, direction);
      onAnnotationDeleted();
    } catch (error) {
      console.error('Error deleting annotation:', error);
      alert(`Failed to delete: ${error.message}`);
    } finally {
      setDeleting(false);
    }
  };

  // Filter sub-annotations for this instance (children of this annotation)
  const subAnnotations = allAnnotations.filter(ann => ann.parentInstance === annotation.id);

  // Check if we can expand (haven't reached max level and have sub-relations)
  const canExpand = currentLevel < maxLevel;
  const hasSubAnnotations = subAnnotations.length > 0 || subRelations.length > 0;

  return (
    <div className="annotation-instance-card" style={{ marginLeft: `${currentLevel * 20}px` }}>
      {/* Instance Header */}
      <div className="instance-card-header">
        <div className="instance-card-info">
          {canExpand && hasSubAnnotations && (
            <button
              className="instance-expand-btn"
              onClick={() => setExpanded(!expanded)}
              title={expanded ? 'Collapse sub-relations' : 'Expand sub-relations'}
            >
              {expanded ? '▼' : '▶'}
            </button>
          )}
          <span className="instance-name">{annotation.displayName}</span>
          <span className="instance-class">({annotation.shortClass})</span>
          {Object.keys(annotation.properties).length > 0 && (
            <span className="instance-props-badge" title={JSON.stringify(annotation.properties, null, 2)}>
              {Object.keys(annotation.properties).length} prop{Object.keys(annotation.properties).length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <button
          className="instance-delete-btn"
          onClick={handleDelete}
          disabled={deleting}
          title="Delete annotation"
        >
          {deleting ? '⌛' : '🗑'}
        </button>
      </div>

      {/* Sub-relations (Level N+1) */}
      {expanded && canExpand && (
        <div className="instance-card-subrelations">
          {loading && <div className="instance-loading">Loading sub-relations...</div>}

          {!loading && subRelations.length === 0 && (
            <div className="instance-empty">No sub-relations available</div>
          )}

          {!loading && subRelations.length > 0 && (
            <div className="instance-subrelation-list">
              <div className="subrelation-header">
                Level {currentLevel + 1} Relations for {annotation.displayName}:
              </div>
              {subRelations.map((relation, index) => (
                <AnnotationRelationRow
                  key={`${relation.property}-${relation.target_class}-${index}`}
                  relation={relation}
                  element={element}
                  parentInstance={annotation}  // This instance is the parent for Level N+1
                  currentLevel={currentLevel + 1}
                  maxLevel={maxLevel}
                  allAnnotations={allAnnotations}
                  allRelations={allRelations}
                  onAnnotationCreated={onAnnotationCreated}
                  onAnnotationDeleted={onAnnotationDeleted}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Import AnnotationRelationRow here to avoid circular dependency issues
// This is imported after the component definition
import AnnotationRelationRow from './AnnotationRelationRow';

export default AnnotationInstanceCard;
