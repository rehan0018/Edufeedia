import React, { useEffect, useState } from 'react';
import { ShieldCheck, Clock, Award, BookOpen, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react';
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
        setError(err.message || 'Unable to retrieve linked student records.');
        setLoading(false);
      });
  }, []);

  const student = data?.student;
  const summary = data?.summary;
  const consent = summary?.consent;

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
          <ShieldCheck size={16} /> Parent Insights & Consent Portal
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>
          {student?.name ? `${student.name}'s Learning Summary` : "Student Learning Summary"}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
          Live weekly educational progress, mastery milestones, and active parental consent records.
        </p>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
          <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Retrieving verified progress from student database...</p>
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
                {summary?.xp != null ? summary.xp : (student?.xp || 0)} XP
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {summary?.total_lessons_completed || 0} Lessons Completed
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Quiz Accuracy Average</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                {summary?.average_quiz_accuracy != null ? `${Math.round(summary.average_quiz_accuracy)}%` : 'N/A'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Bloom's Taxonomy Evaluations
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Learning Streak</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                {summary?.streak != null ? summary.streak : (student?.streak || 0)} Days
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Consecutive Study Days
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 22px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '4px' }}>Consent Status</div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: consent?.is_verified ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                {consent?.is_verified ? 'Verified ✓' : 'Pending Review'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                DPDP Act Compliance
              </div>
            </div>
          </div>

          {/* Dynamic Privacy & Consent Record */}
          <div className="glass-panel" style={{
            padding: '22px 28px',
            borderLeft: consent?.is_verified ? '4px solid var(--accent-emerald)' : '4px solid var(--accent-amber)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              {consent?.is_verified ? (
                <CheckCircle size={20} color="var(--accent-emerald)" />
              ) : (
                <XCircle size={20} color="var(--accent-amber)" />
              )}
              <h3 style={{ fontSize: '1.15rem' }}>
                {consent?.is_verified ? 'Parental Consent Verified & Active' : 'Digital Consent Pending'}
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
              {consent?.is_verified
                ? `Active parental consent is logged for: ${consent.purpose || 'Curated Educational Learning & AI Tutoring'}. Child privacy boundaries are actively enforced.`
                : 'No signed digital consent record was located for this student. Educational interactions will adhere to strict child-safety defaults.'}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
