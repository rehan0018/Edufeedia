import React, { useState } from 'react';
import { Sparkles, Lock, Mail, ArrowRight, UserCheck, ShieldCheck } from 'lucide-react';
import { apiLogin } from '../services/api';

export default function AuthScreen({ onLoginSuccess }) {
  const [email, setEmail] = useState('rahul@apexschool.edu');
  const [password, setPassword] = useState('Student123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await apiLogin(email, password);
      onLoginSuccess(data.user);
    } catch (err) {
      setError('Invalid email or password. Please try demo accounts below.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDemo = async (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setLoading(true);
    setError('');
    try {
      const data = await apiLogin(demoEmail, demoPass);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err?.message || 'Authentication failed. Please verify credentials or backend status.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px',
      position: 'relative'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '440px',
        padding: '36px 32px',
        background: 'var(--bg-card-solid)',
        border: '1px solid var(--border-glow)'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px auto',
            boxShadow: 'var(--shadow-glow-cyan)'
          }}>
            <Sparkles size={26} color="#0a0f1d" />
          </div>
          <h1 style={{ fontSize: '1.8rem', marginBottom: '6px' }}>Edufeedia</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Safe, distraction-free learning for students under 18.
          </p>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            background: 'hsla(346, 84%, 61%, 0.15)',
            border: '1px solid var(--accent-rose)',
            color: 'var(--accent-rose)',
            fontSize: '0.85rem',
            marginBottom: '18px'
          }}>
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              School Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 42px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-space)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 42px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-space)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: '12px', marginTop: '8px' }}
          >
            {loading ? 'Authenticating...' : 'Login to Account'} <ArrowRight size={16} />
          </button>
        </form>

        {/* 1-Click Demo Personas */}
        <div style={{
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-space)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '10px', textTransform: 'uppercase' }}>
            💡 1-Click Demo Persona Access
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              style={{ justifyContent: 'flex-start' }}
              onClick={() => handleSelectDemo('rahul@apexschool.edu', 'Student123!')}
            >
              🎓 <strong>Student:</strong> Rahul Kumar (Grade 10)
            </button>

            <button
              type="button"
              className="btn btn-outline btn-sm"
              style={{ justifyContent: 'flex-start' }}
              onClick={() => handleSelectDemo('sharma@apexschool.edu', 'Teacher123!')}
            >
              👩‍🏫 <strong>Teacher:</strong> Mrs. Sharma (Apex School)
            </button>

            <button
              type="button"
              className="btn btn-outline btn-sm"
              style={{ justifyContent: 'flex-start' }}
              onClick={() => handleSelectDemo('parent@gmail.com', 'Parent123!')}
            >
              👨‍👩‍👧 <strong>Parent:</strong> Rajesh Kumar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
