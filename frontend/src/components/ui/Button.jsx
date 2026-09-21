/**
 * Button.jsx
 *
 * Reusable button component with variants matching AnnotationWindow design.
 */

import React from 'react';
import './ui.css';

const Button = ({
  children,
  variant = 'primary',
  icon,
  onClick,
  disabled = false,
  loading = false,
  className = '',
  type = 'button',
  ...props
}) => {
  const variantClass = `ui-btn-${variant}`;
  const loadingClass = loading ? 'ui-btn-loading' : '';

  return (
    <button
      type={type}
      className={`ui-btn ${variantClass} ${loadingClass} ${className}`}
      onClick={onClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="ui-btn-spinner">⏳</span>}
      {!loading && icon && <span className="ui-btn-icon">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};

export default Button;
