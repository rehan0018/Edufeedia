import React, { useState } from 'react';
import {
  Compass, Sparkles, BookOpen, Brain, Trophy, LogOut, Flame, Zap,
  ShieldCheck, Sun, Moon, Lock, Star, Heart, ArrowLeft,
  GraduationCap, Users, LayoutDashboard, Menu, X
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isStudent = user?.role === 'student';
  const isTeacher = user?.role === 'teacher' || user?.role === 'school_admin';
  const isParent = user?.role === 'parent';

  const streakDays = user?.student_profile?.streak_count || user?.streak_count || 1;
  const xpScore = user?.xp_score ?? user?.student_profile?.total_xp ?? 0;

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

      {/* Center Navigation Tabs (When in Student Mode - Desktop) */}
      {experienceMode === 'student' && (
        <nav className="nav-desktop-tabs" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className={`btn ${currentTab === 'navigator' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setTab('navigator')}
            style={{ padding: '7px 12px', fontSize: '0.84rem' }}
          >
            <Compass size={14} /> Navigator
          </button>

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

      {/* Center Navigation (Teacher Mode - Desktop) */}
      {experienceMode === 'teacher' && (
        <nav className="nav-desktop-tabs" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-primary"
            onClick={() => setTab('teacher')}
            style={{ padding: '7px 14px', fontSize: '0.84rem' }}
          >
            <BookOpen size={15} /> Class Analytics & Moderation
          </button>
        </nav>
      )}

      {/* User Info, Gamification Badges, Theme Toggle, Mobile Hamburger & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {experienceMode === 'student' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Dynamic Streak */}
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
              <span>{streakDays} Day{streakDays === 1 ? '' : 's'}</span>
            </div>

            {/* Dynamic XP */}
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
              <span style={{ color: 'var(--accent-coral)' }}>{xpScore} XP</span>
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

        {/* Mobile Navigation Toggle Button */}
        <button
          className="btn btn-outline btn-sm mobile-menu-btn"
          onClick={() => setMobileMenuOpen(prev => !prev)}
          aria-label="Toggle Navigation Menu"
          aria-expanded={mobileMenuOpen}
          style={{ padding: '6px 10px' }}
        >
          {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        {/* Logout */}
        <button className="btn btn-outline btn-sm" onClick={onLogout} title="Logout">
          <LogOut size={16} />
        </button>
      </div>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="mobile-nav-drawer"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            background: 'var(--bg-card-solid, var(--bg-card))',
            borderBottom: '2px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-lg)',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            zIndex: 99
          }}
        >
          {experienceMode === 'student' && (
            <>
              <button
                className={`btn ${currentTab === 'navigator' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setTab('navigator'); setMobileMenuOpen(false); }}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Compass size={16} /> Navigator
              </button>
              <button
                className={`btn ${currentTab === 'feed' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setTab('feed'); setMobileMenuOpen(false); }}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Sparkles size={16} /> Today's Plan
              </button>
              <button
                className={`btn ${currentTab === 'explore' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setTab('explore'); setMobileMenuOpen(false); }}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <BookOpen size={16} /> Explore
              </button>
              <button
                className={`btn ${currentTab === 'tutor' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setTab('tutor'); setMobileMenuOpen(false); }}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Brain size={16} /> AI Tutor
              </button>
              <button
                className={`btn ${currentTab === 'challenges' ? 'btn-fun' : 'btn-outline'}`}
                onClick={() => { setTab('challenges'); setMobileMenuOpen(false); }}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Trophy size={16} /> Challenges
              </button>
              <button
                className={`btn ${currentTab === 'mastery' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setTab('mastery'); setMobileMenuOpen(false); }}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Zap size={16} /> Mastery
              </button>
            </>
          )}

          {experienceMode === 'teacher' && (
            <button
              className="btn btn-primary"
              onClick={() => { setTab('teacher'); setMobileMenuOpen(false); }}
              style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
            >
              <BookOpen size={16} /> Class Analytics & Moderation
            </button>
          )}
        </div>
      )}
    </header>
  );
}
