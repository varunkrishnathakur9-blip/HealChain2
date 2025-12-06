import React from 'react';

/**
 * Badge Component - Status Indicator
 * 
 * @param {Object} props
 * @param {'active' | 'pending' | 'completed' | 'failed' | 'locked'} props.status - Badge status
 * @param {string} props.label - Custom label text (defaults to status)
 * @param {'sm' | 'md' | 'lg'} props.size - Badge size
 */
export const Badge = ({
  status,
  label,
  size = 'md',
  className = '',
  ...props
}) => {
  const statusConfig = {
    active: {
      bg: 'var(--color-success-light)',
      text: 'var(--color-success)',
      dot: '🟢',
      defaultLabel: 'Active',
    },
    pending: {
      bg: 'var(--color-warning-light)',
      text: 'var(--color-warning)',
      dot: '🟡',
      defaultLabel: 'Pending',
    },
    completed: {
      bg: 'var(--color-success-light)',
      text: 'var(--color-success)',
      dot: '✅',
      defaultLabel: 'Completed',
    },
    failed: {
      bg: 'var(--color-error-light)',
      text: 'var(--color-error)',
      dot: '❌',
      defaultLabel: 'Failed',
    },
    locked: {
      bg: 'var(--color-bg-tertiary)',
      text: 'var(--color-text-secondary)',
      dot: '🔒',
      defaultLabel: 'Locked',
    },
  };

  const config = statusConfig[status] || statusConfig.pending;
  const sizeMap = {
    sm: { fontSize: '12px', padding: 'var(--space-1) var(--space-3)' },
    md: { fontSize: '14px', padding: 'var(--space-2) var(--space-3)' },
    lg: { fontSize: '16px', padding: 'var(--space-2) var(--space-4)' },
  };

  const badgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 'var(--space-1)',
    padding: sizeMap[size].padding,
    backgroundColor: config.bg,
    color: config.text,
    borderRadius: '99px',
    fontSize: sizeMap[size].fontSize,
    fontWeight: 500,
    lineHeight: 1,
  };

  return (
    <span
      className={`badge badge-${status} ${className}`}
      style={badgeStyle}
      {...props}
    >
      <span>{config.dot}</span>
      <span>{label || config.defaultLabel}</span>
    </span>
  );
};

export default Badge;

