import React from 'react';

/**
 * Button Component - All Variants
 * 
 * @param {Object} props
 * @param {'primary' | 'secondary' | 'outline' | 'ghost'} props.variant - Button style variant
 * @param {'sm' | 'md' | 'lg'} props.size - Button size
 * @param {boolean} props.disabled - Disable button
 * @param {boolean} props.loading - Show loading state
 * @param {React.ReactNode} props.icon - Icon element
 * @param {Function} props.onClick - Click handler
 * @param {React.ReactNode} props.children - Button content
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.type - Button type (button, submit, reset)
 */
export const Button = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  onClick,
  children,
  className = '',
  type = 'button',
  ...props
}) => {
  const baseStyles = {
    fontFamily: 'var(--font-family-base)',
    fontWeight: 500,
    borderRadius: 'var(--radius-md)',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 200ms ease',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 'var(--space-2)',
    border: 'none',
    outline: 'none',
    opacity: disabled || loading ? 0.5 : 1,
    pointerEvents: disabled || loading ? 'none' : 'auto',
  };

  const sizeStyles = {
    sm: {
      padding: 'var(--space-2) var(--space-3)',
      fontSize: 'var(--font-size-sm)',
    },
    md: {
      padding: 'var(--space-3) var(--space-4)',
      fontSize: 'var(--font-size-base)',
    },
    lg: {
      padding: 'var(--space-4) var(--space-6)',
      fontSize: 'var(--font-size-lg)',
    },
  };

  const variantStyles = {
    primary: {
      backgroundColor: 'var(--color-primary)',
      color: 'white',
      border: '1px solid var(--color-primary)',
    },
    secondary: {
      backgroundColor: 'var(--color-bg-secondary)',
      color: 'var(--color-text-primary)',
      border: '1px solid var(--color-border)',
    },
    outline: {
      backgroundColor: 'transparent',
      color: 'var(--color-primary)',
      border: '2px solid var(--color-primary)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--color-text-secondary)',
      border: 'none',
    },
  };

  const hoverStyles = {
    primary: {
      ':hover': {
        backgroundColor: 'var(--color-primary-dark)',
      },
    },
    secondary: {
      ':hover': {
        backgroundColor: 'var(--color-bg-tertiary)',
      },
    },
    outline: {
      ':hover': {
        backgroundColor: 'var(--color-primary-light)',
      },
    },
    ghost: {
      ':hover': {
        color: 'var(--color-text-primary)',
      },
    },
  };

  const combinedStyle = {
    ...baseStyles,
    ...sizeStyles[size],
    ...variantStyles[variant],
  };

  return (
    <button
      type={type}
      className={className}
      style={combinedStyle}
      onClick={onClick}
      disabled={disabled || loading}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          Object.assign(e.target.style, hoverStyles[variant][':hover']);
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          Object.assign(e.target.style, variantStyles[variant]);
        }
      }}
      {...props}
    >
      {loading && (
        <span
          style={{
            display: 'inline-block',
            width: '14px',
            height: '14px',
            border: '2px solid currentColor',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 0.6s linear infinite',
          }}
        />
      )}
      {icon && !loading && icon}
      {children}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
};

export default Button;

