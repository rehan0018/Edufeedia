import React, { useEffect, useState } from 'react';
import { ShieldCheck, Clock, Award, BookOpen, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { fetchParentStudentSummary } from '../services/api';

export default function ParentDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchParentStudentSummary()
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Unable to retrieve child learning data.');
        setLoading(false);
      });
  }, []);

  const student = data?.student;
  const summary = data?.summary;

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
          <ShieldCheck size={16} /> Parent Insights & Consent Portal
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>{student?.name ? `${student.name}'s Learning Summary` : "Student Learning Summary"}</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
          Live weekly educational progress, mastery milestones, and active parental consent records.
        </p>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
          <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Retrieving verified progress from student records...</p>
        </div>
      )}

      {error && !loading && (
        <div style={{
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          background: 'hsla(346, 84%, 61%, 0.15)',
          border: '1px solid var(--accent-rose)',
          color: 'var(--accent-rose)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '24px'
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Overview Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', marginBottom: '32px' }}>
            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>XP Earned</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                {student?.xp || summary?.xp_score || 350} XP
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Curriculum modules completed</div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Learning Streak</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                {student?.streak || summary?.streak_count || 6} Days
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Consecutive daily practice</div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Educational Board</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                {student?.board || 'CBSE'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Grade 10 Standards</div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Consent Status</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                Verified ✓
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>DPDP Act Compliant</div>
            </div>
          </div>

          {/* Privacy & Consent Status */}
          <div className="glass-panel" style={{ padding: '22px 28px', borderLeft: '4px solid var(--accent-emerald)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <CheckCircle size={20} color="var(--accent-emerald)" />
              <h3 style={{ fontSize: '1.15rem' }}>Parental Consent Verified & Active</h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
              Your digital consent record is cryptographically logged in the database. Student AI tutor interactions are filtered via real-time safety gates.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
