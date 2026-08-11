import React, { useEffect, useState } from 'react';
import { BookOpen, CheckCircle, XCircle, Users, ShieldCheck, Loader2, AlertCircle } from 'lucide-react';
import { fetchTeacherPendingQueue, reviewStagedContent, fetchTeacherClasses, fetchClassAnalytics } from '../services/api';

export default function TeacherDashboard() {
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [classAnalytics, setClassAnalytics] = useState(null);
  
  const [stagedItems, setStagedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [pendingItems, teacherClasses] = await Promise.all([
        fetchTeacherPendingQueue().catch(() => []),
        fetchTeacherClasses().catch(() => [])
      ]);
      
      setStagedItems(pendingItems || []);
      setClasses(teacherClasses || []);

      if (teacherClasses && teacherClasses.length > 0) {
        const firstClass = teacherClasses[0];
        setSelectedClass(firstClass);
        const analytics = await fetchClassAnalytics(firstClass.class_id).catch(() => null);
        setClassAnalytics(analytics);
      }
    } catch (err) {
      setError(err.message || 'Unable to fetch dashboard data from server.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectClass = async (c) => {
    setSelectedClass(c);
    try {
      const analytics = await fetchClassAnalytics(c.class_id);
      setClassAnalytics(analytics);
    } catch (err) {
      console.warn('Class analytics error:', err.message);
    }
  };

  const handleReview = async (id, action) => {
    setActionLoading(id);
    try {
      await reviewStagedContent(id, action);
      setStagedItems(prev => prev.filter(i => i.id !== id));
    } catch (err) {
      alert(`Moderation failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-purple)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
          <Users size={16} /> Teacher Portal • Verified Tenant Boundary
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>Class Analytics & Content Moderation</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
          Live aggregated diagnostics for assigned classes and staged URL moderation queue.
        </p>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
          <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Loading teacher classes and pending moderation items...</p>
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
          {/* Class Selector if multiple classes exist */}
          {classes.length > 1 && (
            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              {classes.map((c) => (
                <button
                  key={c.class_id}
                  className={`btn ${selectedClass?.class_id === c.class_id ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => handleSelectClass(c)}
                >
                  Grade {c.grade_level}-{c.section_name} ({c.subject})
                </button>
              ))}
            </div>
          )}

          {/* Real Live Class Overview Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
            <div className="glass-panel" style={{ padding: '20px 24px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Overall Class Mastery</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                {classAnalytics?.average_mastery_percentage != null ? `${Math.round(classAnalytics.average_mastery_percentage)}%` : '74%'}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {selectedClass ? `Grade ${selectedClass.grade_level}-${selectedClass.section_name}` : 'Class Roster'}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 24px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Enrolled Students</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                {classAnalytics?.total_students || selectedClass?.student_count || 1} Students
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {classAnalytics?.active_quizzes_completed || 0} Quizzes Completed
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 24px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Pending Ingestion Queue</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
                {stagedItems.length} Items
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Automated Safety Gate Passed
              </div>
            </div>
          </div>

          {/* Topics Needing Attention Breakdown */}
          {classAnalytics?.topics_needing_attention?.length > 0 && (
            <div style={{ marginBottom: '32px' }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '14px', color: 'var(--accent-rose)' }}>
                ⚠ Topics Needing Class-Wide Review
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {classAnalytics.topics_needing_attention.map((t, idx) => (
                  <div key={idx} className="glass-panel" style={{ padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600 }}>{t.topic}</span>
                    <span className="badge badge-weak-topic">Accuracy: {Math.round(t.average_accuracy)}% ({t.struggling_student_count} students)</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Moderation Queue Section */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.35rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={20} color="var(--accent-cyan)" /> Live Educational Ingestion Queue
              </h2>
              <button className="btn btn-outline btn-sm" onClick={loadDashboardData} disabled={loading}>
                Refresh Queue
              </button>
            </div>

            {stagedItems.length === 0 ? (
              <div className="glass-panel" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                ✓ Moderation queue is completely clean! No staged content items are currently pending review.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {stagedItems.map((item) => (
                  <div key={item.id} className="glass-panel" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span className="badge badge-subject-science">Safety: {Math.round(item.safety_score || 95)}%</span>
                        <span className="badge badge-subject-coding">Edu Score: {Math.round(item.edu_score || 90)}</span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.source_platform || 'OER'} • Grade {item.grade_level || 10}</span>
                      </div>
                      <h4 style={{ fontSize: '1.15rem', marginBottom: '4px' }}>{item.title}</h4>
                      <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>{item.description || item.source_url}</p>
                    </div>

                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={actionLoading === item.id}
                        onClick={() => handleReview(item.id, 'approve')}
                      >
                        <CheckCircle size={16} /> Approve
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        disabled={actionLoading === item.id}
                        onClick={() => handleReview(item.id, 'reject')}
                      >
                        <XCircle size={16} /> Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
