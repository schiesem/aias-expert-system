/**
 * RelationRow.jsx
 *
 * Component to display a single relation with its existing annotations.
 * Allows creating new annotations and viewing/deleting existing ones.
 */

import React, { useState } from 'react';
import AnnotationInstanceForm from './AnnotationInstanceForm';
import {
  formatCardinality,
  getShortClassName,
  getRelationDescription,
  deleteAnnotation
} from '../../utils/annotationUtils';
import './RelationRow.css';

const RelationRow = ({
  relation,
  element,
  annotations,
  onAnnotationCreated,
  onAnnotationDeleted,
  parentInstance = null,  // Added: for nested annotations (Level 2+)
  availableParents = []   // Added: list of parent instances to choose from
}) => {
  const [showForm, setShowForm] = useState(false);
  const [showInstances, setShowInstances] = useState(false);
  const [deleting, setDeleting] = useState(null);

  // Find existing annotations for this relation
  // For Level 1: show annotations without a parent (parentInstance === null or undefined)
  // For Level 2+: show annotations that belong to one of the available parents
  const relatedAnnotations = annotations.filter(ann => {
    // Check if property and class match
    const propertyMatches = ann.property === relation.property;
    const classMatches = ann.class === relation.target_class;

    if (!propertyMatches || !classMatches) {
      return false;
    }

    // Level 1: no available parents, so show only root-level annotations
    if (availableParents.length === 0) {
      return !ann.parentInstance;  // Only show annotations without a parent
    }

    // Level 2+: show only annotations that belong to available parents
    const parentNames = availableParents.map(p => p.name);
    return ann.parentInstance && parentNames.includes(ann.parentInstance);
  });

  // Debug logging
  if (annotations.length > 0 && availableParents.length > 0) {
    console.log(`🔍 Level 2+ Matching for relation ${relation.property}:`, {
      relation_property: relation.property,
      relation_target_class: relation.target_class,
      available_parents: availableParents.map(p => p.name),
      all_annotations: annotations,
      matched: relatedAnnotations,
      matched_count: relatedAnnotations.length
    });
  }

  /**
   * Handle delete annotation.
   */
  const handleDelete = async (annotationId, displayName) => {
    if (!confirm(`Delete annotation "${displayName}"?`)) {
      return;
    }

    setDeleting(annotationId);

    try {
      await deleteAnnotation(element.id, relation.property, annotationId);
      onAnnotationDeleted();
    } catch (error) {
      console.error('Error deleting annotation:', error);
      alert(`Failed to delete annotation: ${error.message}`);
    } finally {
      setDeleting(null);
    }
  };

  /**
   * Handle successful annotation creation.
   */
  const handleCreated = () => {
    setShowForm(false);
    onAnnotationCreated();
  };

  // Get short class name for display
  const shortClassName = getShortClassName(relation.target_class);
  const description = getRelationDescription(relation);
  const cardinality = formatCardinality(relation.cardinality);

  return (
    <div className={`relation-row ${relation.is_required ? 'required' : 'optional'}`}>
      {/* Relation Header */}
      <div className="relation-row-header">
        <div className="relation-row-main">
          <div className="relation-row-property">
            <span className="relation-property-name">{relation.property}</span>
            {relation.is_required && (
              <span className="relation-required-badge" title="Required relation">
                *
              </span>
            )}
          </div>
          <div className="relation-row-target">
            → <span className="relation-target-class">{shortClassName}</span>
          </div>
        </div>
        <div className="relation-row-actions">
          <span className="relation-cardinality" title={cardinality}>
            {relation.cardinality}
          </span>
          {relatedAnnotations.length > 0 && (
            <button
              className="relation-btn relation-btn-toggle"
              onClick={() => setShowInstances(!showInstances)}
              title={showInstances ? 'Hide instances' : 'Show instances'}
            >
              {showInstances ? '▲' : '▼'} {relatedAnnotations.length}
            </button>
          )}
          <button
            className="relation-btn relation-btn-add"
            onClick={() => setShowForm(!showForm)}
            title="Add annotation"
          >
            {showForm ? '✕' : '+'} Add
          </button>
        </div>
      </div>

      {/* Description */}
      <div className="relation-row-description">
        {description}
      </div>

      {/* Existing Instances */}
      {showInstances && relatedAnnotations.length > 0 && (
        <div className="relation-instances">
          <div className="relation-instances-header">
            Existing Instances ({relatedAnnotations.length}):
          </div>
          <div className="relation-instances-list">
            {relatedAnnotations.map((ann, index) => (
              <div key={`${ann.id}-${index}`} className="relation-instance-item">
                <div className="instance-item-info">
                  <span className="instance-item-name">{ann.displayName}</span>
                  {ann.parentInstance && (
                    <span className="instance-item-parent" title={`Parent: ${ann.parentInstance}`}>
                      (→ {ann.parentInstance})
                    </span>
                  )}
                  {ann.hasSubAnnotations && (
                    <span className="instance-item-badge" title="Has sub-annotations">
                      🔗
                    </span>
                  )}
                  {Object.keys(ann.properties).length > 0 && (
                    <span className="instance-item-properties">
                      {Object.keys(ann.properties).length} prop{Object.keys(ann.properties).length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <button
                  className="instance-item-delete"
                  onClick={() => handleDelete(ann.id, ann.displayName)}
                  disabled={deleting === ann.id}
                  title="Delete annotation"
                >
                  {deleting === ann.id ? '⌛' : '🗑'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Creation Form */}
      {showForm && (
        <div className="relation-form-container">
          <AnnotationInstanceForm
            element={element}
            relation={relation}
            parentInstance={parentInstance}
            availableParents={availableParents}
            onSuccess={handleCreated}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}
    </div>
  );
};

export default RelationRow;
