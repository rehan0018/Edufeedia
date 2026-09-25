import React from 'react';
import {
  Sparkles, BookOpen, Brain, Trophy, LogOut, Flame, Zap,
  ShieldCheck, Sun, Moon, Lock, Star, Heart, ArrowLeft,
  GraduationCap, Users, LayoutDashboard
} from 'lucide-react';

export default function Navbar({
  currentTab,
  setTab,
  user,
  onLogout,
  theme,
  toggleTheme,
  experienceMode = 'student',
  onSwitchExperience,
  activeChild,
  onOpenParentGate
}) {
  const isStudent = user?.role === 'student';
  const isTeacher = user?.role === 'teacher' || user?.role === 'school_admin';
  const isParent = user?.role === 'parent';

  // If in Kids Mode (0–10 years): Render child-safe cartoon header
  if (experienceMode === 'kids') {
    return (
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 24px',
        background: '#FFFFFF',
        borderBottom: '3px solid #EAF3FF',
        boxShadow: '0 4px 16px rgba(37, 99, 235, 0.08)'
      }}>
        {/* Kids Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #FF7A59, #FFD166)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(255, 122, 89, 0.3)'
          }}>
            <Sparkles size={22} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, fontFamily: 'var(--font-heading)', color: '#2563EB', lineHeight: 1.1 }}>
              Edu<span style={{ color: '#FF7A59' }}>Kids</span> 🎈
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', fontWeight: 700 }}>
              Safe & Fun Learning World
            </div>
          </div>
        </div>

        {/* Center: Active Child Companion Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: '#EAF3FF',
          padding: '6px 16px',
          borderRadius: '999px',
          border: '2px solid rgba(37, 99, 235, 0.15)'
        }}>
          <span style={{ fontSize: '1.4rem' }}>
            {activeChild?.avatar_mascot === 'unicorn' ? '🦄' : (activeChild?.avatar_mascot === 'owl' ? '🦉' : '🦁')}
          </span>
          <div>
            <span style={{ fontWeight: 800, fontSize: '0.92rem', color: '#172033' }}>
              {activeChild?.name || 'Aarav'}
            </span>
            <span style={{ fontSize: '0.75rem', color: '#2563EB', fontWeight: 700, marginLeft: '6px' }}>
              (Age {activeChild?.age || 7})
            </span>
          </div>
        </div>

        {/* Right: Curiosity Stars + Parent Exit Gate */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Star Counter */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: '#FFFBEB',
            border: '2px solid #FFD166',
            padding: '6px 14px',
            borderRadius: '999px',
            fontWeight: 800,
            fontSize: '0.9rem',
            color: '#D97706'
          }}>
            <Star size={18} fill="#FFD166" color="#FFD166" />
            <span>{activeChild?.stars_count || 24} Stars</span>
          </div>

          {/* Theme Toggle */}
          <button
            className="btn btn-outline btn-sm"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            style={{ padding: '6px 10px', borderRadius: '12px', borderColor: '#E2E8F0' }}
          >
            {theme === 'dark' ? <Sun size={16} color="#FF7A59" /> : <Moon size={16} color="#2563EB" />}
          </button>

          {/* Parent Gate Exit Button */}
          <button
            onClick={onOpenParentGate}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '999px',
              background: '#F1F5F9',
              border: '1px solid #CBD5E1',
              color: '#475569',
              fontWeight: 800,
              fontSize: '0.84rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            title="Parents Only: Exit Kids Mode"
          >
            <Lock size={14} color="#64748B" />
            <span>Parents Exit</span>
          </button>
        </div>
      </header>
    );
  }

  // Standard Header for Student, Parent & Teacher modes
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 28px',
      background: 'var(--bg-card)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
      boxShadow: 'var(--shadow-sm)',
      transition: 'background var(--transition-smooth), border-color var(--transition-smooth)'
    }}>
      {/* Brand Logo & Mode Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
          onClick={() => {
            if (isTeacher) setTab('teacher');
            else if (isParent) {
              onSwitchExperience && onSwitchExperience('parent');
              setTab('parent');
            } else {
              onSwitchExperience && onSwitchExperience('student');
              setTab('feed');
            }
          }}
        >
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'var(--gradient-hero)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(232, 90, 79, 0.25)'
          }}>
            <Sparkles size={20} color="#FFFFFF" />
          </div>
          <span style={{
            fontSize: '1.35rem',
            fontWeight: 800,
            fontFamily: 'var(--font-heading)',
            letterSpacing: '-0.03em',
            color: 'var(--text-primary)'
          }}>
            Edu<span style={{ color: 'var(--brand-primary)' }}>feedia</span>
          </span>
        </div>

        {/* Unified Experience Selector (Kids 👶 | Student 🧑‍🎓 | Parent 👨‍👩‍👧) */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-soft-blue)',
          padding: '4px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border-subtle)',
          gap: '4px'
        }}>
          <button
            onClick={() => onSwitchExperience && onSwitchExperience('kids')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 800,
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: experienceMode === 'kids' ? '#FF7A59' : 'transparent',
              color: experienceMode === 'kids' ? '#FFFFFF' : 'var(--text-secondary)',
              transition: 'all 0.2s'
            }}
          >
            👶 Kids Mode (0–10)
          </button>

          <button
            onClick={() => {
              onSwitchExperience && onSwitchExperience('student');
              setTab('feed');
            }}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 800,
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: experienceMode === 'student' ? 'var(--brand-primary)' : 'transparent',
              color: experienceMode === 'student' ? '#FFFFFF' : 'var(--text-secondary)',
              transition: 'all 0.2s'
            }}
          >
            🧑‍🎓 Student (11–17)
          </button>

          <button
            onClick={() => {
              onSwitchExperience && onSwitchExperience('parent');
              setTab('parent');
            }}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 800,
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: experienceMode === 'parent' ? 'var(--accent-mint)' : 'transparent',
              color: experienceMode === 'parent' ? '#FFFFFF' : 'var(--text-secondary)',
              transition: 'all 0.2s'
            }}
          >
            👨‍👩‍👧 Parent Hub
          </button>
        </div>
      </div>

      {/* Center Navigation Tabs (When in Student Mode) */}
      {experienceMode === 'student' && (
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className={`btn ${currentTab === 'feed' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setTab('feed')}
            style={{ padding: '7px 12px', fontSize: '0.84rem' }}
          >
            <Sparkles size={14} /> Today's Plan
          </button>

          <button
            className={`btn ${currentTab === 'explore' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setTab('explore')}
            style={{ padding: '7px 12px', fontSize: '0.84rem' }}
          >
            <BookOpen size={14} /> Explore
          </button>

          <button
            className={`btn ${currentTab === 'tutor' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setTab('tutor')}
            style={{ padding: '7px 12px', fontSize: '0.84rem' }}
          >
            <Brain size={14} /> AI Tutor
          </button>

          <button
            className={`btn ${currentTab === 'challenges' ? 'btn-fun' : 'btn-outline'}`}
            onClick={() => setTab('challenges')}
            style={{ padding: '7px 12px', fontSize: '0.84rem' }}
          >
            <Trophy size={14} /> Challenges
          </button>

          <button
            className={`btn ${currentTab === 'mastery' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setTab('mastery')}
            style={{ padding: '7px 12px', fontSize: '0.84rem' }}
          >
            <Zap size={14} /> Mastery
          </button>
        </nav>
      )}

      {/* Center Navigation (Teacher Mode) */}
      {experienceMode === 'teacher' && (
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-primary"
            onClick={() => setTab('teacher')}
            style={{ padding: '7px 14px', fontSize: '0.84rem' }}
          >
            <BookOpen size={15} /> Class Analytics & Moderation
          </button>
        </nav>
      )}

      {/* User Info, Gamification Badges, Theme Toggle, & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {experienceMode === 'student' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Streak */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '5px 10px',
              background: 'rgba(255, 209, 102, 0.2)',
              border: '1px solid var(--accent-yellow)',
              borderRadius: 'var(--radius-full)',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              fontWeight: 700
            }}>
              <Flame size={15} color="#D97706" />
              <span>6 Days</span>
            </div>

            {/* XP */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '5px 10px',
              background: 'rgba(255, 122, 89, 0.15)',
              border: '1px solid rgba(255, 122, 89, 0.35)',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.82rem',
              fontWeight: 700
            }}>
              <Zap size={15} color="var(--accent-coral)" />
              <span style={{ color: 'var(--accent-coral)' }}>{user?.xp_score ?? 420} XP</span>
            </div>
          </div>
        )}

        {/* User Role Card */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          background: 'var(--bg-soft-blue)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.85rem'
        }}>
          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{user?.first_name || 'User'}</span>
          <span style={{
            fontSize: '0.7rem',
            padding: '2px 6px',
            borderRadius: '4px',
            background: 'var(--brand-primary)',
            color: '#FFFFFF',
            fontWeight: 800,
            textTransform: 'uppercase'
          }}>
            {user?.role || 'student'}
          </span>
        </div>

        {/* Theme Toggle (Light / Dark) */}
        <button
          className="btn btn-outline btn-sm"
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          style={{ padding: '6px 10px', borderRadius: 'var(--radius-md)' }}
        >
          {theme === 'dark' ? (
            <Sun size={16} color="var(--accent-coral)" />
          ) : (
            <Moon size={16} color="var(--brand-primary)" />
          )}
        </button>

        {/* Logout */}
        <button className="btn btn-outline btn-sm" onClick={onLogout} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
