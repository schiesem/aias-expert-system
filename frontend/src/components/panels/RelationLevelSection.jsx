/**
 * RelationLevelSection.jsx
 *
 * Displays all relations for a single level (1, 2, 3, etc.) in a flat structure.
 * For Level 2+, allows parent selection before creating/linking annotations.
 *
 * Replaces the nested AnnotationRelationRow behavior with a simpler flat display.
 */

import React, { useState } from 'react';
import RelationRowFlat from './RelationRowFlat';
import './RelationLevelSection.css';

const RelationLevelSection = ({
  level,
  relations,
  element,
  allAnnotations,
  parentLevelAnnotations = [],  // Available parent instances (for Level 2+)
  onAnnotationCreated,
  onAnnotationDeleted
}) => {
  // State to track selected parent per relation (for Level 2+)
  const [selectedParents, setSelectedParents] = useState({});

  /**
   * Handle parent selection change for a specific relation.
   */
  const handleParentChange = (relationKey, parentInstance) => {
    setSelectedParents(prev => ({
      ...prev,
      [relationKey]: parentInstance
    }));
  };

  /**
   * Get unique key for a relation.
   */
  const getRelationKey = (relation) => {
    return `${relation.property}-${relation.target_class}`;
  };

  return (
    <div className="level-section">
      {/* Level Header */}
      <div className="level-section-header">
        <h3 className="level-section-title">
          Level {level} Relations
        </h3>
        <span className="level-section-count">
          {relations.length} relation{relations.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Relation List */}
      <div className="level-section-content">
        {relations.length === 0 ? (
          <div className="level-section-empty">
            No relations found for Level {level}.
          </div>
        ) : (
          relations.map((relation, index) => {
            const relationKey = getRelationKey(relation);
            const selectedParent = selectedParents[relationKey] || null;

            return (
              <RelationRowFlat
                key={`${relationKey}-${index}`}
                relation={relation}
                element={element}
                level={level}
                selectedParent={selectedParent}
                onParentChange={(parent) => handleParentChange(relationKey, parent)}
                parentOptions={parentLevelAnnotations}
                allAnnotations={allAnnotations}
                onAnnotationCreated={onAnnotationCreated}
                onAnnotationDeleted={onAnnotationDeleted}
              />
            );
          })
        )}
      </div>
    </div>
  );
};

export default RelationLevelSection;
