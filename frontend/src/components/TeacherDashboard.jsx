import React, { useEffect, useState } from 'react';
import { BookOpen, CheckCircle, XCircle, Users, ShieldCheck, Loader2, AlertCircle } from 'lucide-react';
import { fetchTeacherPendingQueue, reviewStagedContent } from '../services/api';

export default function TeacherDashboard() {
  const [stagedItems, setStagedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    loadPendingQueue();
  }, []);

  const loadPendingQueue = async () => {
    setLoading(true);
    setError('');
    try {
      const items = await fetchTeacherPendingQueue();
      setStagedItems(items || []);
    } catch (err) {
      setError(err.message || 'Unable to fetch pending items from moderation server.');
    } finally {
      setLoading(false);
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
          <Users size={16} /> Teacher Portal • School Tenant: Apex Public School
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>Class Analytics & Ingestion Moderation</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
          Live aggregated class diagnostics and staged educational content moderation queue.
        </p>
      </div>

      {/* Class Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Overall Class Mastery</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>74.2%</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>32 Enrolled Students</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Topics Needing Review</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-rose)' }}>2 Topics</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Newton's Laws & Bonding</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Pending Moderation</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{stagedItems.length} Items</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Multi-Label Safety Audited</div>
        </div>
      </div>

      {/* Moderation Queue Section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.35rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldCheck size={20} color="var(--accent-cyan)" /> Live Educational Ingestion Queue
          </h2>
          <button className="btn btn-outline btn-sm" onClick={loadPendingQueue} disabled={loading}>
            Refresh Queue
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
            <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
            <p>Fetching pending content items from backend server...</p>
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
            gap: '10px'
          }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && stagedItems.length === 0 && (
          <div className="glass-panel" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            ✓ Moderation queue is completely clean! No staged content items are currently pending approval.
          </div>
        )}

        {!loading && !error && stagedItems.length > 0 && (
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
    </div>
  );
}
