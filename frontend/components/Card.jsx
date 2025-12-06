import React from 'react';

/**
 * Card Component
 * 
 * @param {Object} props
 * @param {string} props.title - Card title
 * @param {string} props.subtitle - Card subtitle
 * @param {React.ReactNode} props.children - Card content
 * @param {React.ReactNode} props.action - Action element (button, link, etc.)
 * @param {'success' | 'warning' | 'error' | 'info'} props.highlight - Highlight border color
 * @param {string} props.className - Additional CSS classes
 */
export const Card = ({
  title,
  subtitle,
  children,
  action,
  highlight,
  className = '',
  ...props
}) => {
  const highlightColor = highlight
    ? {
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        error: 'var(--color-error)',
        info: 'var(--color-primary)',
      }[highlight]
    : null;

  const cardStyle = {
    backgroundColor: 'var(--color-bg-primary)',
    border: `1px solid var(--color-border)`,
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--space-6)',
    boxShadow: 'var(--shadow-md)',
    transition: 'all 200ms ease',
    ...(highlightColor && {
      borderLeft: `4px solid ${highlightColor}`,
    }),
  };

  return (
    <div
      className={`card ${className}`}
      style={cardStyle}
      {...props}
    >
      {(title || subtitle || action) && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: title || subtitle ? 'var(--space-3)' : 0,
          }}
        >
          <div style={{ flex: 1 }}>
            {title && (
              <h3
                style={{
                  fontSize: 'var(--font-size-lg)',
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  margin: 0,
                  marginBottom: subtitle ? 'var(--space-2)' : 0,
                }}
              >
                {title}
              </h3>
            )}
            {subtitle && (
              <p
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  margin: 0,
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {action && <div style={{ marginLeft: 'var(--space-4)' }}>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;

