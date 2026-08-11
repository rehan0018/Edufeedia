import React, { useState, useEffect } from 'react';
import { X, CheckCircle2, XCircle, Trophy, ArrowRight, Brain, Loader2, AlertCircle } from 'lucide-react';
import confetti from 'canvas-confetti';
import { fetchQuizForContent, submitQuizAttempt } from '../services/api';

export default function QuizModal({ lesson, onClose, onQuizComplete }) {
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);
  
  const [submitting, setSubmitting] = useState(false);
  const [backendResult, setBackendResult] = useState(null);

  useEffect(() => {
    if (lesson?.id) {
      setLoading(true);
      fetchQuizForContent(lesson.id)
        .then(data => {
          setQuiz(data);
          setLoading(false);
        })
        .catch(err => {
          setError(err.message || 'No quiz available for this module.');
          setLoading(false);
        });
    }
  }, [lesson]);

  const questions = quiz?.questions || [];
  const currentQ = questions[currentIdx];

  const handleSelectOption = (opt) => {
    if (isAnswered) return;
    setSelectedOption(opt);
    setIsAnswered(true);

    const updatedAnswers = [...answers, { question_id: currentQ.id, selected_answer: opt }];
    setAnswers(updatedAnswers);
  };

  const handleNext = async () => {
    if (currentIdx + 1 < questions.length) {
      setCurrentIdx(prev => prev + 1);
      setSelectedOption(null);
      setIsAnswered(false);
    } else {
      // Submit full quiz attempt to backend
      setSubmitting(true);
      try {
        const result = await submitQuizAttempt(quiz.id, answers);
        setBackendResult(result);
        confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        onQuizComplete?.(result);
      } catch (err) {
        setError(err.message || 'Failed to submit quiz to grading server.');
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div className="modal-overlay">
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '680px',
        padding: '32px',
        background: 'var(--bg-card-solid)',
        border: '1px solid var(--border-glow)'
      }}>
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
            <h2 style={{ fontSize: '1.35rem' }}>{quiz?.title || lesson?.title || 'Interactive Assessment'}</h2>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose} style={{ padding: '6px' }}>
            <X size={20} />
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
            <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
            <p>Loading curriculum assessment from learning server...</p>
          </div>
        )}

        {error && !loading && !backendResult && (
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

        {!loading && !error && currentQ && !backendResult && (
          <div>
            {/* Bloom's / Difficulty Pill */}
            <div style={{ display: 'inline-block', marginBottom: '14px' }}>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                background: 'hsla(265, 89%, 66%, 0.18)',
                color: 'var(--accent-purple)',
                border: '1px solid hsla(265, 89%, 66%, 0.4)'
              }}>
                Difficulty: {currentQ.difficulty || 'Medium'}
              </span>
            </div>

            {/* Question Text */}
            <h3 style={{ fontSize: '1.2rem', marginBottom: '22px', lineHeight: '1.4' }}>
              {currentQ.question_text}
            </h3>

            {/* Options List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              {currentQ.options.map((opt, idx) => {
                let btnStyle = {
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-space)',
                  color: 'var(--text-primary)',
                  fontSize: '0.98rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: isAnswered ? 'default' : 'pointer',
                  transition: 'var(--transition-fast)'
                };

                if (isAnswered) {
                  if (opt === currentQ.correct_answer) {
                    btnStyle.border = '2px solid var(--accent-emerald)';
                    btnStyle.background = 'hsla(152, 76%, 50%, 0.15)';
                  } else if (opt === selectedOption) {
                    btnStyle.border = '2px solid var(--accent-rose)';
                    btnStyle.background = 'hsla(346, 84%, 61%, 0.15)';
                  }
                }

                return (
                  <div
                    key={idx}
                    style={btnStyle}
                    onClick={() => handleSelectOption(opt)}
                  >
                    <span>{opt}</span>
                    {isAnswered && opt === currentQ.correct_answer && (
                      <CheckCircle2 size={20} color="var(--accent-emerald)" />
                    )}
                    {isAnswered && opt === selectedOption && opt !== currentQ.correct_answer && (
                      <XCircle size={20} color="var(--accent-rose)" />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Explanation Card */}
            {isAnswered && (
              <div style={{
                padding: '16px 20px',
                borderRadius: 'var(--radius-md)',
                background: selectedOption === currentQ.correct_answer ? 'hsla(152, 76%, 50%, 0.1)' : 'hsla(346, 84%, 61%, 0.1)',
                border: `1px solid ${selectedOption === currentQ.correct_answer ? 'var(--accent-emerald)' : 'var(--accent-rose)'}`,
                marginBottom: '20px'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '4px', color: selectedOption === currentQ.correct_answer ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {selectedOption === currentQ.correct_answer ? '✓ Correct Answer' : '⚠ Concept Clarification'}
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  {currentQ.explanation}
                </div>
              </div>
            )}

            {/* Next Action */}
            {isAnswered && (
              <button
                className="btn btn-primary"
                style={{ width: '100%', padding: '12px' }}
                disabled={submitting}
                onClick={handleNext}
              >
                {submitting ? 'Submitting to Backend...' : (currentIdx + 1 < questions.length ? 'Next Question' : 'Submit Quiz to Server')} <ArrowRight size={16} />
              </button>
            )}
          </div>
        )}

        {/* Backend Live Grading Results */}
        {backendResult && (
          <div style={{ textAlign: 'center', padding: '10px 0' }}>
            <div style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--accent-amber), var(--accent-purple))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <Trophy size={36} color="#0a0f1d" />
            </div>

            <h3 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Backend Evaluated! 🎉</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
              Your attempt has been recorded in the database, updating your mastery profile and SM-2 spaced repetition queue.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '14px',
              marginBottom: '28px'
            }}>
              <div style={{ padding: '14px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Score</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {backendResult.score} / {backendResult.max_score}
                </div>
              </div>

              <div style={{ padding: '14px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Accuracy</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                  {Math.round(backendResult.accuracy_percentage)}%
                </div>
              </div>

              <div style={{ padding: '14px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>XP Awarded</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
                  +{backendResult.xp_gained} XP
                </div>
              </div>
            </div>

            <button
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
