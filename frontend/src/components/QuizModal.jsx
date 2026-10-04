import React, { useState, useEffect, useRef } from 'react';
import { X, CheckCircle2, Trophy, ArrowRight, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import confetti from 'canvas-confetti';
import { fetchQuizForContent, submitQuizAttempt } from '../services/api';

export default function QuizModal({ lesson, onClose, onQuizComplete }) {
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [submitError, setSubmitError] = useState('');
  
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  
  const [submitting, setSubmitting] = useState(false);
  const [backendResult, setBackendResult] = useState(null);
  const closeBtnRef = useRef(null);

  // Dialog semantics, Escape key listener and body scroll lock
  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
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

  useEffect(() => {
    if (lesson?.id) {
      setLoading(true);
      setLoadError('');
      fetchQuizForContent(lesson.id)
        .then(data => {
          setQuiz(data);
          setLoading(false);
        })
        .catch(err => {
          setLoadError(err.message || 'No assessment quiz available for this lesson.');
          setLoading(false);
        });
    }
  }, [lesson]);

  const questions = quiz?.questions || [];
  const currentQ = questions[currentIdx];

  const handleSelectOption = (opt) => {
    setSelectedOption(opt);
    setSubmitError('');
    const remaining = answers.filter(a => a.question_id !== currentQ.id);
    setAnswers([...remaining, { question_id: currentQ.id, selected_answer: opt }]);
  };

  const handleNext = async () => {
    if (!selectedOption) return;

    if (currentIdx + 1 < questions.length) {
      const nextIdx = currentIdx + 1;
      setCurrentIdx(nextIdx);
      const nextQ = questions[nextIdx];
      const prevAnswer = answers.find(a => a.question_id === nextQ?.id);
      setSelectedOption(prevAnswer ? prevAnswer.selected_answer : null);
      setSubmitError('');
    } else {
      const finalAnswers = [
        ...answers.filter(a => a.question_id !== currentQ.id),
        { question_id: currentQ.id, selected_answer: selectedOption }
      ];

      setSubmitting(true);
      setSubmitError('');
      try {
        const result = await submitQuizAttempt(quiz.id, finalAnswers);
        setBackendResult(result);
        confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        onQuizComplete?.(result);
      } catch (err) {
        setSubmitError(err.message || 'Failed to submit quiz to server. Your answers are saved—please retry.');
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="quiz-modal-title"
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
          maxWidth: '720px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '32px',
          background: 'var(--bg-card-solid, var(--bg-card))',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg, 16px)',
          boxShadow: 'var(--shadow-lg)'
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-subject-coding">Assessment Quiz</span>
              {questions.length > 0 && !backendResult && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Question {currentIdx + 1} of {questions.length}
                </span>
              )}
            </div>
            <h2 id="quiz-modal-title" style={{ fontSize: '1.35rem', color: 'var(--text-primary)' }}>
              {quiz?.title || lesson?.title || 'Interactive Assessment'}
            </h2>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onClose}
            aria-label="Close quiz modal"
            style={{ padding: '6px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--brand-primary)' }}>
            <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
            <p>Loading curriculum assessment from learning server...</p>
          </div>
        )}

        {/* Load Error State (e.g. no quiz found for topic) */}
        {loadError && !loading && !backendResult && (
          <div
            role="alert"
            style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(255, 122, 89, 0.12)',
              border: '1px solid var(--accent-coral)',
              color: 'var(--accent-coral)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <AlertCircle size={20} />
            <span>{loadError}</span>
          </div>
        )}

        {/* Question Player View (Remains visible even if submission error occurs) */}
        {!loading && !loadError && currentQ && !backendResult && (
          <div>
            {/* Difficulty Pill */}
            <div style={{ display: 'inline-block', marginBottom: '14px' }}>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(37, 99, 235, 0.12)',
                color: 'var(--brand-primary)',
                border: '1px solid var(--border-subtle)'
              }}>
                Difficulty: {currentQ.difficulty || 'Medium'}
              </span>
            </div>

            <h3
              id={`question-text-${currentIdx}`}
              style={{ fontSize: '1.15rem', marginBottom: '20px', lineHeight: 1.45, color: 'var(--text-primary)' }}
            >
              {currentQ.question_text}
            </h3>

            {/* Accessible Options List */}
            <div
              role="radiogroup"
              aria-labelledby={`question-text-${currentIdx}`}
              style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}
            >
              {currentQ.options.map((opt, idx) => {
                const isSelected = selectedOption === opt;
                return (
                  <button
                    key={idx}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    tabIndex={0}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '14px 18px',
                      borderRadius: 'var(--radius-md)',
                      border: isSelected ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                      background: isSelected ? 'var(--bg-soft-blue)' : 'var(--bg-card)',
                      color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)',
                      fontWeight: isSelected ? 600 : 400,
                      fontSize: '0.98rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      outline: 'none'
                    }}
                    onClick={() => handleSelectOption(opt)}
                    onKeyDown={(e) => {
                      if (e.key === ' ' || e.key === 'Enter') {
                        e.preventDefault();
                        handleSelectOption(opt);
                      }
                    }}
                  >
                    <span>{opt}</span>
                    {isSelected && <CheckCircle2 size={20} color="var(--brand-primary)" />}
                  </button>
                );
              })}
            </div>

            {/* Submission Error Banner & Recovery Button */}
            {submitError && (
              <div
                role="alert"
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid var(--accent-coral)',
                  color: 'var(--accent-coral)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  marginBottom: '20px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
                  <AlertCircle size={18} />
                  <span>{submitError}</span>
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={handleNext}
                  disabled={submitting}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  <RefreshCw size={14} className={submitting ? 'spin' : ''} /> Retry
                </button>
              </div>
            )}

            {/* Next / Submit Button */}
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
              disabled={!selectedOption || submitting}
              onClick={handleNext}
            >
              {submitting ? (
                <>
                  <Loader2 size={16} className="spin" /> Submitting to Server...
                </>
              ) : currentIdx + 1 < questions.length ? (
                <>
                  Next Question <ArrowRight size={16} />
                </>
              ) : (
                'Submit Quiz for Server Evaluation'
              )}
            </button>
          </div>
        )}

        {/* Server Evaluated Result & Explanations */}
        {backendResult && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'var(--gradient-fun)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 12px auto',
                boxShadow: '0 4px 14px rgba(255, 122, 89, 0.25)'
              }}>
                <Trophy size={32} color="#FFFFFF" />
              </div>

              <h3 style={{ fontSize: '1.6rem', marginBottom: '4px', color: 'var(--text-primary)' }}>Quiz Evaluated! 🎉</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Your responses have been recorded in the database, updating topic mastery and SM-2 schedules.
              </p>
            </div>

            {/* Score Overview */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px',
              marginBottom: '24px'
            }}>
              <div style={{ padding: '12px', background: 'var(--bg-soft-blue)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Score</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                  {backendResult.score} / {backendResult.max_score}
                </div>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-soft-blue)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Accuracy</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-mint)' }}>
                  {Math.round(backendResult.accuracy_percentage)}%
                </div>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-soft-blue)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>XP Earned</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-yellow)' }}>
                  +{backendResult.xp_gained} XP
                </div>
              </div>
            </div>

            {/* Question Breakdown with Explanations */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
              <h4 style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Detailed Question Review</h4>
              {backendResult.results?.map((res, idx) => {
                const qObj = questions.find(q => q.id === res.question_id);
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 18px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-soft-blue)',
                      borderLeft: `4px solid ${res.is_correct ? 'var(--accent-mint)' : 'var(--accent-coral)'}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: res.is_correct ? 'var(--accent-mint)' : 'var(--accent-coral)' }}>
                        {res.is_correct ? '✓ Correct' : '✗ Incorrect'}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Question {idx + 1}</span>
                    </div>

                    <p style={{ fontSize: '0.92rem', marginBottom: '6px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {qObj?.question_text || `Question ${idx + 1}`}
                    </p>

                    <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                      Your Answer: <span style={{ color: res.is_correct ? 'var(--accent-mint)' : 'var(--accent-coral)', fontWeight: 600 }}>{res.selected_answer}</span>
                    </div>

                    {!res.is_correct && (
                      <div style={{ fontSize: '0.84rem', color: 'var(--accent-mint)', marginBottom: '4px', fontWeight: 600 }}>
                        Correct Answer: {res.correct_answer}
                      </div>
                    )}

                    {res.explanation && (
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px', fontStyle: 'italic' }}>
                        💡 {res.explanation}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
              onClick={onClose}
            >
              Continue to Daily Plan
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
