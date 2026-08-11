import React, { useState } from 'react';
import { Brain, Send, Sparkles, ShieldCheck, Loader2, AlertCircle } from 'lucide-react';
import { askSocraticTutor } from '../services/api';

export default function SocraticTutorChat({ activeTopic = "Newton's Laws" }) {
  const [messages, setMessages] = useState([
    {
      sender: 'tutor',
      text: `Hello! I am your Edufeedia Socratic study companion. We are currently exploring **${activeTopic}**. What core concept or problem step would you like to examine together?`,
      socratic_cue: "Can you describe the physical relationship between force, mass, and acceleration in your own words?",
      follow_ups: [
        "Why does acceleration increase when net force rises?",
        "What is the difference between mass and weight?"
      ]
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
        follow_ups: resp.follow_up_questions
      };
      setMessages(prev => [...prev, tutorMsg]);
    } catch (err) {
      setError(err.message || 'The AI Tutor is temporarily unavailable. Please try again.');
      setMessages(prev => [...prev, {
        sender: 'tutor',
        text: '⚠ Tutor service is currently unavailable. Please try again or ask a question about a different topic.',
        is_error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px 28px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-subject-science">Socratic AI Tutor</span>
              <span style={{
                fontSize: '0.75rem',
                color: 'var(--accent-emerald)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontWeight: 600
              }}>
                <ShieldCheck size={14} /> Multi-Label Safety Gate
              </span>
            </div>
            <h1 style={{ fontSize: '1.8rem' }}>🧠 Socratic Study Companion</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              Curriculum-grounded hybrid RAG assistant designed to guide you through first-principles reasoning.
            </p>
          </div>

          <div style={{
            padding: '8px 14px',
            background: 'var(--bg-space)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.85rem'
          }}>
            <span style={{ color: 'var(--text-muted)' }}>Focus Topic:</span> <strong style={{ color: 'var(--accent-cyan)' }}>{activeTopic}</strong>
          </div>
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
        gap: '18px',
        marginBottom: '20px'
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
            <div style={{
              maxWidth: '82%',
              padding: '14px 18px',
              borderRadius: 'var(--radius-md)',
              background: m.sender === 'student' 
                ? 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))' 
                : m.is_error 
                  ? 'hsla(346, 84%, 61%, 0.15)'
                  : 'var(--bg-card-solid)',
              color: m.sender === 'student' ? 'hsl(222, 47%, 9%)' : 'var(--text-primary)',
              border: m.sender === 'student' ? 'none' : m.is_error ? '1px solid var(--accent-rose)' : '1px solid var(--border-subtle)',
              fontWeight: m.sender === 'student' ? 600 : 400,
              lineHeight: '1.5'
            }}>
              <div style={{ fontSize: '0.78rem', opacity: 0.75, marginBottom: '4px', textTransform: 'uppercase', fontWeight: 700 }}>
                {m.sender === 'student' ? 'You' : 'Edufeedia Socratic Tutor'}
              </div>
              <div>{m.text}</div>

              {m.socratic_cue && (
                <div style={{
                  marginTop: '10px',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'hsla(222, 40%, 8%, 0.8)',
                  color: 'var(--accent-cyan)',
                  fontSize: '0.86rem',
                  fontStyle: 'italic',
                  borderLeft: '3px solid var(--accent-cyan)'
                }}>
                  🤔 Socratic Prompt: {m.socratic_cue}
                </div>
              )}
            </div>

            {/* Follow-up Suggestion Buttons */}
            {m.follow_ups && (
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
                {m.follow_ups.map((q, qIdx) => (
                  <button
                    key={qIdx}
                    className="btn btn-outline btn-sm"
                    style={{ fontSize: '0.78rem', padding: '4px 10px' }}
                    onClick={() => handleSend(q)}
                  >
                    💡 {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', fontSize: '0.9rem' }}>
            <Loader2 size={18} className="spin" /> Socratic tutor is querying curriculum context...
          </div>
        )}
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
          placeholder="Ask a question about formulas, definitions, or problem steps..."
          style={{
            flex: 1,
            padding: '14px 18px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-card-solid)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            fontSize: '0.98rem',
            outline: 'none'
          }}
        />
        <button type="submit" className="btn btn-primary" style={{ padding: '0 24px' }}>
          <Send size={18} /> Ask
        </button>
      </form>
    </div>
  );
}
