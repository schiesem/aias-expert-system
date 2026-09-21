/**
 * EmptyState.jsx
 *
 * Component for displaying empty states, errors, or informational messages.
 */

import React from 'react';
import './ui.css';

const EmptyState = ({
  icon,
  message,
  submessage,
  variant = 'info',
  className = ''
}) => {
  const variantClass = `ui-empty-${variant}`;

  return (
    <div className={`ui-empty-state ${variantClass} ${className}`}>
      {icon && <div className="ui-empty-icon">{icon}</div>}
      <p className="ui-empty-message">{message}</p>
      {submessage && <p className="ui-empty-submessage">{submessage}</p>}
    </div>
  );
};

export default EmptyState;
