import React, { useState } from 'react';
import { X, CheckCircle2, XCircle, Trophy, Sparkles, ArrowRight, RotateCcw, Brain, Zap } from 'lucide-react';
import confetti from 'canvas-confetti';

const SAMPLE_QUESTIONS = [
  {
    id: 'q1',
    question_text: "According to Newton's Second Law of Motion, which equation correctly relates Force (F), Mass (m), and Acceleration (a)?",
    options: ["F = m / a", "F = m * a", "F = m + a", "F = a / m"],
    correct_answer: "F = m * a",
    explanation: "Newton's Second Law states that force is directly proportional to the product of mass and acceleration (F = ma).",
    bloom_level: "Recall",
    topic: "Newton's Laws"
  },
  {
    id: 'q2',
    question_text: "If you apply a constant net force of 20 N to a 4 kg box on a frictionless floor, what is its acceleration?",
    options: ["80 m/s²", "5 m/s²", "16 m/s²", "0.2 m/s²"],
    correct_answer: "5 m/s²",
    explanation: "Using F = ma, we solve for a = F / m = 20 N / 4 kg = 5 m/s².",
    bloom_level: "Apply",
    topic: "Newton's Laws"
  },
  {
    id: 'q3',
    question_text: "What is the primary cellular organelle where aerobic respiration and major ATP synthesis occur?",
    options: ["Ribosome", "Endoplasmic Reticulum", "Mitochondria", "Golgi Apparatus"],
    correct_answer: "Mitochondria",
    explanation: "Mitochondria are the powerhouses of the cell where the Krebs cycle and oxidative phosphorylation take place to generate ATP.",
    bloom_level: "Understand",
    topic: "Human Respiration"
  },
  {
    id: 'q4',
    question_text: "In quadratic equations of the form ax² + bx + c = 0, what does the discriminant value D = b² - 4ac > 0 indicate?",
    options: ["Two distinct real roots", "Two equal real roots", "No real roots", "Infinite roots"],
    correct_answer: "Two distinct real roots",
    explanation: "A positive discriminant (D > 0) indicates two distinct, real roots on the Cartesian parabola.",
    bloom_level: "Analyze",
    topic: "Quadratic Equations"
  },
  {
    id: 'q5',
    question_text: "In Python, which keyword is used to declare a user-defined function?",
    options: ["function", "func", "def", "lambda"],
    correct_answer: "def",
    explanation: "The 'def' keyword is standard in Python syntax to define a function block.",
    bloom_level: "Recall",
    topic: "Python Functions"
  }
];

export default function QuizModal({ lesson, onClose, onQuizComplete }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [quizFinished, setQuizFinished] = useState(false);

  const questions = SAMPLE_QUESTIONS;
  const currentQ = questions[currentIdx];

  const handleSelectOption = (opt) => {
    if (isAnswered) return;
    setSelectedOption(opt);
    setIsAnswered(true);

    if (opt === currentQ.correct_answer) {
      setScore(prev => prev + 1);
    }
  };

  const handleNext = () => {
    if (currentIdx + 1 < questions.length) {
      setCurrentIdx(prev => prev + 1);
      setSelectedOption(null);
      setIsAnswered(false);
    } else {
      setQuizFinished(true);
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
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
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Question {currentIdx + 1} of {questions.length}</span>
            </div>
            <h2 style={{ fontSize: '1.35rem' }}>{currentQ?.topic || 'Curriculum Diagnostic'}</h2>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose} style={{ padding: '6px' }}>
            <X size={20} />
          </button>
        </div>

        {!quizFinished ? (
          <div>
            {/* Bloom's Level Pill */}
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
                Bloom's Taxonomy: {currentQ.bloom_level}
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
                  {selectedOption === currentQ.correct_answer ? '✓ Correct! +20 XP' : '⚠ Key Concept Explanation'}
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
                onClick={handleNext}
              >
                {currentIdx + 1 < questions.length ? 'Next Question' : 'Complete Quiz'} <ArrowRight size={16} />
              </button>
            )}
          </div>
        ) : (
          /* Quiz Results Screen */
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

            <h3 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Quiz Completed! 🎉</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
              Your answers have updated your curriculum mastery profile and spaced repetition intervals.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '14px',
              marginBottom: '28px'
            }}>
              <div style={{ padding: '14px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Score</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{score} / {questions.length}</div>
              </div>

              <div style={{ padding: '14px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Accuracy</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{Math.round((score / questions.length) * 100)}%</div>
              </div>

              <div style={{ padding: '14px', background: 'var(--bg-space)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>XP Gained</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-amber)' }}>+{score * 20} XP</div>
              </div>
            </div>

            <button
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
              onClick={() => {
                onQuizComplete?.(score);
                onClose();
              }}
            >
              Continue to Daily Plan
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
