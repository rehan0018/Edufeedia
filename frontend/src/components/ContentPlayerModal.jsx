import React, { useState, useEffect, useRef } from 'react';
import { X, CheckCircle2, Brain, Sparkles, AlertTriangle, Loader2, RefreshCw, ArrowRight } from 'lucide-react';
import { recordLessonProgress } from '../services/api';

export default function ContentPlayerModal({ lesson, onClose, onCompleteAndQuiz, onOpenTutor }) {
  const [submitting, setSubmitting] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [progressSaved, setProgressSaved] = useState(false);
  const closeBtnRef = useRef(null);

  // Focus management and Escape key handling
  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Focus close button on mount
    closeBtnRef.current?.focus();

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  if (!lesson) return null;

  // Safe Video Embed URL Constructor with Host Allowlist
  const embedSrc = (() => {
    const url = lesson.source_url || '';
    const embedCode = lesson.embed_code || '';

    // Safe YouTube ID extractor
    const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/i)
      || embedCode.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtube-nocookie\.com\/embed\/)([a-zA-Z0-9_-]{11})/i);
    if (ytMatch && ytMatch[1]) {
      return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(ytMatch[1])}?rel=0&modestbranding=1`;
    }

    // Safe Vimeo ID extractor
    const vimeoMatch = url.match(/vimeo\.com\/(?:video\/)?([0-9]{6,12})/i)
      || embedCode.match(/player\.vimeo\.com\/video\/([0-9]{6,12})/i);
    if (vimeoMatch && vimeoMatch[1]) {
      return `https://player.vimeo.com/video/${encodeURIComponent(vimeoMatch[1])}?dnt=1`;
    }

    return null;
  })();

  const handleSaveProgress = async (andQuiz = false) => {
    setSubmitting(true);
    setSaveError('');
    try {
      await recordLessonProgress(lesson.id, 100);
      setProgressSaved(true);
      if (andQuiz) {
        onCompleteAndQuiz(lesson);
      }
    } catch (err) {
      setSaveError(err.message || 'Failed to record lesson progress on server.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="lesson-player-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        backdropFilter: 'blur(6px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '860px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '28px',
          background: 'var(--bg-card-solid, var(--bg-card))',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg, 16px)',
          boxShadow: 'var(--shadow-lg)'
        }}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-subject-science">{lesson.subject}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Grade {lesson.grade_level || 10} • {lesson.topic}
              </span>
            </div>
            <h2 id="lesson-player-title" style={{ fontSize: '1.45rem', color: 'var(--text-primary)' }}>
              {lesson.title}
            </h2>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onClose}
            aria-label="Close lesson modal"
            style={{ padding: '6px' }}
          >
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
              title={lesson.title || 'Educational lesson video'}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              sandbox="allow-scripts allow-same-origin allow-presentation"
              loading="lazy"
              referrerPolicy="no-referrer"
              allowFullScreen
            ></iframe>
          </div>
        ) : (
          <div style={{
            padding: '36px 24px',
            textAlign: 'center',
            background: 'var(--bg-soft-blue)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            marginBottom: '20px'
          }}>
            <Sparkles size={36} color="var(--brand-primary)" style={{ margin: '0 auto 12px auto' }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: '6px', color: 'var(--text-primary)' }}>
              Interactive Curriculum Notes & Lesson Module
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto' }}>
              Review the conceptual summary and formula takeaways below before proceeding to the Bloom's taxonomy assessment quiz.
            </p>
          </div>
        )}

        {/* Pedagogical Summary & Key Notes */}
        <div style={{
          background: 'var(--bg-soft-blue)',
          padding: '18px 22px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '24px'
        }}>
          <h4 style={{ fontSize: '1.05rem', color: 'var(--brand-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} /> Key Learning Takeaways
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: '1.5' }}>
            {lesson.description || 'Focus on understanding the foundational principles, definitions, and real-world formula applications for this module.'}
          </p>
        </div>

        {/* Progress Save Error State & Recovery Controls */}
        {saveError && (
          <div
            role="alert"
            style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--accent-coral)',
              marginBottom: '20px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-coral)', fontWeight: 600, marginBottom: '8px' }}>
              <AlertTriangle size={20} />
              <span>Could not save lesson progress</span>
            </div>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
              {saveError} You can retry saving your progress or proceed directly to the assessment quiz.
            </p>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => handleSaveProgress(true)}
                disabled={submitting}
              >
                {submitting ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />} Retry Saving & Take Quiz
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => onCompleteAndQuiz(lesson)}
              >
                Continue to Quiz Without Saving <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Action Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <button type="button" className="btn btn-outline" onClick={() => onOpenTutor(lesson.topic, lesson.id)}>
            <Brain size={18} /> Ask Socratic AI Tutor
          </button>

          {!saveError && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={submitting}
              style={{ padding: '12px 24px', fontSize: '1rem' }}
              onClick={() => handleSaveProgress(true)}
            >
              {submitting ? <Loader2 size={18} className="spin" /> : <CheckCircle2 size={18} />} Complete & Take Quiz
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
