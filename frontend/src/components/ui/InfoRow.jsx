/**
 * InfoRow.jsx
 *
 * Single label/value row for displaying information.
 */

import React from 'react';
import './ui.css';

const InfoRow = ({ label, value, className = '' }) => {
  return (
    <div className={`ui-info-row ${className}`}>
      <span className="ui-info-label">{label}:</span>
      <span className="ui-info-value">{value}</span>
    </div>
  );
};

export default InfoRow;
