/**
 * Card.jsx
 *
 * Reusable card container component matching AnnotationWindow design.
 * Supports panel (fixed) and modal (overlay) variants.
 */

import React from 'react';
import './ui.css';

/**
 * Main Card container
 */
export const Card = ({ children, variant = 'panel', className = '' }) => {
  const baseClass = variant === 'modal' ? 'ui-card-modal' : 'ui-card-panel';

  return (
    <div className={`${baseClass} ${className}`}>
      {children}
    </div>
  );
};

/**
 * Card Header with title, optional badge, and optional close button
 */
export const CardHeader = ({ title, badge, onClose, icon }) => {
  return (
    <div className="ui-card-header">
      <div className="ui-card-title">
        {icon && <span className="ui-card-icon">{icon}</span>}
        <h2>{title}</h2>
        {badge !== null && badge !== undefined && (
          <span className="ui-badge ui-badge-success">{badge}</span>
        )}
      </div>
      {onClose && (
        <button
          className="ui-card-close"
          onClick={onClose}
          title="Close"
          aria-label="Close"
        >
          ×
        </button>
      )}
    </div>
  );
};

/**
 * Card Info section - displays label/value pairs
 */
export const CardInfo = ({ rows = [] }) => {
  if (rows.length === 0) return null;

  return (
    <div className="ui-card-info">
      {rows.map((row, index) => (
        <div key={index} className="ui-info-row">
          <span className="ui-info-label">{row.label}:</span>
          <span className="ui-info-value">{row.value}</span>
        </div>
      ))}
    </div>
  );
};

/**
 * Card Actions toolbar - for buttons and controls
 */
export const CardActions = ({ children, align = 'space-between' }) => {
  const alignClass = align === 'left' ? 'ui-actions-left' :
                     align === 'right' ? 'ui-actions-right' :
                     'ui-actions-space-between';

  return (
    <div className={`ui-card-actions ${alignClass}`}>
      {children}
    </div>
  );
};

/**
 * Card Content - scrollable main content area
 */
export const CardContent = ({ children, className = '' }) => {
  return (
    <div className={`ui-card-content ${className}`}>
      {children}
    </div>
  );
};

/**
 * Card Footer - optional footer with hints or additional info
 */
export const CardFooter = ({ children }) => {
  return (
    <div className="ui-card-footer">
      {children}
    </div>
  );
};

export default Card;
