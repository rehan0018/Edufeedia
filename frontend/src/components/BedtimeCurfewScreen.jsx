import React from 'react';
import { Moon, Stars, Lock, ShieldCheck, Sun } from 'lucide-react';

export default function BedtimeCurfewScreen({ childName, curfewHours, message, onOpenParentGate }) {
  return (
    <div style={{
      minHeight: '85vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      position: 'relative'
    }}>
      <div className="kids-card" style={{
        maxWidth: '560px',
        width: '100%',
        padding: '48px 36px',
        textAlign: 'center',
        background: 'linear-gradient(180deg, #1A2138 0%, #0F1523 100%)',
        color: '#FFFFFF',
        border: '3px solid #2F3B5C',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)'
      }}>

        {/* Night Sky Glow & Sleeping Mascot */}
        <div style={{ position: 'relative', width: '120px', height: '120px', margin: '0 auto 24px auto' }}>
          <div style={{
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(255, 209, 102, 0.25) 0%, rgba(37, 99, 235, 0.05) 70%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '4rem'
          }}>
            😴
          </div>
          <div style={{ position: 'absolute', top: '-10px', right: '-10px', color: '#FFD166' }}>
            <Moon size={36} fill="#FFD166" />
          </div>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          borderRadius: '20px',
          background: 'rgba(255, 209, 102, 0.15)',
          color: '#FFD166',
          fontSize: '0.85rem',
          fontWeight: 700,
          marginBottom: '16px'
        }}>
          <Stars size={16} /> Bedtime Sleep Routine Active
        </div>

        <h1 style={{ fontSize: '1.9rem', fontWeight: 800, marginBottom: '12px', color: '#FFFFFF' }}>
          EduFeedia is sleeping too! 🌙
        </h1>

        <p style={{ fontSize: '1.05rem', color: '#CBD5E1', lineHeight: '1.6', marginBottom: '24px' }}>
          {message || `Sweet dreams, ${childName || 'explorer'}! Good sleep helps your brain remember all the awesome discoveries you made today.`}
        </p>

        {curfewHours && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.06)',
            borderRadius: '16px',
            padding: '12px 18px',
            fontSize: '0.88rem',
            color: '#94A3B8',
            marginBottom: '28px'
          }}>
            ⏰ Scheduled Curfew: <strong>{curfewHours}</strong>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={onOpenParentGate}
            style={{
              background: 'transparent',
              border: '2px solid rgba(255, 255, 255, 0.25)',
              color: '#CBD5E1',
              padding: '10px 22px',
              borderRadius: '20px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s ease'
            }}
          >
            <Lock size={16} /> Grown-Up Settings & Controls
          </button>
        </div>

      </div>
    </div>
  );
}
