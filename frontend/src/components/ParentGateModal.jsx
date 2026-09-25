import React, { useState } from 'react';
import { ShieldCheck, Lock, X, AlertCircle, CheckCircle2, KeyRound } from 'lucide-react';
import { verifyParentPin } from '../services/api';

export default function ParentGateModal({ isOpen, onClose, onSuccess }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [mathAnswer, setMathAnswer] = useState('');
  const [mathQuestion] = useState({ q: '9 × 6', a: 54 });
  const [gateMode, setGateMode] = useState('pin'); // 'pin' or 'math'

  if (!isOpen) return null;

  const handleSubmitPin = async (e) => {
    e.preventDefault();
    if (!pin) {
      setError('Please enter your 4-digit PIN');
      return;
    }
    try {
      setLoading(true);
      setError('');
      const res = await verifyParentPin(pin);
      if (res.verified) {
        onSuccess();
        onClose();
      } else {
        setError(res.message || 'Incorrect PIN. Default demo PIN is 1234.');
      }
    } catch (err) {
      if (pin === '1234') {
        onSuccess();
        onClose();
      } else {
        setError(err.message || 'Verification failed. Try default PIN: 1234');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyMath = (e) => {
    e.preventDefault();
    if (parseInt(mathAnswer.trim(), 10) === mathQuestion.a) {
      onSuccess();
      onClose();
    } else {
      setError(`Almost! ${mathQuestion.q} is ${mathQuestion.a}. Only parents can unlock this.`);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="kids-card" style={{ maxWidth: '420px', width: '100%', padding: '32px 28px', textAlign: 'center', position: 'relative' }}>
        
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '18px', right: '18px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
        >
          <X size={22} />
        </button>

        {/* Lock Icon Header */}
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(232, 90, 79, 0.15)',
          color: '#E85A4F',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px auto'
        }}>
          <Lock size={32} />
        </div>

        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '6px' }}>
          Parent Verification Gate
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '22px' }}>
          This area is for grown-ups. Enter your parent security PIN to continue.
        </p>

        {error && (
          <div style={{
            background: 'rgba(232, 90, 79, 0.1)',
            border: '1px solid #E85A4F',
            color: '#E85A4F',
            padding: '10px 14px',
            borderRadius: '14px',
            fontSize: '0.85rem',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            textAlign: 'left'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {gateMode === 'pin' ? (
          <form onSubmit={handleSubmitPin}>
            <div style={{ marginBottom: '20px' }}>
              <input
                type="password"
                maxLength={6}
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                placeholder="Enter 4-digit PIN"
                autoFocus
                style={{
                  fontSize: '1.6rem',
                  letterSpacing: '8px',
                  textAlign: 'center',
                  padding: '12px 16px',
                  borderRadius: '16px',
                  border: '2px solid #E2DED0',
                  width: '100%',
                  background: 'var(--bg-main)',
                  fontWeight: 800
                }}
              />
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                💡 Default Demo Parent PIN: <strong>1234</strong>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                type="submit"
                disabled={loading}
                className="kids-btn-fun"
                style={{ width: '100%', justifyContent: 'center' }}
              >
                {loading ? 'Verifying...' : 'Unlock Parent Hub 🔓'}
              </button>

              <button
                type="button"
                onClick={() => { setGateMode('math'); setError(''); }}
                style={{ background: 'none', border: 'none', color: '#2563EB', fontSize: '0.85rem', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Grown-up math challenge instead?
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleVerifyMath}>
            <div style={{ background: 'rgba(37, 99, 235, 0.08)', borderRadius: '16px', padding: '16px', marginBottom: '18px' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Adult Knowledge Check</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#2563EB' }}>
                What is {mathQuestion.q} = ?
              </div>
            </div>

            <input
              type="number"
              value={mathAnswer}
              onChange={(e) => setMathAnswer(e.target.value)}
              placeholder="Answer"
              autoFocus
              style={{
                fontSize: '1.3rem',
                textAlign: 'center',
                padding: '10px 14px',
                borderRadius: '14px',
                border: '2px solid #E2DED0',
                width: '100%',
                marginBottom: '16px'
              }}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                type="submit"
                className="kids-btn-fun"
                style={{ width: '100%', justifyContent: 'center' }}
              >
                Submit Answer 🚀
              </button>

              <button
                type="button"
                onClick={() => { setGateMode('pin'); setError(''); }}
                style={{ background: 'none', border: 'none', color: '#2563EB', fontSize: '0.85rem', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Use 4-digit PIN instead
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}
