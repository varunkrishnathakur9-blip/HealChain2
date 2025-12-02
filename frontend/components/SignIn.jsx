import React from 'react';

const SignIn = ({ onSignIn }) => {
  const handleGoogleSignIn = () => {
    // Try to use Google Identity Services if available, otherwise fallback to prompt
    if (window.google && window.google.accounts && window.google.accounts.id) {
      // Lightweight one-tap style: request a credential and decode it on the backend in full apps
      window.google.accounts.id.prompt();
      // For demo purposes, fallback to a mock sign-in after prompt
      setTimeout(() => {
        onSignIn({ name: 'Google User', email: 'user@example.com' });
      }, 500);
    } else {
      // Fallback: simple prompt to collect a name/email for local development
      const name = window.prompt('Enter your name (dev fallback)') || 'Dev User';
      const email = window.prompt('Enter your email (dev fallback)') || 'dev@example.com';
      onSignIn({ name, email });
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', padding: 24, background: '#fff', borderRadius: 8 }}>
      <h2 style={{ marginBottom: 12 }}>Sign up / Sign in</h2>
      <p style={{ color: '#444' }}>Sign in with Google to continue (development fallback supported).</p>
      <div style={{ display: 'flex', gap: 12, marginTop: 18 }}>
        <button onClick={handleGoogleSignIn} style={{ padding: '10px 16px', background: '#4285F4', color: 'white', border: 'none', borderRadius: 6 }}>Sign in with Google</button>
        <button onClick={() => onSignIn({ name: 'Guest', email: 'guest@example.com' })} style={{ padding: '10px 16px' }}>Continue as Guest</button>
      </div>
    </div>
  );
};

export default SignIn;
