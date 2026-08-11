import React, { useEffect, useState } from 'react';
import { Trophy, AlertTriangle, RotateCcw, Sparkles, CheckCircle2, TrendingUp, Calendar } from 'lucide-react';
import { fetchMasteryAnalytics } from '../services/api';

export default function MasteryDashboard({ onStartRevision }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchMasteryAnalytics().then(setAnalytics);
  }, []);

  if (!analytics) return null;

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-amber)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
          <TrendingUp size={16} /> Educational Intelligence & Memory Retention
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>Curriculum Mastery & Spaced Revision</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', maxWidth: '600px' }}>
          Calculated dynamically from quiz diagnostic attempts and active recall intervals (SM-2 Algorithm).
        </p>
      </div>

      {/* Subject Mastery Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        {Object.entries(analytics.subject_mastery || {}).map(([subj, score], idx) => (
          <div key={idx} className="glass-panel" style={{ padding: '20px 24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{subj}</span>
              <span style={{ fontWeight: 800, color: score >= 80 ? 'var(--accent-emerald)' : 'var(--accent-cyan)' }}>{score}%</span>
            </div>
            <div className="progress-bar-track">
              <div
                className="progress-bar-fill"
                style={{
                  width: `${score}%`,
                  background: score >= 80 ? 'linear-gradient(90deg, var(--accent-emerald), var(--accent-cyan))' : 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))'
                }}
              ></div>
            </div>
            <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {score >= 80 ? '✓ Proficient mastery' : 'Targeted revision recommended'}
            </div>
          </div>
        ))}
      </div>

      {/* Weak Topics Diagnostic */}
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '1.35rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <AlertTriangle size={20} color="var(--accent-rose)" /> Topics Needing Targeted Practice
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {(analytics.weak_topics || []).map((t, idx) => (
            <div
              key={idx}
              className="glass-panel"
              style={{
                padding: '18px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderLeft: '4px solid var(--accent-rose)'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                  <span className="badge badge-weak-topic">Mastery: {t.mastery_score}%</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{t.subject}</span>
                </div>
                <h3 style={{ fontSize: '1.15rem' }}>{t.topic}</h3>
                <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                  Recent quiz accuracy indicates conceptual confusion. Revision scheduled for <strong>{t.next_revision_date}</strong>.
                </p>
              </div>

              <button className="btn btn-outline" onClick={() => onStartRevision(t.topic)}>
                Practice Now
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming Spaced Repetition Calendar */}
      <div>
        <h2 style={{ fontSize: '1.35rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <RotateCcw size={20} color="var(--accent-amber)" /> Upcoming Spaced Revision (Active Recall)
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {(analytics.upcoming_revisions || []).map((r, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: '18px 22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="badge badge-spaced-due">Scheduled: {r.scheduled_date}</span>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>SM-2 Interval: {r.interval_days}d</span>
              </div>
              <h4 style={{ fontSize: '1.1rem', marginBottom: '4px' }}>{r.topic}</h4>
              <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                Active recall review timed to prevent forgetting curves and lock concepts into long-term memory.
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
