/**
 * RelationLevel.jsx
 *
 * Component to display relations at a specific level.
 * Shows a collapsible section with all relations for that level.
 */

import React from 'react';
import RelationRow from './RelationRow';
import { sortRelations } from '../../utils/annotationUtils';
import './RelationLevel.css';

const RelationLevel = ({
  level,
  relations,
  expanded,
  onToggle,
  element,
  annotations,
  onAnnotationCreated,
  onAnnotationDeleted
}) => {
  // Sort relations (required first, then alphabetically)
  const sortedRelations = sortRelations(relations);

  // For Level 2+, find available parent instances from Level 1 annotations
  // Parent instances are the annotations whose target_class matches the domain of Level 2 relations
  const getAvailableParents = (relation) => {
    if (level === 1) {
      return []; // Level 1 has no parents
    }

    // Find Level 1 annotations that match this relation's expected parent class
    // For now, we'll return all Level 1 annotations as potential parents
    // TODO: Filter by matching the relation's domain class
    return annotations.filter(ann => {
      // Include all annotations for now - in a full implementation,
      // we would check if ann.class matches the domain of the relation
      return true;
    });
  };

  // Count required vs optional relations
  const requiredCount = sortedRelations.filter(r => r.is_required).length;
  const optionalCount = sortedRelations.length - requiredCount;

  return (
    <div className={`relation-level ${expanded ? 'expanded' : 'collapsed'}`}>
      {/* Level Header */}
      <div className="relation-level-header" onClick={onToggle}>
        <div className="relation-level-title">
          <span className="relation-level-icon">{expanded ? '▼' : '▶'}</span>
          <span className="relation-level-label">Level {level}</span>
          <span className="relation-level-count">
            {sortedRelations.length} relation{sortedRelations.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="relation-level-info">
          {requiredCount > 0 && (
            <span className="relation-level-badge required">
              {requiredCount} required
            </span>
          )}
          {optionalCount > 0 && (
            <span className="relation-level-badge optional">
              {optionalCount} optional
            </span>
          )}
        </div>
      </div>

      {/* Level Content */}
      {expanded && (
        <div className="relation-level-content">
          {sortedRelations.length === 0 ? (
            <div className="relation-level-empty">
              No relations found at level {level}
            </div>
          ) : (
            <div className="relation-rows">
              {sortedRelations.map((relation, index) => (
                <RelationRow
                  key={`${relation.property}-${relation.target_class}-${index}`}
                  relation={relation}
                  element={element}
                  annotations={annotations}
                  onAnnotationCreated={onAnnotationCreated}
                  onAnnotationDeleted={onAnnotationDeleted}
                  availableParents={getAvailableParents(relation)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RelationLevel;
