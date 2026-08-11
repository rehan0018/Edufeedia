import React from 'react';
import { Sparkles, BookOpen, Brain, Trophy, LogOut, Flame, Zap, ShieldCheck } from 'lucide-react';

export default function Navbar({ currentTab, setTab, user, onLogout }) {
  const isStudent = user?.role === 'student';
  const isTeacher = user?.role === 'teacher' || user?.role === 'school_admin';
  const isParent = user?.role === 'parent';

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '14px 28px',
      background: 'hsla(222, 47%, 9%, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
    }}>
      {/* Brand Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => setTab(isStudent ? 'feed' : isTeacher ? 'teacher' : 'parent')}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'var(--shadow-glow-cyan)'
        }}>
          <Sparkles size={20} color="#0a0f1d" />
        </div>
        <span style={{ fontSize: '1.35rem', fontWeight: 800, fontFamily: 'var(--font-heading)', letterSpacing: '-0.03em' }}>
          Edu<span style={{ color: 'var(--accent-cyan)' }}>feedia</span>
        </span>
      </div>

      {/* Navigation Tabs (Strictly Role Separated) */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {isStudent && (
          <>
            <button
              className={`btn ${currentTab === 'feed' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setTab('feed')}
              style={{ padding: '8px 16px', fontSize: '0.88rem' }}
            >
              <Sparkles size={16} /> Today's Plan
            </button>

            <button
              className={`btn ${currentTab === 'tutor' ? 'btn-accent' : 'btn-outline'}`}
              onClick={() => setTab('tutor')}
              style={{ padding: '8px 16px', fontSize: '0.88rem' }}
            >
              <Brain size={16} /> AI Tutor
            </button>

            <button
              className={`btn ${currentTab === 'mastery' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setTab('mastery')}
              style={{ padding: '8px 16px', fontSize: '0.88rem' }}
            >
              <Trophy size={16} /> Mastery & Revision
            </button>
          </>
        )}

        {isTeacher && (
          <button
            className={`btn ${currentTab === 'teacher' ? 'btn-accent' : 'btn-outline'}`}
            onClick={() => setTab('teacher')}
            style={{ padding: '8px 16px', fontSize: '0.88rem' }}
          >
            <BookOpen size={16} /> Class Analytics & Moderation
          </button>
        )}

        {isParent && (
          <button
            className={`btn ${currentTab === 'parent' ? 'btn-accent' : 'btn-outline'}`}
            onClick={() => setTab('parent')}
            style={{ padding: '8px 16px', fontSize: '0.88rem' }}
          >
            <ShieldCheck size={16} /> Child Learning Summary
          </button>
        )}
      </nav>

      {/* User Info, Gamification Badges, & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {isStudent && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: 'hsla(43, 96%, 56%, 0.12)',
              border: '1px solid hsla(43, 96%, 56%, 0.3)',
              borderRadius: 'var(--radius-full)',
              color: 'var(--accent-amber)',
              fontSize: '0.85rem',
              fontWeight: 700
            }}>
              <Flame size={16} /> 6 Days
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: 'hsla(188, 95%, 53%, 0.12)',
              border: '1px solid hsla(188, 95%, 53%, 0.3)',
              borderRadius: 'var(--radius-full)',
              color: 'var(--accent-cyan)',
              fontSize: '0.85rem',
              fontWeight: 700
            }}>
              <Zap size={16} /> {user?.xp_score || 350} XP
            </div>
          </div>
        )}

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          background: 'var(--bg-card-solid)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.88rem'
        }}>
          <span style={{ fontWeight: 600 }}>{user?.first_name || 'Guest'}</span>
          <span style={{
            fontSize: '0.72rem',
            padding: '2px 6px',
            borderRadius: '4px',
            background: 'var(--accent-purple)',
            color: 'white',
            fontWeight: 700,
            textTransform: 'uppercase'
          }}>
            {user?.role || 'Student'}
          </span>
        </div>

        <button className="btn btn-outline btn-sm" onClick={onLogout} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
