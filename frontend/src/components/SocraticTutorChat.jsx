import React, { useState, useRef, useEffect } from 'react';
import { Brain, Send, Sparkles, ShieldCheck, Loader2, AlertCircle, BookOpen, Lightbulb, Compass, HelpCircle, RefreshCw } from 'lucide-react';
import { askSocraticTutor } from '../services/api';

export default function SocraticTutorChat({ activeTopic = "Newton's Laws" }) {
  const [messages, setMessages] = useState([
    {
      sender: 'tutor',
      text: `Hello! I am your Edufeedia Socratic study companion. I help you build deep first-principles intuition step-by-step rather than just giving away final answers. Ask me about **${activeTopic}** or explore any STEM curriculum concept!`,
      socratic_cue: "What core mechanism or formula in your syllabus would you like to explore together?",
      subject: "Science",
      topic: activeTopic,
      grounding_source: `Curriculum Guide • Grade 10`,
      follow_ups: [
        "How do forces interact in action-reaction pairs?",
        "What is the physical meaning of momentum (p = mv)?",
        "What is a computer network?"
      ]
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const chatBottomRef = useRef(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (questionText = inputQuestion) => {
    if (!questionText.trim() || loading) return;

    const userMsg = { sender: 'student', text: questionText };
    setMessages(prev => [...prev, userMsg]);
    setInputQuestion('');
    setLoading(true);
    setError('');

    try {
      const resp = await askSocraticTutor(questionText);
      const tutorMsg = {
        sender: 'tutor',
        text: resp.answer,
        socratic_cue: resp.socratic_cue,
        follow_ups: resp.follow_up_questions || [],
        subject: resp.subject || 'Curriculum',
        topic: resp.topic || activeTopic,
        grounding_source: resp.grounding_source || `${resp.subject || 'Curriculum'} • Grade 10`,
        provider: resp.provider || 'edufeedia_rag'
      };
      setMessages(prev => [...prev, tutorMsg]);
    } catch (err) {
      setError(err.message || 'The AI Tutor is temporarily unavailable.');
      setMessages(prev => [...prev, {
        sender: 'tutor',
        text: '⚠ Tutor service is currently unavailable. Please check your connection or explore another topic in the Explore Catalog.',
        is_error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = (actionType) => {
    const lastTutorMsg = [...messages].reverse().find(m => m.sender === 'tutor' && !m.is_error);
    const contextTopic = lastTutorMsg?.topic || activeTopic;

    if (actionType === 'simpler') {
      handleSend(`Can you explain ${contextTopic} in simpler terms with an everyday analogy for beginners?`);
    } else if (actionType === 'example') {
      handleSend(`Can you give a concrete real-world engineering or scientific example of ${contextTopic}?`);
    } else if (actionType === 'practice') {
      handleSend(`Can you give me an interactive Socratic practice question to test my understanding of ${contextTopic}?`);
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '28px 16px' }}>
      
      {/* Header Panel */}
      <div className="glass-panel" style={{ padding: '22px 26px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              padding: '3px 10px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
              color: '#0a0f1d'
            }}>
              🤖 Socratic AI Tutor
            </span>
            <span style={{
              fontSize: '0.75rem',
              color: 'var(--accent-emerald)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 600
            }}>
              <ShieldCheck size={14} /> Multi-Label Safety & Privacy Gate
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px' }}>
            Curriculum Socratic Guide
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Powered by Intent-Aware Hybrid RAG & pedagogical first-principles reasoning.
          </p>
        </div>

        <div style={{
          padding: '8px 14px',
          background: 'var(--bg-space)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.84rem'
        }}>
          <span style={{ color: 'var(--text-muted)' }}>Focus Context:</span> <strong style={{ color: 'var(--accent-cyan)' }}>{activeTopic}</strong>
        </div>
      </div>

      {/* Chat Messages Stream */}
      <div className="glass-panel" style={{
        padding: '24px',
        minHeight: '440px',
        maxHeight: '520px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        marginBottom: '16px'
      }}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: m.sender === 'student' ? 'flex-end' : 'flex-start',
            }}
          >
            {m.sender === 'student' ? (
              /* Student Message Bubble */
              <div style={{
                maxWidth: '75%',
                padding: '12px 18px',
                borderRadius: '18px 18px 4px 18px',
                background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
                color: '#0a0f1d',
                fontWeight: 600,
                fontSize: '0.95rem',
                lineHeight: '1.45',
                boxShadow: 'var(--shadow-glow-cyan)'
              }}>
                {m.text}
              </div>
            ) : (
              /* Tutor Socratic Study Card */
              <div style={{
                maxWidth: '90%',
                padding: '20px',
                borderRadius: '18px 18px 18px 4px',
                background: m.is_error ? 'hsla(346, 84%, 61%, 0.12)' : 'var(--bg-card-solid)',
                border: m.is_error ? '1px solid var(--accent-rose)' : '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                lineHeight: '1.55'
              }}>
                {/* Attribution Badge */}
                {m.grounding_source && !m.is_error && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.78rem',
                    color: 'var(--accent-cyan)',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    marginBottom: '10px'
                  }}>
                    <BookOpen size={14} /> Grounded in: {m.grounding_source}
                  </div>
                )}

                {/* Explanation Body */}
                <div style={{ fontSize: '0.94rem', color: 'var(--text-primary)', marginBottom: m.socratic_cue ? '14px' : '0' }}>
                  {m.text}
                </div>

                {/* Socratic Thinking Prompt Box */}
                {m.socratic_cue && (
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'hsla(186, 100%, 50%, 0.08)',
                    borderLeft: '4px solid var(--accent-cyan)',
                    borderTop: '1px solid hsla(186, 100%, 50%, 0.2)',
                    borderRight: '1px solid hsla(186, 100%, 50%, 0.2)',
                    borderBottom: '1px solid hsla(186, 100%, 50%, 0.2)',
                    color: 'var(--accent-cyan)',
                    fontSize: '0.88rem',
                    fontWeight: 500,
                    marginBottom: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '4px', textTransform: 'uppercase', fontSize: '0.76rem' }}>
                      <Lightbulb size={14} /> Think About This:
                    </div>
                    {m.socratic_cue}
                  </div>
                )}

                {/* Interactive Follow-up Exploration Pills */}
                {m.follow_ups && m.follow_ups.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', fontWeight: 600 }}>
                      Explore Next Questions:
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {m.follow_ups.map((q, qIdx) => (
                        <button
                          key={qIdx}
                          className="btn btn-outline btn-sm"
                          style={{
                            fontSize: '0.8rem',
                            padding: '6px 12px',
                            borderRadius: '16px',
                            background: 'var(--bg-space)',
                            borderColor: 'var(--border-subtle)',
                            textAlign: 'left'
                          }}
                          onClick={() => handleSend(q)}
                        >
                          💡 {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '14px 18px',
            borderRadius: '16px',
            background: 'var(--bg-card-solid)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--accent-cyan)',
            fontSize: '0.88rem',
            maxWidth: '340px'
          }}>
            <Loader2 size={18} className="spin" />
            <span>Consulting verified curriculum grounding...</span>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Quick-Action Pedagogical Buttons */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
        <button
          type="button"
          className="btn btn-outline btn-sm"
          disabled={loading}
          onClick={() => handleQuickAction('simpler')}
          style={{ fontSize: '0.82rem', padding: '6px 12px' }}
        >
          💡 Explain Simpler
        </button>

        <button
          type="button"
          className="btn btn-outline btn-sm"
          disabled={loading}
          onClick={() => handleQuickAction('example')}
          style={{ fontSize: '0.82rem', padding: '6px 12px' }}
        >
          🔬 Real-World Example
        </button>

        <button
          type="button"
          className="btn btn-outline btn-sm"
          disabled={loading}
          onClick={() => handleQuickAction('practice')}
          style={{ fontSize: '0.82rem', padding: '6px 12px' }}
        >
          🎯 Practice Question
        </button>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: 'flex', gap: '12px' }}
      >
        <input
          type="text"
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          placeholder="Ask Edufeedia a question (e.g. 'what is computer network', 'how does gravity work')..."
          style={{
            flex: 1,
            padding: '14px 18px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-card-solid)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            fontSize: '0.96rem',
            outline: 'none'
          }}
        />
        <button
          type="submit"
          disabled={loading || !inputQuestion.trim()}
          className="btn btn-primary"
          style={{ padding: '0 24px', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Send size={18} /> Ask
        </button>
      </form>
    </div>
  );
}
