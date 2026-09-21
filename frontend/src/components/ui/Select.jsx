/**
 * Select.jsx
 *
 * Reusable dropdown select component with consistent styling.
 */

import React from 'react';
import { getShortClassName } from '../../utils/annotationUtils';
import './ui.css';

const Select = ({
  value,
  onChange,
  options = [],
  placeholder = 'Select...',
  disabled = false,
  optionKey = null,
  optionValue = null,
  className = '',
  ...props
}) => {
  const handleChange = (e) => {
    if (onChange) {
      onChange(e.target.value, e);
    }
  };

  // Support both array of strings and array of objects
  const renderOptions = () => {
    return options.map((option, index) => {
      let optKey, optVal;

      if (typeof option === 'string') {
        optKey = option;
        optVal = option;
      } else if (typeof option === 'object') {
        // If optionKey/optionValue are provided, use them
        // Otherwise, use the first property of the object
        if (optionKey && optionValue) {
          optKey = option[optionKey];
          optVal = option[optionValue];
        } else {
          // Default: assume object like { functionType: "Train" } or { resourceType: "Sensor" }
          const keys = Object.keys(option);
          if (keys.length > 0) {
            optKey = option[keys[0]];
            optVal = option[keys[0]];
          }
        }
      }

      // Der Wert bleibt namensraumqualifiziert (z.B. "ISO22989.Acquisition"),
      // angezeigt wird nur der Klassenname.
      return (
        <option key={`${optKey}-${index}`} value={optVal}>
          {getShortClassName(optKey)}
        </option>
      );
    });
  };

  return (
    <select
      className={`ui-select ${className}`}
      value={value || ''}
      onChange={handleChange}
      disabled={disabled}
      {...props}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {renderOptions()}
    </select>
  );
};

export default Select;
