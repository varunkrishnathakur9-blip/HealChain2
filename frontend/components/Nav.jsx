import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './Button';

/**
 * Navigation Component
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.walletConnect - Wallet connect component to display
 */
export const Nav = ({ walletConnect, className = '' }) => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/tasks', label: 'Tasks' },
    { path: '/mining', label: 'Mining' },
    { path: '/rewards', label: 'Rewards' },
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const navStyle = {
    backgroundColor: 'var(--color-bg-primary)',
    borderBottom: '1px solid var(--color-border)',
    padding: 'var(--space-4) var(--space-6)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: 'var(--shadow-sm)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  };

  const brandStyle = {
    fontSize: 'var(--font-size-2xl)',
    fontWeight: 700,
    color: 'var(--color-primary)',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--space-2)',
  };

  const linksStyle = {
    display: 'flex',
    gap: 'var(--space-6)',
    alignItems: 'center',
    listStyle: 'none',
  };

  const linkStyle = (active) => ({
    color: active ? 'var(--color-primary)' : 'var(--color-text-secondary)',
    textDecoration: 'none',
    fontSize: 'var(--font-size-sm)',
    fontWeight: active ? 500 : 400,
    transition: 'color 200ms ease',
    padding: 'var(--space-2) 0',
    borderBottom: active ? '2px solid var(--color-primary)' : '2px solid transparent',
  });

  return (
    <nav className={`nav ${className}`} style={navStyle}>
      <Link to="/" style={brandStyle}>
        <span>⛓️</span>
        <span>HealChain</span>
      </Link>

      {/* Desktop Navigation */}
      <div className="hide-mobile" style={linksStyle}>
        {navLinks.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            style={linkStyle(isActive(link.path))}
            onMouseEnter={(e) => {
              if (!isActive(link.path)) {
                e.target.style.color = 'var(--color-primary)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive(link.path)) {
                e.target.style.color = 'var(--color-text-secondary)';
              }
            }}
          >
            {link.label}
          </Link>
        ))}
        {walletConnect && <div style={{ marginLeft: 'var(--space-4)' }}>{walletConnect}</div>}
      </div>

      {/* Mobile Menu Button */}
      <button
        className="show-mobile-only"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        style={{
          background: 'none',
          border: 'none',
          fontSize: 'var(--font-size-2xl)',
          cursor: 'pointer',
          color: 'var(--color-text-primary)',
          padding: 'var(--space-2)',
        }}
        aria-label="Toggle menu"
      >
        {mobileMenuOpen ? '✕' : '☰'}
      </button>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div
          className="show-mobile-only"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'var(--color-bg-primary)',
            borderBottom: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-md)',
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)',
          }}
        >
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              style={{
                ...linkStyle(isActive(link.path)),
                display: 'block',
                padding: 'var(--space-3)',
              }}
            >
              {link.label}
            </Link>
          ))}
          {walletConnect && (
            <div style={{ marginTop: 'var(--space-2)' }}>{walletConnect}</div>
          )}
        </div>
      )}

      <style>{`
        @media (max-width: 640px) {
          .nav .show-mobile-only {
            display: block !important;
          }
          .nav .hide-mobile {
            display: none !important;
          }
        }
        @media (min-width: 641px) {
          .nav .show-mobile-only {
            display: none !important;
          }
          .nav .hide-mobile {
            display: flex !important;
          }
        }
      `}</style>
    </nav>
  );
};

export default Nav;

