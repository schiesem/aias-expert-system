/**
 * AnnotationInstanceForm.jsx
 *
 * Form to create a new annotation instance.
 * Allows user to input instance name and optional properties.
 */

import React, { useState } from 'react';
import { createAnnotation, validateInstanceData } from '../../utils/annotationUtils';
import './AnnotationInstanceForm.css';

const AnnotationInstanceForm = ({
  element,
  relation,
  onSuccess,
  onCancel,
  parentInstance = null,
  availableParents = []  // Keep for backward compatibility, but not used in nested mode
}) => {
  const [instanceName, setInstanceName] = useState('');
  const [properties, setProperties] = useState({});
  const [newPropKey, setNewPropKey] = useState('');
  const [newPropValue, setNewPropValue] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  // In nested mode: parentInstance is the annotation object with {id, displayName, ...}
  // In old mode: availableParents is array and selectedParent is chosen from dropdown
  const [selectedParent, setSelectedParent] = useState(
    parentInstance ? parentInstance.id : ''  // Use .id instead of .name
  );

  /**
   * Add a new property to the instance.
   */
  const handleAddProperty = () => {
    if (!newPropKey.trim()) {
      alert('Property key cannot be empty');
      return;
    }

    if (properties[newPropKey]) {
      alert('Property key already exists');
      return;
    }

    setProperties({
      ...properties,
      [newPropKey]: newPropValue
    });

    // Reset inputs
    setNewPropKey('');
    setNewPropValue('');
  };

  /**
   * Remove a property from the instance.
   */
  const handleRemoveProperty = (key) => {
    const newProps = { ...properties };
    delete newProps[key];
    setProperties(newProps);
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate instance data
    const instanceData = {
      name: instanceName.trim(),
      properties: properties
    };

    const validation = validateInstanceData(instanceData);
    if (!validation.valid) {
      setError(validation.error);
      return;
    }

    // Validate parent selection for Level 2+ annotations (only in old mode with dropdown)
    if (!parentInstance && availableParents.length > 0 && !selectedParent) {
      setError('Please select a parent instance');
      return;
    }

    setCreating(true);

    try {
      // Get direction from relation (default to outgoing)
      const direction = relation.direction || 'outgoing';

      await createAnnotation(
        element.id,
        element.class,
        relation.property,
        relation.target_class,
        instanceData,
        selectedParent || null,  // Pass parent instance name if selected
        direction  // Pass direction for incoming vs outgoing relations
      );

      // Success
      onSuccess();
    } catch (err) {
      console.error('Error creating annotation:', err);
      setError(err.message || 'Failed to create annotation');
    } finally {
      setCreating(false);
    }
  };

  return (
    <form className="annotation-instance-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <h4>Create New {relation.target_class} Instance</h4>
      </div>

      {error && (
        <div className="form-error">
          <span className="error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* Parent Instance Info (for Level 2+ annotations in nested mode) */}
      {parentInstance && (
        <div className="form-group form-readonly">
          <label className="form-label">Parent Instance:</label>
          <div className="parent-info">
            <span className="parent-name">{parentInstance.displayName}</span>
            <span className="parent-class">({parentInstance.shortClass})</span>
          </div>
          <div className="form-hint">
            This annotation will be linked to {parentInstance.displayName}.
          </div>
        </div>
      )}

      {/* Parent Instance Selector (for Level 2+ annotations in old mode - backward compatibility) */}
      {!parentInstance && availableParents.length > 0 && (
        <div className="form-group">
          <label htmlFor="parent-instance" className="form-label">
            Parent Instance <span className="form-required">*</span>
          </label>
          <select
            id="parent-instance"
            className="form-input"
            value={selectedParent}
            onChange={(e) => setSelectedParent(e.target.value)}
            required
            disabled={creating}
          >
            <option value="">-- Select Parent Instance --</option>
            {availableParents.map((parent) => (
              <option key={parent.name} value={parent.name}>
                {parent.name} ({parent.shortClass || parent.class})
              </option>
            ))}
          </select>
          <div className="form-hint">
            This annotation will be linked to the selected parent instance.
          </div>
        </div>
      )}

      {/* Instance Name */}
      <div className="form-group">
        <label htmlFor="instance-name" className="form-label">
          Instance Name <span className="form-required">*</span>
        </label>
        <input
          type="text"
          id="instance-name"
          className="form-input"
          value={instanceName}
          onChange={(e) => setInstanceName(e.target.value)}
          placeholder="e.g., MyModel, DataSet1, etc."
          required
          disabled={creating}
        />
        <div className="form-hint">
          Use letters, numbers, underscores, or hyphens only.
        </div>
      </div>

      {/* Properties (Optional) */}
      <div className="form-group">
        <label className="form-label">
          Properties <span className="form-optional">(optional)</span>
        </label>

        {/* Existing Properties */}
        {Object.keys(properties).length > 0 && (
          <div className="property-list">
            {Object.entries(properties).map(([key, value]) => (
              <div key={key} className="property-item">
                <div className="property-item-info">
                  <span className="property-key">{key}:</span>
                  <span className="property-value">{value}</span>
                </div>
                <button
                  type="button"
                  className="property-remove"
                  onClick={() => handleRemoveProperty(key)}
                  disabled={creating}
                  title="Remove property"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add New Property */}
        <div className="property-add">
          <input
            type="text"
            className="form-input form-input-small"
            placeholder="Property key"
            value={newPropKey}
            onChange={(e) => setNewPropKey(e.target.value)}
            disabled={creating}
          />
          <input
            type="text"
            className="form-input form-input-small"
            placeholder="Property value"
            value={newPropValue}
            onChange={(e) => setNewPropValue(e.target.value)}
            disabled={creating}
          />
          <button
            type="button"
            className="form-btn form-btn-add"
            onClick={handleAddProperty}
            disabled={creating || !newPropKey.trim()}
          >
            + Add
          </button>
        </div>
      </div>

      {/* Form Actions */}
      <div className="form-actions">
        <button
          type="button"
          className="form-btn form-btn-cancel"
          onClick={onCancel}
          disabled={creating}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="form-btn form-btn-submit"
          disabled={creating || !instanceName.trim()}
        >
          {creating ? 'Creating...' : 'Create Instance'}
        </button>
      </div>
    </form>
  );
};

export default AnnotationInstanceForm;
