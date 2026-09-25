import React from 'react';
import { X, Info, CheckCircle2, ShieldCheck, HeartHandshake, Compass } from 'lucide-react';

export default function WhySeeingThisModal({ isOpen, onClose, explanation }) {
  if (!isOpen || !explanation) return null;

  return (
    <div className="modal-backdrop">
      <div className="kids-card" style={{ maxWidth: '500px', width: '100%', padding: '28px 24px', position: 'relative' }}>
        
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: 'rgba(37, 99, 235, 0.12)',
            color: '#2563EB',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Info size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
              Why was this recommended?
            </h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Transparent Recommendation Explainability
            </span>
          </div>
        </div>

        {/* Content Title */}
        <div style={{
          background: 'var(--bg-main)',
          border: '2px solid #E2DED0',
          borderRadius: '16px',
          padding: '12px 16px',
          marginBottom: '18px'
        }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>
            Module Title
          </div>
          <div style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
            {explanation.title}
          </div>
        </div>

        {/* Reasons List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
          {explanation.reasons && explanation.reasons.map((reason, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                padding: '10px 14px',
                borderRadius: '14px',
                background: 'rgba(52, 191, 163, 0.08)',
                border: '1px solid rgba(52, 191, 163, 0.3)'
              }}
            >
              <CheckCircle2 size={18} color="#0D9488" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: '1.4' }}>
                {reason}
              </span>
            </div>
          ))}
        </div>

        {/* Learning Balance Notice */}
        {explanation.learning_balance_note && (
          <div style={{
            background: 'rgba(255, 209, 102, 0.15)',
            border: '1px solid #FFD166',
            borderRadius: '14px',
            padding: '12px 16px',
            marginBottom: '20px',
            fontSize: '0.85rem',
            color: 'var(--text-primary)'
          }}>
            <strong>⚖️ Learning Balance:</strong> {explanation.learning_balance_note}
          </div>
        )}

        <button
          onClick={onClose}
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center', borderRadius: '16px', padding: '12px' }}
        >
          Got it! 👍
        </button>

      </div>
    </div>
  );
}
