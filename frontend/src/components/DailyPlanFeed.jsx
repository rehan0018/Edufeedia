import React from 'react';
import { Play, Sparkles, CheckCircle2, Clock, Brain, Flame, Target, BookOpen, RotateCcw, AlertTriangle } from 'lucide-react';

export default function DailyPlanFeed({ dailyPlan, onSelectLesson, onOpenQuiz, onOpenTutor }) {
  const items = dailyPlan?.items || [];
  const completedCount = items.filter(i => i.is_completed).length;
  const progressPct = items.length > 0 ? Math.round((completedCount / items.length) * 100) : 0;

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Hero Welcome Banner */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--accent-cyan)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
              <Sparkles size={16} /> Curated Curriculum • Grade 10 CBSE
            </div>
            <h1 style={{ fontSize: '2.2rem', marginBottom: '6px' }}>{dailyPlan?.greeting || 'Good morning, Rahul! 👋'}</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '560px' }}>
              Your distraction-free daily syllabus. Focused, verified, and personalized to your learning pace.
            </p>
          </div>

          <div style={{
            background: 'hsla(222, 40%, 10%, 0.8)',
            padding: '16px 24px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            minWidth: '220px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.88rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Today's Progress</span>
              <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{progressPct}%</span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${progressPct}%` }}></div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              <span>{completedCount} of {items.length} completed</span>
              <span>+60 XP earned</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.45rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Target size={22} color="var(--accent-cyan)" /> Today's Learning Plan
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            High-yield lessons scheduled from your diagnostic quiz results and retention intervals.
          </p>
        </div>

        <button className="btn btn-accent btn-sm" onClick={onOpenQuiz}>
          <Brain size={16} /> Take Daily Quiz (5 Q)
        </button>
      </div>

      {/* Learning Cards Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {items.map((item, idx) => {
          const isSpaced = item.explanation?.candidate_source === 'spaced_repetition';
          const isWeak = item.topic === "Newton's Laws" || item.topic === "Chemical Bonding";

          return (
            <div
              key={item.id || idx}
              className="glass-panel"
              style={{
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '20px',
                borderLeft: isSpaced ? '4px solid var(--accent-amber)' : isWeak ? '4px solid var(--accent-rose)' : '4px solid var(--accent-cyan)',
                cursor: 'pointer'
              }}
              onClick={() => onSelectLesson(item)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flex: 1 }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: 'var(--bg-card-solid)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.1rem',
                  fontWeight: 800,
                  color: isSpaced ? 'var(--accent-amber)' : 'var(--accent-cyan)'
                }}>
                  {idx + 1}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px', flexWrap: 'wrap' }}>
                    <span className={`badge ${
                      item.subject === 'Science' ? 'badge-subject-science' :
                      item.subject === 'Mathematics' ? 'badge-subject-math' : 'badge-subject-coding'
                    }`}>
                      {item.subject}
                    </span>

                    {isSpaced && (
                      <span className="badge badge-spaced-due">
                        <RotateCcw size={12} /> Spaced Review Due
                      </span>
                    )}

                    {isWeak && !isSpaced && (
                      <span className="badge badge-weak-topic">
                        <AlertTriangle size={12} /> Targeted Practice
                      </span>
                    )}

                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={14} /> ~{item.duration_minutes || 15} min
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.15rem', marginBottom: '4px' }}>{item.title}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: '1.4' }}>
                    {item.description}
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button
                  className="btn btn-primary"
                  style={{ padding: '10px 18px', whiteSpace: 'nowrap' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectLesson(item);
                  }}
                >
                  <Play size={16} fill="currentColor" /> {isSpaced ? 'Revise' : 'Start'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
