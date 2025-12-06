import React from 'react';

/**
 * Progress Bar Component
 * 
 * @param {Object} props
 * @param {number} props.value - Progress value (0-100)
 * @param {string} props.label - Label text above bar
 * @param {'primary' | 'success' | 'warning' | 'error'} props.color - Progress bar color
 * @param {boolean} props.showPercentage - Show percentage value
 */
export const ProgressBar = ({
  value,
  label,
  color = 'primary',
  showPercentage = true,
  className = '',
  ...props
}) => {
  const clampedValue = Math.max(0, Math.min(100, value));
  const roundedValue = Math.round(clampedValue);

  const colorMap = {
    primary: 'var(--color-primary)',
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    error: 'var(--color-error)',
  };

  const progressColor = colorMap[color] || colorMap.primary;

  return (
    <div className={`progress-bar ${className}`} {...props}>
      {(label || showPercentage) && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 'var(--space-2)',
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
          }}
        >
          {label && <span>{label}</span>}
          {showPercentage && <span>{roundedValue}%</span>}
        </div>
      )}
      <div
        style={{
          height: '8px',
          backgroundColor: 'var(--color-border)',
          borderRadius: '99px',
          overflow: 'hidden',
          width: '100%',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${clampedValue}%`,
            backgroundColor: progressColor,
            transition: 'width 300ms ease',
            borderRadius: '99px',
          }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;

