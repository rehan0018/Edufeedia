import React, { useState } from 'react';
import { X, CheckCircle2, Brain, Sparkles, AlertTriangle, Loader2 } from 'lucide-react';
import { recordLessonProgress } from '../services/api';

export default function ContentPlayerModal({ lesson, onClose, onCompleteAndQuiz, onOpenTutor }) {
  const [submitting, setSubmitting] = useState(false);

  if (!lesson) return null;

  const handleComplete = async () => {
    setSubmitting(true);
    try {
      await recordLessonProgress(lesson.id, 100);
    } catch (err) {
      console.warn('Progress log warning:', err.message);
    } finally {
      setSubmitting(false);
      onCompleteAndQuiz(lesson);
    }
  };

  const embedSrc = lesson.embed_code?.match(/src="([^"]+)"/)?.[1] || (
    lesson.source_url?.includes('youtube.com/watch?v=') 
      ? `https://www.youtube-nocookie.com/embed/${lesson.source_url.split('v=')[1]?.split('&')[0]}`
      : null
  );

  return (
    <div className="modal-overlay">
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '860px',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '28px',
        background: 'var(--bg-card-solid)',
        border: '1px solid var(--border-glow)'
      }}>
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-subject-science">{lesson.subject}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Grade {lesson.grade_level || 10} • {lesson.topic}
              </span>
            </div>
            <h2 style={{ fontSize: '1.45rem' }}>{lesson.title}</h2>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose} style={{ padding: '6px' }}>
            <X size={20} />
          </button>
        </div>

        {/* Video Embed Player or Safe Player Card */}
        {embedSrc ? (
          <div style={{
            position: 'relative',
            paddingBottom: '56.25%',
            height: 0,
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            background: '#000',
            marginBottom: '20px',
            boxShadow: 'var(--shadow-md)'
          }}>
            <iframe
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 0 }}
              src={embedSrc}
              title={lesson.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
        ) : (
          <div style={{
            padding: '36px 24px',
            textAlign: 'center',
            background: 'var(--bg-space)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            marginBottom: '20px'
          }}>
            <Sparkles size={36} color="var(--accent-cyan)" style={{ margin: '0 auto 12px auto' }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: '6px' }}>Interactive Curriculum Notes & Lesson Module</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto' }}>
              Review the conceptual summary and formula takeaways below before proceeding to the Bloom's taxonomy assessment quiz.
            </p>
          </div>
        )}

        {/* Pedagogical Summary & Key Notes */}
        <div style={{
          background: 'hsla(222, 40%, 10%, 0.8)',
          padding: '18px 22px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '24px'
        }}>
          <h4 style={{ fontSize: '1.05rem', color: 'var(--accent-cyan)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} /> Key Learning Takeaways
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: '1.5' }}>
            {lesson.description || 'Focus on understanding the foundational principles, definitions, and real-world formula applications for this module.'}
          </p>
        </div>

        {/* Action Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <button className="btn btn-accent" onClick={() => onOpenTutor(lesson.topic)}>
            <Brain size={18} /> Ask Socratic AI Tutor
          </button>

          <button
            className="btn btn-primary"
            disabled={submitting}
            style={{ padding: '12px 24px', fontSize: '1rem' }}
            onClick={handleComplete}
          >
            {submitting ? <Loader2 size={18} className="spin" /> : <CheckCircle2 size={18} />} Complete & Take Quiz
          </button>
        </div>
      </div>
    </div>
  );
}
