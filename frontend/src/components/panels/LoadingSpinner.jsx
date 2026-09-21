/**
 * LoadingSpinner.jsx
 *
 * Simple loading spinner component with optional message.
 */

import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Loading...' }) => {
  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner">
        <div className="spinner-circle"></div>
      </div>
      {message && <div className="loading-message">{message}</div>}
    </div>
  );
};

export default LoadingSpinner;
