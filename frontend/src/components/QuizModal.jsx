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
          setError(err.message || 'No assessment quiz available for this lesson.');
          setLoading(false);
        });
    }
  }, [lesson]);

  const questions = quiz?.questions || [];
  const currentQ = questions[currentIdx];

  const handleSelectOption = (opt) => {
    setSelectedOption(opt);
    // Keep answers map updated
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
    } else {
      // Build final answers payload ensuring the last question is included
      const finalAnswers = [
        ...answers.filter(a => a.question_id !== currentQ.id),
        { question_id: currentQ.id, selected_answer: selectedOption }
      ];

      setSubmitting(true);
      try {
        const result = await submitQuizAttempt(quiz.id, finalAnswers);
        setBackendResult(result);
        confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        onQuizComplete?.(result);
      } catch (err) {
        setError(err.message || 'Failed to submit quiz to server.');
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div className="modal-overlay">
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '720px',
        maxHeight: '90vh',
        overflowY: 'auto',
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

        {/* Question Player View */}
        {!loading && !error && currentQ && !backendResult && (
          <div>
            {/* Difficulty Pill */}
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
                const isSelected = selectedOption === opt;
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 18px',
                      borderRadius: 'var(--radius-md)',
                      border: isSelected ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      background: isSelected ? 'hsla(188, 95%, 53%, 0.12)' : 'var(--bg-space)',
                      color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)',
                      fontSize: '0.98rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'var(--transition-fast)'
                    }}
                    onClick={() => handleSelectOption(opt)}
                  >
                    <span>{opt}</span>
                    {isSelected && <CheckCircle2 size={20} color="var(--accent-cyan)" />}
                  </div>
                );
              })}
            </div>

            {/* Next / Submit Button */}
            <button
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
                background: 'linear-gradient(135deg, var(--accent-amber), var(--accent-purple))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 12px auto'
              }}>
                <Trophy size={32} color="#0a0f1d" />
              </div>

              <h3 style={{ fontSize: '1.6rem', marginBottom: '4px' }}>Quiz Evaluated! 🎉</h3>
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
              <div style={{ padding: '12px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Score</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {backendResult.score} / {backendResult.max_score}
                </div>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Accuracy</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                  {Math.round(backendResult.accuracy_percentage)}%
                </div>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>XP Earned</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
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
                      background: 'var(--bg-space)',
                      borderLeft: `4px solid ${res.is_correct ? 'var(--accent-emerald)' : 'var(--accent-rose)'}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: res.is_correct ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                        {res.is_correct ? '✓ Correct' : '✗ Incorrect'}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Question {idx + 1}</span>
                    </div>

                    <p style={{ fontSize: '0.92rem', marginBottom: '6px', fontWeight: 600 }}>
                      {qObj?.question_text || `Question ${idx + 1}`}
                    </p>

                    <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                      Your Answer: <span style={{ color: res.is_correct ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>{res.selected_answer}</span>
                    </div>

                    {!res.is_correct && (
                      <div style={{ fontSize: '0.84rem', color: 'var(--accent-emerald)', marginBottom: '4px' }}>
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
