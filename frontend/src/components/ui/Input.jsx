/**
 * Input.jsx
 *
 * Reusable text input component with consistent styling.
 */

import React from 'react';
import './ui.css';

const Input = ({
  value,
  onChange,
  placeholder = '',
  disabled = false,
  error = false,
  className = '',
  type = 'text',
  ...props
}) => {
  const errorClass = error ? 'ui-input-error' : '';

  const handleChange = (e) => {
    if (onChange) {
      onChange(e.target.value, e);
    }
  };

  return (
    <input
      type={type}
      className={`ui-input ${errorClass} ${className}`}
      value={value || ''}
      onChange={handleChange}
      placeholder={placeholder}
      disabled={disabled}
      {...props}
    />
  );
};

export default Input;
