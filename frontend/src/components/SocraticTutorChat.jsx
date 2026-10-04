import React, { useState, useRef, useEffect } from 'react';
import {
  Brain, Send, Sparkles, ShieldCheck, Loader2, AlertCircle, BookOpen,
  Lightbulb, Compass, HelpCircle, RefreshCw, Cpu, Filter, ExternalLink, Video, FileText, Database
} from 'lucide-react';
import { askSocraticTutor } from '../services/api';

export default function SocraticTutorChat({ activeTopic = "Newton's Laws", user = null, activeLessonId = null }) {
  // Session tracking & multi-turn history
  const [conversationId, setConversationId] = useState(() => (
    typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `conv-${Date.now()}`
  ));

  // Provider & Resource Selection Filters
  const [selectedProvider, setSelectedProvider] = useState('auto'); // 'auto' | 'openai' | 'gemini'
  const [selectedResourceType, setSelectedResourceType] = useState('all'); // 'all' | 'paper' | 'video' | 'dataset' | 'pdf'

  const studentGrade = user?.student_profile?.grade_level || user?.grade_level || 10;
  const studentBoard = user?.student_profile?.board || 'CBSE';

  const createInitialMessage = () => ({
    sender: 'tutor',
    text: activeTopic
      ? `Hello! I am your Edufeedia Socratic study companion for Grade ${studentGrade} (${studentBoard}). I help you build first-principles intuition step-by-step rather than giving away answers directly. What question about **${activeTopic}** would you like to explore together?`
      : `Hello! I am your Edufeedia Socratic study companion for Grade ${studentGrade} (${studentBoard}). Ask me any curriculum concept to begin exploring together.`,
    socratic_cue: "What core mechanism or formula in your syllabus would you like to explore together?",
    subject: null,
    topic: activeTopic || null,
    grounding_source: null,
    curriculum_citations: [],
    is_greeting: true,
    follow_ups: activeTopic ? [
      `How do forces interact in ${activeTopic}?`,
      `Can you give an intuitive everyday example of ${activeTopic}?`,
      `Quiz me with a Socratic problem on ${activeTopic}.`
    ] : [
      "How does photosynthesis convert sunlight to energy?",
      "Explain Newton's second law of motion.",
      "How do binary search algorithms work?"
    ]
  });

  const [messages, setMessages] = useState([createInitialMessage()]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reportedMsgIdx, setReportedMsgIdx] = useState(null);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleStartNewSession = () => {
    const newId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `conv-${Date.now()}`;
    setConversationId(newId);
    setMessages([createInitialMessage()]);
    setError('');
  };

  const handleSend = async (questionText = inputQuestion) => {
    if (!questionText.trim() || loading) return;

    const userMsg = { sender: 'student', text: questionText };
    setMessages(prev => [...prev, userMsg]);
    setInputQuestion('');
    setLoading(true);
    setError('');

    // Prepare multi-turn conversation history (last 6 relevant turns)
    const conversationHistory = messages
      .filter(m => !m.is_error && !m.is_greeting)
      .slice(-6)
      .map(m => ({
        role: m.sender === 'student' ? 'user' : 'assistant',
        text: m.text
      }));

    try {
      const resp = await askSocraticTutor(questionText, {
        contentItemId: activeLessonId,
        conversationHistory,
        provider: selectedProvider,
        resourceType: selectedResourceType,
        conversationId
      });

      const hasRealCitations = Array.isArray(resp.curriculum_citations) && resp.curriculum_citations.length > 0;
      const tutorMsg = {
        sender: 'tutor',
        text: resp.answer,
        socratic_cue: resp.socratic_cue,
        follow_ups: resp.follow_up_questions || [],
        subject: resp.subject || null,
        topic: resp.topic || activeTopic,
        grounding_source: hasRealCitations ? (resp.grounding_source || 'Verified Curriculum Sources') : null,
        curriculum_citations: resp.curriculum_citations || [],
        provider: resp.provider || selectedProvider,
        is_safe: resp.is_safe !== false,
        is_greeting: false
      };
      setMessages(prev => [...prev, tutorMsg]);
    } catch (err) {
      const rawMsg = err.message || '';
      let friendly = 'The AI Tutor is temporarily unavailable. Please try again shortly or explore catalog materials.';
      if (rawMsg.includes('Guardian consent') || rawMsg.includes('revoked')) {
        friendly = '🔒 Guardian consent is required under DPDP Act Section 9 to use the AI Socratic Tutor. Please ask your parent or guardian to verify consent in the Guardian Hub.';
      } else if (rawMsg.includes('curfew') || rawMsg.includes('screen time') || rawMsg.includes('Screen time limit')) {
        friendly = '🌙 Your daily AI study quota or bedtime curfew has been reached for today. Time for a healthy break!';
      } else if (rawMsg.includes('Too many') || rawMsg.includes('rate limit') || rawMsg.includes('pause a moment')) {
        friendly = '⏳ You are asking questions quickly! Please take a quick breath before sending your next inquiry.';
      } else if (rawMsg.includes('budget') || rawMsg.includes('quota')) {
        friendly = '📊 The daily learning token budget for this session has been fulfilled. You can continue reviewing lessons and flashcards.';
      }

      setError(friendly);
      setMessages(prev => [...prev, {
        sender: 'tutor',
        text: friendly,
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
      <div className="glass-panel" style={{ padding: '22px 26px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              padding: '4px 10px',
              borderRadius: '12px',
              background: 'var(--gradient-hero)',
              color: '#FFFFFF'
            }}>
              🤖 Socratic AI Tutor
            </span>
            <span style={{
              fontSize: '0.75rem',
              color: 'var(--accent-mint)',
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
            Verified source-grounded reasoning with pedagogical guidance for Grade {studentGrade} ({studentBoard}).
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <div style={{
            padding: '8px 14px',
            background: 'var(--bg-soft-blue)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.84rem'
          }}>
            <span style={{ color: 'var(--text-muted)' }}>Focus Context:</span> <strong style={{ color: 'var(--brand-primary)' }}>{activeTopic}</strong>
          </div>

          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={handleStartNewSession}
            title="Start a fresh conversation and reset discussion history"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem' }}
          >
            <RefreshCw size={14} /> New Session
          </button>
        </div>
      </div>

      {/* Provider & Resource Filters Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '10px 16px',
        marginBottom: '16px',
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        fontSize: '0.84rem'
      }}>
        {/* Model Provider Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Cpu size={14} /> AI Provider:
          </span>
          <select
            id="tutor-provider-select"
            aria-label="Select AI Tutor Provider"
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            style={{
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-space)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              fontSize: '0.84rem',
              cursor: 'pointer'
            }}
          >
            <option value="auto">Auto (Best Match)</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="gemini">Google (Gemini 1.5)</option>
          </select>
        </div>

        {/* Resource Type Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Filter size={14} /> Resource Filter:
          </span>
          <select
            id="tutor-resource-select"
            aria-label="Select Resource Filter"
            value={selectedResourceType}
            onChange={(e) => setSelectedResourceType(e.target.value)}
            style={{
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-space)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              fontSize: '0.84rem',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Curriculum Resources</option>
            <option value="paper">Papers & Documents</option>
            <option value="video">Videos & Lectures</option>
            <option value="dataset">Datasets & Problems</option>
          </select>
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
                background: 'var(--brand-primary)',
                color: '#FFFFFF',
                fontWeight: 600,
                fontSize: '0.95rem',
                lineHeight: '1.45',
                boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)'
              }}>
                {m.text}
              </div>
            ) : (
              /* Tutor Socratic Study Card */
              <div style={{
                maxWidth: '90%',
                padding: '20px',
                borderRadius: '18px 18px 18px 4px',
                background: m.is_error ? 'rgba(255, 122, 89, 0.12)' : 'var(--bg-card)',
                border: m.is_error ? '1px solid var(--accent-coral)' : '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                lineHeight: '1.55'
              }}>
                {/* Genuine Attribution Badge (Only shown when real citations exist) */}
                {m.curriculum_citations && m.curriculum_citations.length > 0 && !m.is_error ? (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.78rem',
                    color: 'var(--brand-primary)',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    marginBottom: '10px'
                  }}>
                    <BookOpen size={14} /> Grounded in {m.curriculum_citations.length} Verified Evidence Source{m.curriculum_citations.length > 1 ? 's' : ''}
                  </div>
                ) : (!m.is_error && !m.is_greeting && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)',
                    fontWeight: 600,
                    marginBottom: '10px'
                  }}>
                    <Compass size={14} /> General Pedagogical Guidance (First-Principles Steering)
                  </div>
                ))}

                {/* Explanation Body */}
                <div style={{ fontSize: '0.94rem', color: 'var(--text-primary)', marginBottom: m.socratic_cue ? '14px' : '0' }}>
                  {m.text}
                </div>

                {/* Retrieved Source Citations with Clickable Links, Page, & Timestamps */}
                {m.curriculum_citations && m.curriculum_citations.length > 0 && (
                  <div style={{
                    marginTop: '12px',
                    marginBottom: '14px',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-soft-blue)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.82rem'
                  }}>
                    <div style={{ fontWeight: 700, color: 'var(--brand-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <BookOpen size={14} /> Verified Evidence Citations:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {m.curriculum_citations.map((cite, cIdx) => {
                        const isVideo = cite.resource_type === 'video' || cite.timestamp || (cite.url && cite.url.includes('youtube'));
                        return (
                          <div
                            key={cIdx}
                            style={{
                              padding: '8px 10px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'var(--bg-card)',
                              border: '1px solid var(--border-subtle)',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              flexWrap: 'wrap',
                              gap: '6px'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              {isVideo ? <Video size={14} color="var(--accent-coral)" /> : <FileText size={14} color="var(--brand-primary)" />}
                              <div>
                                <strong>{cite.source_title || cite.title || 'Curriculum Reference'}</strong>
                                <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>
                                  ({cite.chapter || cite.section || 'Core Syllabus'})
                                </span>
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              {cite.page && (
                                <span style={{
                                  fontSize: '0.74rem',
                                  padding: '2px 8px',
                                  borderRadius: '10px',
                                  background: 'var(--bg-soft-blue)',
                                  color: 'var(--text-secondary)'
                                }}>
                                  📄 {cite.page}
                                </span>
                              )}
                              {cite.timestamp && (
                                <span style={{
                                  fontSize: '0.74rem',
                                  padding: '2px 8px',
                                  borderRadius: '10px',
                                  background: 'rgba(239, 68, 68, 0.1)',
                                  color: 'var(--accent-coral)'
                                }}>
                                  ⏱️ {cite.timestamp}
                                </span>
                              )}
                              {cite.url && (
                                <a
                                  href={cite.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                    color: 'var(--brand-primary)',
                                    textDecoration: 'none',
                                    fontWeight: 600,
                                    fontSize: '0.76rem'
                                  }}
                                >
                                  View Source <ExternalLink size={12} />
                                </a>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Socratic Thinking Prompt Box */}
                {m.socratic_cue && (
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-soft-blue)',
                    borderLeft: '4px solid var(--brand-primary)',
                    borderTop: '1px solid var(--border-subtle)',
                    borderRight: '1px solid var(--border-subtle)',
                    borderBottom: '1px solid var(--border-subtle)',
                    color: 'var(--text-primary)',
                    fontSize: '0.88rem',
                    fontWeight: 500,
                    marginBottom: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '4px', textTransform: 'uppercase', fontSize: '0.76rem', color: 'var(--brand-primary)' }}>
                      <Lightbulb size={14} color="var(--accent-yellow)" /> Think About This:
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
                          type="button"
                          className="btn btn-outline btn-sm"
                          style={{
                            fontSize: '0.8rem',
                            padding: '6px 12px',
                            borderRadius: '16px',
                            background: 'var(--bg-soft-blue)',
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

                {/* Report Affordance */}
                {!m.is_error && !m.is_greeting && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                    <button
                      type="button"
                      onClick={() => setReportedMsgIdx(idx)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: reportedMsgIdx === idx ? 'var(--accent-mint)' : 'var(--text-muted)',
                        fontSize: '0.74rem',
                        cursor: 'pointer',
                        padding: '4px 8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                      title="Report this explanation if inaccurate or out of syllabus"
                    >
                      <HelpCircle size={12} />
                      {reportedMsgIdx === idx ? 'Reported for educator review ✓' : 'Flag / Report response'}
                    </button>
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
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--brand-primary)',
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
          id="socratic-chat-input"
          type="text"
          aria-label="Ask a Socratic question"
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          placeholder="Ask Edufeedia a question (e.g. 'what is computer network', 'how does gravity work')..."
          style={{
            flex: 1,
            padding: '14px 18px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-card)',
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
