/**
 * ClassDefinitionDisplay.jsx
 *
 * Displays the rdfs:comment definition of an ontology class.
 * Used in element config panels to show class descriptions.
 */

import React from 'react';
import './ui.css';

const ClassDefinitionDisplay = ({ definition, className = '' }) => {
  // Don't render if no definition or placeholder text
  if (!definition || definition === 'tbd.' || definition.trim() === '') {
    return null;
  }

  return (
    <div className={`ui-class-definition ${className}`}>
      <p className="ui-class-definition-text">{definition}</p>
    </div>
  );
};

export default ClassDefinitionDisplay;
