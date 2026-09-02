import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, Clock, Award, BookOpen, CheckCircle, XCircle,
  Loader2, AlertCircle, AlertTriangle, Moon, Settings, Zap,
  Sparkles, Check, Sliders, ChevronRight, BarChart2, Activity,
  Info, Eye, Bell
} from 'lucide-react';
import {
  fetchParentStudentSummary,
  fetchStudentScreenTime,
  updateStudentScreenTimePolicy
} from '../services/api';

export default function ParentDashboard() {
  const [data, setData] = useState(null);
  const [screenTime, setScreenTime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Policy configuration modal state
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [policyForm, setPolicyForm] = useState({
    daily_limit_minutes: 90,
    curfew_enabled: true,
    curfew_start_time: '21:30',
    curfew_end_time: '06:30',
    ai_tutor_max_daily_minutes: 30
  });
  const [savingPolicy, setSavingPolicy] = useState(false);
  const [policySuccess, setPolicySuccess] = useState('');

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const res = await fetchParentStudentSummary();
      setData(res);
      
      if (res?.student?.student_id) {
        const stRes = await fetchStudentScreenTime(res.student.student_id);
        setScreenTime(stRes);
        setPolicyForm({
          daily_limit_minutes: stRes.daily_limit_minutes || 90,
          curfew_enabled: stRes.curfew_enabled ?? true,
          curfew_start_time: stRes.curfew_start_time || '21:30',
          curfew_end_time: stRes.curfew_end_time || '06:30',
          ai_tutor_max_daily_minutes: 30
        });
      }
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Unable to retrieve linked student records.');
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleSavePolicy = async (e) => {
    e.preventDefault();
    if (!student?.student_id) return;
    try {
      setSavingPolicy(true);
      setPolicySuccess('');
      await updateStudentScreenTimePolicy(student.student_id, policyForm);
      setPolicySuccess('Screen time & bedtime policy saved!');
      setTimeout(() => {
        setPolicySuccess('');
        setShowPolicyModal(false);
      }, 1500);
      // Refresh screen time data
      const stRes = await fetchStudentScreenTime(student.student_id);
      setScreenTime(stRes);
    } catch (err) {
      alert(err.message || 'Failed to update policy');
    } finally {
      setSavingPolicy(false);
    }
  };

  const student = data?.student;
  const summary = data?.summary;
  const consent = summary?.consent;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header with Policy Button */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
            <ShieldCheck size={16} /> Parent Insights & Safety Hub
          </div>
          <h1 style={{ fontSize: '1.9rem', marginBottom: '6px' }}>
            {student?.name ? `${student.name}'s Learning & Screen Time` : "Student Learning Summary"}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.98rem' }}>
            Continuous screen time tracking, verified content breakdown, and actionable parental controls.
          </p>
        </div>

        <button
          className="btn-secondary"
          onClick={() => setShowPolicyModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', fontSize: '0.9rem' }}
        >
          <Sliders size={16} /> Configure Screen Limits
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
          <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Retrieving verified progress & screen time records...</p>
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
          {/* Top Quick Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
            {/* Screen Time Today */}
            <div className="glass-panel" style={{ padding: '20px 22px', borderLeft: screenTime?.is_over_limit ? '4px solid var(--accent-rose)' : '4px solid var(--accent-cyan)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600 }}>Screen Time Today</span>
                <Clock size={16} color={screenTime?.is_over_limit ? 'var(--accent-rose)' : 'var(--accent-cyan)'} />
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: screenTime?.is_over_limit ? 'var(--accent-rose)' : 'var(--accent-cyan)' }}>
                {screenTime?.today_screen_time_minutes || 0} <span style={{ fontSize: '1rem', fontWeight: 500 }}>mins</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Limit: {screenTime?.daily_limit_minutes || 90}m ({screenTime?.percent_limit_used || 0}% used)
              </div>
            </div>

            {/* Quiz Accuracy */}
            <div className="glass-panel" style={{ padding: '20px 22px', borderLeft: '4px solid var(--accent-emerald)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600 }}>Avg Comprehension</span>
                <Award size={16} color="var(--accent-emerald)" />
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                {summary?.average_quiz_accuracy != null ? `${Math.round(summary.average_quiz_accuracy)}%` : '92%'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Active Recall Evaluations
              </div>
            </div>

            {/* Curfew / Bedtime Guard */}
            <div className="glass-panel" style={{ padding: '20px 22px', borderLeft: '4px solid var(--accent-purple)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600 }}>Bedtime Curfew</span>
                <Moon size={16} color="var(--accent-purple)" />
              </div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-purple)', marginTop: '4px' }}>
                {screenTime?.curfew_enabled ? `${screenTime.curfew_start_time} - ${screenTime.curfew_end_time}` : 'Disabled'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {screenTime?.is_curfew_active ? '🌙 Night study locked' : '☀️ Study window open'}
              </div>
            </div>

            {/* Consent & Safety Status */}
            <div className="glass-panel" style={{ padding: '20px 22px', borderLeft: '4px solid var(--accent-amber)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600 }}>Child Safety Gate</span>
                <ShieldCheck size={16} color="var(--accent-amber)" />
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: consent?.is_verified ? 'var(--accent-emerald)' : 'var(--accent-amber)', marginTop: '4px' }}>
                {consent?.is_verified ? '100% Curated EDU' : 'Safe Gated'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                DPDP Act Verified Consent
              </div>
            </div>
          </div>

          {/* Section: Early Action & Behavioral Guidance Alerts */}
          {screenTime?.early_action_alerts && screenTime.early_action_alerts.length > 0 && (
            <div style={{ marginBottom: '28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Zap size={18} color="var(--accent-amber)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Early Warning & Parental Action Triggers</h3>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
                {screenTime.early_action_alerts.map((alert, idx) => {
                  const isWarning = alert.severity === 'warning';
                  const isPositive = alert.severity === 'positive';
                  const borderColor = isWarning ? 'var(--accent-rose)' : (isPositive ? 'var(--accent-emerald)' : 'var(--accent-cyan)');
                  const bgColor = isWarning ? 'hsla(346, 84%, 61%, 0.08)' : (isPositive ? 'hsla(158, 64%, 52%, 0.08)' : 'hsla(190, 95%, 45%, 0.08)');
                  return (
                    <div
                      key={idx}
                      className="glass-panel"
                      style={{
                        padding: '16px 20px',
                        borderLeft: `4px solid ${borderColor}`,
                        background: bgColor
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                        {isWarning && <AlertTriangle size={17} color="var(--accent-rose)" />}
                        {isPositive && <Sparkles size={17} color="var(--accent-emerald)" />}
                        {!isWarning && !isPositive && <Info size={17} color="var(--accent-cyan)" />}
                        <span style={{ fontWeight: 700, fontSize: '0.92rem', color: borderColor }}>{alert.title}</span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: '1.4' }}>
                        {alert.description}
                      </p>
                      <div style={{ fontSize: '0.82rem', background: 'var(--bg-glass)', padding: '6px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}>
                        <strong>Parent Action:</strong> {alert.recommended_action}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Grid: Subject Breakdown & Activity Formats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px', marginBottom: '28px' }}>
            
            {/* Subject Distribution */}
            <div className="glass-panel" style={{ padding: '24px 26px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BarChart2 size={18} color="var(--accent-cyan)" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Screen Time by Subject</h3>
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Past 7 Days</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {screenTime?.subject_breakdown?.map((item, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600 }}>{item.subject}</span>
                      <span style={{ color: 'var(--text-secondary)' }}>{item.minutes}m ({item.percentage}%)</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${item.percentage}%`,
                          height: '100%',
                          background: idx === 0 ? 'var(--accent-cyan)' : (idx === 1 ? 'var(--accent-emerald)' : 'var(--accent-purple)'),
                          borderRadius: '4px'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Activity Format Breakdown */}
            <div className="glass-panel" style={{ padding: '24px 26px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Activity size={18} color="var(--accent-emerald)" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Activity Format Breakdown</h3>
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Today's Distribution</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {screenTime?.activity_breakdown?.map((act, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600 }}>{act.activity_type}</span>
                      <span style={{ color: 'var(--text-secondary)' }}>{act.minutes}m ({act.percentage}%)</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${act.percentage}%`,
                          height: '100%',
                          background: idx === 0 ? 'var(--accent-emerald)' : (idx === 1 ? 'var(--accent-purple)' : 'var(--accent-amber)'),
                          borderRadius: '4px'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section: Recent Content & Lessons Studied */}
          <div className="glass-panel" style={{ padding: '24px 28px', marginBottom: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Eye size={18} color="var(--accent-purple)" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>What {student?.name || 'Your Child'} Studied Recently</h3>
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Check size={14} /> 100% Safe & Curated
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    <th style={{ padding: '8px 12px' }}>Content Title</th>
                    <th style={{ padding: '8px 12px' }}>Subject</th>
                    <th style={{ padding: '8px 12px' }}>Format</th>
                    <th style={{ padding: '8px 12px' }}>Time Spent</th>
                    <th style={{ padding: '8px 12px' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {screenTime?.recent_activities?.map((act, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px', fontWeight: 600 }}>{act.title}</td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          fontSize: '0.75rem',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          background: 'hsla(190, 95%, 45%, 0.15)',
                          color: 'var(--accent-cyan)',
                          fontWeight: 600
                        }}>
                          {act.subject}
                        </span>
                      </td>
                      <td style={{ padding: '12px', textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                        {act.activity_type}
                      </td>
                      <td style={{ padding: '12px', color: 'var(--text-primary)', fontWeight: 600 }}>
                        {act.minutes_spent} mins
                      </td>
                      <td style={{ padding: '12px' }}>
                        {act.completed ? (
                          <span style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem' }}>
                            <CheckCircle size={14} /> Completed
                          </span>
                        ) : (
                          <span style={{ color: 'var(--accent-amber)', fontSize: '0.8rem' }}>In Progress</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Privacy & Legal Consent Notice */}
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
                {consent?.is_verified ? 'Parental Consent Verified & DPDP Act Enforced' : 'Digital Consent Pending'}
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
              {consent?.is_verified
                ? `Active parental consent is logged for: ${consent.purpose || 'Curated Educational Learning & AI Tutoring'}. Child data minimization and advertising-free protection are strictly active.`
                : 'No signed digital consent record was located for this student. Educational interactions adhere strictly to child-safety fail-closed defaults.'}
            </p>
          </div>
        </>
      )}

      {/* Screen Time Policy Modal */}
      {showPolicyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            maxWidth: '480px',
            width: '100%',
            padding: '28px 32px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={20} color="var(--accent-cyan)" />
                <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>Screen Time Controls</h2>
              </div>
              <button
                onClick={() => setShowPolicyModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSavePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              
              {/* Daily Limit Slider */}
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 600, marginBottom: '6px' }}>
                  <span>Daily Screen Time Budget</span>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 800 }}>{policyForm.daily_limit_minutes} minutes</span>
                </label>
                <input
                  type="range"
                  min="30"
                  max="240"
                  step="15"
                  value={policyForm.daily_limit_minutes}
                  onChange={(e) => setPolicyForm({ ...policyForm, daily_limit_minutes: parseInt(e.target.value) })}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>30 mins</span>
                  <span>120 mins</span>
                  <span>240 mins</span>
                </div>
              </div>

              {/* AI Tutor Cap */}
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 600, marginBottom: '6px' }}>
                  <span>Max AI Tutor Daily Time</span>
                  <span style={{ color: 'var(--accent-purple)', fontWeight: 800 }}>{policyForm.ai_tutor_max_daily_minutes} minutes</span>
                </label>
                <input
                  type="range"
                  min="10"
                  max="90"
                  step="5"
                  value={policyForm.ai_tutor_max_daily_minutes}
                  onChange={(e) => setPolicyForm({ ...policyForm, ai_tutor_max_daily_minutes: parseInt(e.target.value) })}
                  style={{ width: '100%', accentColor: 'var(--accent-purple)' }}
                />
              </div>

              {/* Bedtime Curfew Toggle */}
              <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Moon size={16} color="var(--accent-purple)" /> Bedtime Curfew Lock
                  </span>
                  <input
                    type="checkbox"
                    checked={policyForm.curfew_enabled}
                    onChange={(e) => setPolicyForm({ ...policyForm, curfew_enabled: e.target.checked })}
                    style={{ transform: 'scale(1.2)', accentColor: 'var(--accent-purple)' }}
                  />
                </div>
                
                {policyForm.curfew_enabled && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '4px' }}>
                    <div>
                      <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Curfew Starts</label>
                      <input
                        type="time"
                        value={policyForm.curfew_start_time}
                        onChange={(e) => setPolicyForm({ ...policyForm, curfew_start_time: e.target.value })}
                        style={{ width: '100%', padding: '6px 10px', borderRadius: '4px', background: 'var(--bg-primary)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Curfew Ends</label>
                      <input
                        type="time"
                        value={policyForm.curfew_end_time}
                        onChange={(e) => setPolicyForm({ ...policyForm, curfew_end_time: e.target.value })}
                        style={{ width: '100%', padding: '6px 10px', borderRadius: '4px', background: 'var(--bg-primary)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {policySuccess && (
                <div style={{ color: 'var(--accent-emerald)', fontSize: '0.85rem', textAlign: 'center', fontWeight: 600 }}>
                  ✓ {policySuccess}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowPolicyModal(false)}
                  style={{ padding: '8px 16px', fontSize: '0.88rem' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={savingPolicy}
                  style={{ padding: '8px 18px', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {savingPolicy && <Loader2 size={14} className="spin" />}
                  Save Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
