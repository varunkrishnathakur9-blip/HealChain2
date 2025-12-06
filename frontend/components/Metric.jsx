import React from 'react';

/**
 * Metric Display Component
 * 
 * @param {Object} props
 * @param {string} props.label - Metric label
 * @param {string | number} props.value - Metric value
 * @param {string} props.unit - Unit text (e.g., "ETH", "%")
 * @param {Object} props.change - Change indicator { value: number, direction: 'up' | 'down' }
 * @param {React.ReactNode} props.icon - Icon element
 */
export const Metric = ({
  label,
  value,
  unit,
  change,
  icon,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`metric ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-4)',
        padding: 'var(--space-4)',
        backgroundColor: 'var(--color-bg-secondary)',
        borderRadius: 'var(--radius-md)',
      }}
      {...props}
    >
      {icon && (
        <div
          style={{
            fontSize: '24px',
            opacity: 0.7,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0,
            marginBottom: 'var(--space-1)',
          }}
        >
          {label}
        </p>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 'var(--space-2)',
            flexWrap: 'wrap',
          }}
        >
          <span
            style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              lineHeight: 1,
            }}
          >
            {value}
          </span>
          {unit && (
            <span
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
              }}
            >
              {unit}
            </span>
          )}
          {change && (
            <span
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 500,
                color:
                  change.direction === 'up'
                    ? 'var(--color-success)'
                    : 'var(--color-error)',
                marginLeft: 'var(--space-2)',
              }}
            >
              {change.direction === 'up' ? '↑' : '↓'} {Math.abs(change.value)}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Metric;

