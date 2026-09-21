/**
 * Badge.jsx
 *
 * Badge component for counts and status indicators.
 */

import React from 'react';
import './ui.css';

const Badge = ({ children, variant = 'success', className = '' }) => {
  const variantClass = `ui-badge-${variant}`;

  return (
    <span className={`ui-badge ${variantClass} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;
