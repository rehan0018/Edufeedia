import React from 'react';
import { ShieldCheck, Clock, Award, BookOpen, CheckCircle } from 'lucide-react';

export default function ParentDashboard() {
  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
          <ShieldCheck size={16} /> Parent Insights & Consent Management
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>Rahul's Learning Summary</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
          High-level weekly educational milestones, mastery progress, and privacy consent status.
        </p>
      </div>

      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Weekly Learning Time</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>4h 20m</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Distraction-free focus</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Quiz Accuracy Average</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>82%</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Bloom's recall & apply</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Topics Mastered</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-purple)' }}>12 Topics</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Grade 10 Curriculum</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Active Revisions</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>2 Topics</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Scheduled for review</div>
        </div>
      </div>

      {/* Privacy & Consent Status */}
      <div className="glass-panel" style={{ padding: '22px 28px', borderLeft: '4px solid var(--accent-emerald)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <CheckCircle size={20} color="var(--accent-emerald)" />
          <h3 style={{ fontSize: '1.15rem' }}>Parental Consent Verified</h3>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
          Your digital consent record is active and cryptographically signed. Student private conversations are protected under child privacy guidelines.
        </p>
      </div>
    </div>
  );
}
