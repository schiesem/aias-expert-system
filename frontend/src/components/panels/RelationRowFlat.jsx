/**
 * RelationRowFlat.jsx
 *
 * Displays a single relation with parent/target dropdowns in a flat structure.
 * Simplified from AnnotationRelationRow - no nested rendering.
 *
 * Key Features:
 * - Relation header (property → class, cardinality)
 * - Parent dropdown (Level 2+ only)
 * - Target dropdown ("Use Existing")
 * - "+ Add New" button
 * - Instance list (filtered by parent if Level 2+)
 */

import React, { useState } from 'react';
import AnnotationInstanceForm from './AnnotationInstanceForm';
import {
  formatCardinality,
  getShortClassName,
  getRelationDescription,
  fetchInstancesByClass,
  linkExistingAnnotation,
  deleteAnnotation
} from '../../utils/annotationUtils';
import './RelationRowFlat.css';

const RelationRowFlat = ({
  relation,
  element,
  level,
  selectedParent,        // For Level 2+: chosen parent instance
  onParentChange,        // Callback to change parent
  parentOptions = [],    // Available parent instances
  allAnnotations,
  onAnnotationCreated,
  onAnnotationDeleted
}) => {
  const [showForm, setShowForm] = useState(false);
  const [showUseDropdown, setShowUseDropdown] = useState(false);
  const [showInstances, setShowInstances] = useState(true);  // Expanded by default
  const [availableInstances, setAvailableInstances] = useState([]);
  const [loadingInstances, setLoadingInstances] = useState(false);
  const [linking, setLinking] = useState(false);
  const [deleting, setDeleting] = useState(null);  // Track which instance is being deleted

  // Format relation info
  const shortClassName = getShortClassName(relation.target_class);
  const description = getRelationDescription(relation);
  const cardinalityInfo = formatCardinality(relation.cardinality);
  const isIncoming = relation.direction === 'incoming';

  // Get the "current" class name for display
  // Level 1: Use the element's class (e.g., Inference)
  // Level 2+: Use the parent_class from the relation (e.g., Prediction)
  const currentClassName = level > 1 && relation.parent_class
    ? getShortClassName(relation.parent_class)
    : getShortClassName(element.class);

  /**
   * Filter annotations for this relation based on level.
   */
  const relatedAnnotations = allAnnotations.filter(ann => {
    const matchesRelation = ann.property === relation.property &&
                           ann.class === relation.target_class;

    if (level === 1) {
      // Level 1: Show only root-level annotations (no parent)
      return matchesRelation && !ann.parentInstance;
    } else {
      // Level 2+: Show only annotations matching selected parent
      if (!selectedParent) return false;  // No parent selected yet
      return matchesRelation && ann.parentInstance === selectedParent.id;
    }
  });

  // Calculate current count vs. cardinality
  const currentCount = relatedAnnotations.length;
  const cardinalityParts = relation.cardinality.split('..');
  const maxCount = cardinalityParts[1] || '*';
  const cardinalityDisplay = `(${currentCount}/${maxCount})`;

  /**
   * Load available instances for "Use Existing" dropdown.
   */
  const loadAvailableInstances = async () => {
    setLoadingInstances(true);
    try {
      const instances = await fetchInstancesByClass(relation.target_class);

      // Filter out already linked instances
      const linkedIds = relatedAnnotations.map(ann => ann.id);
      const available = instances.filter(inst => !linkedIds.includes(inst.id));

      console.log(`📋 ${available.length} available instances to link (${linkedIds.length} already linked)`);
      setAvailableInstances(available);
    } catch (error) {
      console.error('Error loading available instances:', error);
      setAvailableInstances([]);
    } finally {
      setLoadingInstances(false);
    }
  };

  /**
   * Handle "Use Existing" button click.
   */
  const handleUseClick = async () => {
    if (!showUseDropdown) {
      await loadAvailableInstances();
    }
    setShowUseDropdown(!showUseDropdown);
  };

  /**
   * Handle selection of existing instance from dropdown.
   */
  const handleSelectInstance = async (instanceId) => {
    setLinking(true);
    try {
      await linkExistingAnnotation(
        element.id,
        relation.property,
        instanceId,
        level > 1 ? selectedParent?.id : null,
        relation.direction || 'outgoing'  // Pass direction for correct property assignment
      );
      setShowUseDropdown(false);
      onAnnotationCreated();  // Refresh data
    } catch (error) {
      console.error('Error linking instance:', error);
      alert(`Failed to link instance: ${error.message}`);
    } finally {
      setLinking(false);
    }
  };

  /**
   * Handle delete button click.
   */
  const handleDelete = async (annotation) => {
    if (!confirm(`Delete annotation "${annotation.displayName}"?`)) {
      return;
    }

    setDeleting(annotation.id);
    try {
      // Pass direction for correct link removal
      const direction = annotation.direction || relation.direction || 'outgoing';
      await deleteAnnotation(element.id, annotation.property, annotation.id, direction);
      onAnnotationDeleted();
    } catch (error) {
      console.error('Error deleting annotation:', error);
      alert(`Failed to delete: ${error.message}`);
    } finally {
      setDeleting(null);
    }
  };

  /**
   * Handle parent selection change.
   */
  const handleParentSelectionChange = (e) => {
    const parentId = e.target.value;
    if (!parentId) {
      onParentChange(null);
      return;
    }

    const parent = parentOptions.find(p => p.id === parentId);
    onParentChange(parent);
  };

  // Check if parent is required but not selected (Level 2+)
  const parentRequired = level > 1;
  const parentSelected = level === 1 || !!selectedParent;
  const canAddOrUse = parentSelected;  // Can only add/use if parent selected (or Level 1)

  return (
    <div className={`relation-row-flat ${relation.is_required ? 'required' : 'optional'}`}>
      {/* Relation Header */}
      <div className="relation-row-header">
        <div className="relation-row-info">
          {/* For outgoing: Inference → creates → Prediction */}
          {/* For incoming: MLModel → executes → Inference ⇐ */}
          {isIncoming ? (
            <>
              <span className="relation-target-class">{shortClassName}</span>
              <span className="relation-arrow">→</span>
              <span className="relation-property">{relation.property}</span>
              {relation.is_required && <span className="relation-required-badge" title="Required relation">*</span>}
              <span className="relation-arrow">→</span>
              <span className="relation-element-class">{currentClassName}</span>
            </>
          ) : (
            <>
              <span className="relation-element-class">{currentClassName}</span>
              <span className="relation-arrow">→</span>
              <span className="relation-property">{relation.property}</span>
              {relation.is_required && <span className="relation-required-badge" title="Required relation">*</span>}
              <span className="relation-arrow">→</span>
              <span className="relation-target-class">{shortClassName}</span>
            </>
          )}
        </div>

        <div className="relation-row-actions">
          <span className="relation-cardinality" title={cardinalityInfo}>
            {cardinalityDisplay}
          </span>

          {relatedAnnotations.length > 0 && (
            <button
              className="relation-toggle-btn"
              onClick={() => setShowInstances(!showInstances)}
              title={showInstances ? 'Hide instances' : 'Show instances'}
            >
              {showInstances ? '▲' : '▼'} {currentCount}
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {description && (
        <div className="relation-description">{description}</div>
      )}

      {/* Parent Selector (Level 2+ only) */}
      {parentRequired && (
        <div className="parent-selector">
          <label htmlFor={`parent-${relation.property}`}>
            Parent {relation.parent_class}:
          </label>
          <select
            id={`parent-${relation.property}`}
            value={selectedParent?.id || ''}
            onChange={handleParentSelectionChange}
            className="parent-selector-dropdown"
          >
            <option value="">-- Select parent {relation.parent_class} --</option>
            {parentOptions.map(parent => (
              <option key={parent.id} value={parent.id}>
                {parent.displayName} ({parent.shortClass})
              </option>
            ))}
          </select>
          {parentOptions.length === 0 && (
            <div className="parent-selector-empty">
              No {relation.parent_class} instances available. Create a Level {level - 1} instance first.
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {canAddOrUse && (
        <div className="relation-row-buttons">
          <button
            className="relation-add-btn"
            onClick={() => setShowForm(!showForm)}
            disabled={relation.is_graphical}
            title={relation.is_graphical
              ? `Cannot create new ${shortClassName} instances here. ${shortClassName} must be created as graphical nodes in the canvas.`
              : "Create new annotation"}
          >
            {showForm ? '✕ Cancel' : '+ Add New'}
          </button>

          <button
            className="relation-use-btn"
            onClick={handleUseClick}
            disabled={loadingInstances || linking}
            title="Link existing annotation"
          >
            ↔ Use Existing {showUseDropdown ? '▲' : '▼'}
          </button>
        </div>
      )}

      {/* Message if parent not selected */}
      {!canAddOrUse && (
        <div className="relation-row-message">
          Select a parent {relation.parent_class} to view and manage {shortClassName} instances.
        </div>
      )}

      {/* Use Existing Dropdown */}
      {showUseDropdown && canAddOrUse && (
        <div className="relation-use-dropdown">
          {loadingInstances && <div className="dropdown-loading">Loading instances...</div>}

          {!loadingInstances && availableInstances.length === 0 && (
            <div className="dropdown-empty">No available instances to link</div>
          )}

          {!loadingInstances && availableInstances.length > 0 && (
            <div className="dropdown-list">
              <div className="dropdown-header">
                Select an existing {shortClassName} to link:
              </div>
              {availableInstances.map(inst => (
                <button
                  key={inst.id}
                  className="dropdown-item"
                  onClick={() => handleSelectInstance(inst.id)}
                  disabled={linking}
                >
                  <span className="dropdown-item-name">{inst.display_name}</span>
                  <span className="dropdown-item-id">({inst.id})</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Creation Form */}
      {showForm && canAddOrUse && (
        <div className="relation-form">
          <AnnotationInstanceForm
            element={element}
            relation={relation}
            parentInstance={level > 1 ? selectedParent : null}
            onSuccess={() => {
              setShowForm(false);
              onAnnotationCreated();
            }}
            onCancel={() => {
              setShowForm(false);
            }}
          />
        </div>
      )}

      {/* Existing Instances */}
      {showInstances && relatedAnnotations.length > 0 && canAddOrUse && (
        <div className="relation-instances">
          <div className="instances-header">
            {level === 1
              ? `Existing ${shortClassName} instances:`
              : `Existing ${shortClassName} instances linked to ${selectedParent?.display_name || 'selected parent'}:`
            }
          </div>
          {relatedAnnotations.map((ann, index) => (
            <div key={`${ann.id}-${index}`} className="instance-item">
              <div className="instance-item-info">
                <span className="instance-name">{ann.displayName}</span>
                <span className="instance-class">({ann.shortClass})</span>
                {Object.keys(ann.properties).length > 0 && (
                  <span className="instance-props-badge" title={JSON.stringify(ann.properties, null, 2)}>
                    {Object.keys(ann.properties).length} prop{Object.keys(ann.properties).length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <button
                className="instance-delete-btn"
                onClick={() => handleDelete(ann)}
                disabled={deleting === ann.id}
                title="Delete annotation"
              >
                {deleting === ann.id ? '⌛' : '🗑'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RelationRowFlat;
