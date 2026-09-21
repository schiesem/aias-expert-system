/**
 * styleUtils.js
 *
 * Shared styling utilities for UI components.
 */

/**
 * Classname utility - combines multiple classnames, filtering out falsy values
 * @param  {...any} classes - Class names or conditional classes
 * @returns {string} - Combined class names
 *
 * Example:
 *   cn('btn', isActive && 'active', disabled && 'disabled')
 *   // Returns: "btn active" (if isActive=true, disabled=false)
 */
export const cn = (...classes) => {
  return classes.filter(Boolean).join(' ');
};

/**
 * Get element type icon
 * @param {string} type - Element type (FunctionNode, ProductNode, etc.)
 * @returns {string} - Icon emoji
 */
export const getElementIcon = (type) => {
  const iconMap = {
    FunctionNode: '⚙️',
    ProductNode: '📦',
    ResourceNode: '💻',
    CommunicationEdge: '📡',
    AssignmentEdge: '🔗',
    FlowEdge: '➡️',
  };

  return iconMap[type] || '📄';
};

/**
 * Get element type color
 * @param {string} type - Element type
 * @returns {string} - Color hex code
 */
export const getElementColor = (type) => {
  const colorMap = {
    FunctionNode: '#2196F3',    // Blue
    ProductNode: '#FF9800',     // Orange
    ResourceNode: '#4CAF50',    // Green
    CommunicationEdge: '#9C27B0', // Purple
    AssignmentEdge: '#F44336',  // Red
    FlowEdge: '#00BCD4',        // Cyan
  };

  return colorMap[type] || '#666666';
};

/**
 * Format date to readable string
 * @param {Date|string|number} date - Date to format
 * @returns {string} - Formatted date string
 */
export const formatDate = (date) => {
  if (!date) return 'Never';

  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid date';

  const now = new Date();
  const diffMs = now - d;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return d.toLocaleDateString();
};

/**
 * Truncate string to max length
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated string with ellipsis
 */
export const truncate = (str, maxLength = 50) => {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
};
