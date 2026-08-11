import React, { useState } from 'react';
import { BookOpen, CheckCircle, XCircle, Users, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function TeacherDashboard() {
  const [stagedItems, setStagedItems] = useState([
    { id: 'stg-1', title: "Newton's Laws of Motion - MIT OpenCourseWare", platform: 'OER', safety: 96, edu: 92, grade: 10, status: 'pending' },
    { id: 'stg-2', title: 'Quadratic Equations & Roots - Khan Academy', platform: 'Khan Academy', safety: 98, edu: 95, grade: 10, status: 'pending' },
    { id: 'stg-3', title: 'Cellular Respiration Animation - PhET Simulation', platform: 'PhET', safety: 99, edu: 94, grade: 10, status: 'pending' }
  ]);

  const handleApprove = (id) => {
    setStagedItems(prev => prev.filter(i => i.id !== id));
  };

  const handleReject = (id) => {
    setStagedItems(prev => prev.filter(i => i.id !== id));
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-purple)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
          <Users size={16} /> Teacher Portal • School Tenant: Apex Public School
        </div>
        <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>Class 10-A Analytics & Content Moderation</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
          Aggregated class performance diagnostics and staged URL ingestion moderation queue.
        </p>
      </div>

      {/* Class Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Overall Class Mastery</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>74.2%</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>32 Active Students</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Topics Needing Class Review</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-rose)' }}>2 Topics</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Newton's Laws (54%), Bonding (51%)</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Moderation Staging Queue</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{stagedItems.length} Pending</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Safety Gate: 100% Passed</div>
        </div>
      </div>

      {/* Moderation Queue */}
      <div>
        <h2 style={{ fontSize: '1.35rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={20} color="var(--accent-cyan)" /> Staged Educational URLs Awaiting Approval
        </h2>

        {stagedItems.length === 0 ? (
          <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            ✓ Moderation queue is clear! All staged educational resources have been reviewed.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {stagedItems.map((item) => (
              <div key={item.id} className="glass-panel" style={{ padding: '18px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="badge badge-subject-science">Safety: {item.safety}%</span>
                    <span className="badge badge-subject-coding">Edu Score: {item.edu}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.platform} • Grade {item.grade}</span>
                  </div>
                  <h4 style={{ fontSize: '1.1rem' }}>{item.title}</h4>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button className="btn btn-primary btn-sm" onClick={() => handleApprove(item.id)}>
                    <CheckCircle size={16} /> Approve
                  </button>
                  <button className="btn btn-outline btn-sm" onClick={() => handleReject(item.id)}>
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
