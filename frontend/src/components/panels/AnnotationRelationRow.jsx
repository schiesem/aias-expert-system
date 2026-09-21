/**
 * AnnotationRelationRow.jsx
 *
 * Displays a single relation (property → class) with:
 * - Relation header (property name, target class, cardinality)
 * - [+ Add] and [↔ Use] buttons
 * - List of existing annotation instances (each with AnnotationInstanceCard)
 * - Creation form
 *
 * This component replaces both RelationRow and RelationLevel from the old architecture.
 */

import React, { useState, useEffect } from 'react';
import AnnotationInstanceCard from './AnnotationInstanceCard';
import AnnotationInstanceForm from './AnnotationInstanceForm';
import {
  formatCardinality,
  getShortClassName,
  getRelationDescription,
  fetchInstancesByClass,
  linkExistingAnnotation
} from '../../utils/annotationUtils';
import './AnnotationRelationRow.css';

const AnnotationRelationRow = ({
  relation,
  element,
  parentInstance = null,  // For Level 2+: parent annotation instance
  currentLevel,
  maxLevel,
  allAnnotations,
  allRelations = {},  // All relations grouped by level (from AnnotationWindow)
  onAnnotationCreated,
  onAnnotationDeleted
}) => {
  const [showForm, setShowForm] = useState(false);
  const [showUseDropdown, setShowUseDropdown] = useState(false);
  const [showInstances, setShowInstances] = useState(true);  // Expanded by default
  const [showNestedRelations, setShowNestedRelations] = useState(true);  // Show nested relations by default
  const [showParentSelector, setShowParentSelector] = useState(false);  // For Level 2+ parent selection
  const [selectedParentForCreation, setSelectedParentForCreation] = useState(null);
  const [availableParents, setAvailableParents] = useState([]);
  const [availableInstances, setAvailableInstances] = useState([]);
  const [loadingInstances, setLoadingInstances] = useState(false);
  const [loadingParents, setLoadingParents] = useState(false);
  const [linking, setLinking] = useState(false);

  // Filter annotations for this relation
  const relatedAnnotations = allAnnotations.filter(ann => {
    const propertyMatches = ann.property === relation.property;
    const classMatches = ann.class === relation.target_class;

    if (!propertyMatches || !classMatches) {
      return false;
    }

    // Check parent matching
    if (parentInstance) {
      // Level 2+: Show only annotations that belong to THIS parent
      return ann.parentInstance === parentInstance.id;
    } else {
      // Level 1: Show only root-level annotations (no parent)
      return !ann.parentInstance;
    }
  });

  // Calculate current count vs. cardinality
  const currentCount = relatedAnnotations.length;
  const cardinalityParts = relation.cardinality.split('..');
  const maxCount = cardinalityParts[1] || '*';
  const cardinalityDisplay = `(${currentCount}/${maxCount})`;
  const cardinalityInfo = formatCardinality(relation.cardinality);
  const shortClassName = getShortClassName(relation.target_class);
  const description = getRelationDescription(relation);

  // Get the "current" class name for display
  // Level 1: Use the element's class (e.g., Inference)
  // Level 2+: Use the parent_class from the relation (e.g., Prediction)
  const currentClassName = currentLevel > 1 && relation.parent_class
    ? getShortClassName(relation.parent_class)
    : getShortClassName(element.class);

  // Get next level relations if within MaxLevel
  const nextLevel = currentLevel + 1;
  const hasNextLevel = nextLevel <= maxLevel;

  // Debug: Log the filtering process
  console.log(`\n🔍 AnnotationRelationRow - Level ${currentLevel}`);
  console.log(`  Relation: ${relation.property} → ${relation.target_class}`);
  console.log(`  Direction: ${relation.direction || 'MISSING'}`);
  console.log(`  Full relation object:`, relation);
  console.log(`  hasNextLevel: ${hasNextLevel}, nextLevel: ${nextLevel}, maxLevel: ${maxLevel}`);
  console.log(`  allRelations object:`, allRelations);
  console.log(`  allRelations keys:`, Object.keys(allRelations));
  console.log(`  allRelations['${nextLevel}']:`, allRelations[nextLevel.toString()]);

  const nextLevelRelations = hasNextLevel && allRelations[nextLevel.toString()] ?
    allRelations[nextLevel.toString()].filter(r => {
      // Handle both fully qualified names and short names
      // parent_class might be "Inference" while target_class is "ISO22989.Prediction"
      const targetShortName = relation.target_class.split('.').pop();
      const parentClassMatches = r.parent_class === relation.target_class || r.parent_class === targetShortName;
      console.log(`    Checking: ${r.property} → ${r.target_class} (parent: ${r.parent_class}) - matches ${relation.target_class} or ${targetShortName}? ${parentClassMatches}`);
      return parentClassMatches;
    }) :
    [];

  console.log(`  ✅ Found ${nextLevelRelations.length} next-level relations for ${relation.target_class}`);

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
        parentInstance?.id || null,
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
   * Handle "+ Add" button click for Level 2+ relations (need parent selection).
   */
  const handleAddClick = async () => {
    // Level 1: Has explicit parentInstance, show form directly
    if (parentInstance) {
      setShowForm(!showForm);
      return;
    }

    // Level 2+ in preview mode: Need to select parent first
    if (currentLevel > 1 && !parentInstance) {
      if (!showParentSelector) {
        // Load available parents
        await loadAvailableParents();
      }
      setShowParentSelector(!showParentSelector);
    } else {
      // Level 1: No parent needed, show form directly
      setShowForm(!showForm);
    }
  };

  /**
   * Load available parent instances for Level 2+ creation.
   */
  const loadAvailableParents = async () => {
    setLoadingParents(true);
    try {
      // Get the parent class from the relation metadata
      const parentClassName = relation.parent_class;

      if (!parentClassName) {
        console.error('No parent_class defined for this relation');
        return;
      }

      // Fetch all instances of the parent class
      const instances = await fetchInstancesByClass(parentClassName);
      console.log(`📋 Found ${instances.length} potential parent instances of ${parentClassName}`);
      setAvailableParents(instances);
    } catch (error) {
      console.error('Error loading parent instances:', error);
      setAvailableParents([]);
    } finally {
      setLoadingParents(false);
    }
  };

  /**
   * Handle parent selection from dropdown.
   */
  const handleSelectParent = (parent) => {
    setSelectedParentForCreation(parent);
    setShowParentSelector(false);
    setShowForm(true);
  };

  // Determine CSS class based on required status
  const rowClassName = [
    'annotation-relation-row',
    relation.is_required ? 'required' : 'optional'
  ].filter(Boolean).join(' ');

  return (
    <div className={rowClassName}>
      {/* Relation Header */}
      <div className="relation-header">
        <div className="relation-info">
          {/* Always show: ElementClass [arrow] property [arrow] TargetClass */}
          {/* For outgoing: Inference → creates → Prediction */}
          {/* For incoming: Inference ← executes ← MLModel */}
          {relation.direction === 'incoming' ? (
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

        <div className="relation-actions">
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

          <button
            className="relation-add-btn"
            onClick={handleAddClick}
            disabled={relation.is_graphical}
            title={relation.is_graphical
              ? `Cannot create new ${shortClassName} instances here. ${shortClassName} must be created as graphical nodes in the canvas.`
              : "Create new annotation"}
          >
            {showForm || showParentSelector ? '✕' : '+'} Add
          </button>

          <button
            className="relation-use-btn"
            onClick={handleUseClick}
            disabled={loadingInstances || linking}
            title="Link existing annotation"
          >
            ↔ Use {showUseDropdown ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* Description */}
      {description && (
        <div className="relation-description">{description}</div>
      )}

      {/* Parent Selector Dropdown (Level 2+) */}
      {showParentSelector && (
        <div className="relation-parent-selector">
          {loadingParents && <div className="dropdown-loading">Loading parent instances...</div>}

          {!loadingParents && availableParents.length === 0 && (
            <div className="dropdown-empty">
              No {relation.parent_class} instances available. Create one first.
            </div>
          )}

          {!loadingParents && availableParents.length > 0 && (
            <div className="dropdown-list">
              <div className="dropdown-header">
                Select parent {relation.parent_class} for this {shortClassName}:
              </div>
              {availableParents.map(parent => (
                <button
                  key={parent.id}
                  className="dropdown-item"
                  onClick={() => handleSelectParent(parent)}
                >
                  <span className="dropdown-item-name">{parent.display_name}</span>
                  <span className="dropdown-item-id">({parent.id})</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Use Existing Dropdown */}
      {showUseDropdown && (
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

      {/* Existing Instances */}
      {showInstances && relatedAnnotations.length > 0 && (
        <div className="relation-instances">
          {relatedAnnotations.map((ann, index) => (
            <AnnotationInstanceCard
              key={`${ann.id}-${index}`}
              annotation={ann}
              element={element}
              currentLevel={currentLevel}
              maxLevel={maxLevel}
              allAnnotations={allAnnotations}
              allRelations={allRelations}
              onAnnotationDeleted={onAnnotationDeleted}
              onAnnotationCreated={onAnnotationCreated}
            />
          ))}
        </div>
      )}

      {/* Creation Form */}
      {showForm && (
        <div className="relation-form">
          <AnnotationInstanceForm
            element={element}
            relation={relation}
            parentInstance={parentInstance || selectedParentForCreation}
            onSuccess={() => {
              setShowForm(false);
              setSelectedParentForCreation(null);
              onAnnotationCreated();
            }}
            onCancel={() => {
              setShowForm(false);
              setSelectedParentForCreation(null);
            }}
          />
        </div>
      )}

      {/* Nested Relations Preview (Level N+1) - Show structure even without instances */}
      {hasNextLevel && nextLevelRelations.length > 0 && (
        <div className="relation-nested-preview">
          <div
            className="nested-preview-header"
            onClick={() => setShowNestedRelations(!showNestedRelations)}
            title={showNestedRelations ? 'Hide nested relations' : 'Show nested relations'}
          >
            <span className="nested-toggle-btn">
              {showNestedRelations ? '▼' : '▶'}
            </span>
            <span className="nested-level-label">
              Level {nextLevel} Relations for {shortClassName}: ({nextLevelRelations.length})
            </span>
          </div>
          {showNestedRelations && (
            <div className="nested-relation-list">
              {nextLevelRelations.map((nextRelation, index) => (
                <AnnotationRelationRow
                  key={`${nextRelation.property}-${nextRelation.target_class}-${index}`}
                  relation={nextRelation}
                  element={element}
                  parentInstance={null}  // Preview mode, no specific parent yet
                  currentLevel={nextLevel}
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

export default AnnotationRelationRow;
