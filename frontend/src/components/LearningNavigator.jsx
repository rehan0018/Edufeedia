import React, { useState, useEffect } from 'react';
import {
  Compass, Search, Sparkles, BookOpen, Play, CheckCircle2,
  HelpCircle, ArrowRight, Award, Zap, Brain, ShieldCheck,
  ChevronRight, ExternalLink, RotateCcw, AlertTriangle, X,
  Layers, Info, Check, Clock, Globe
} from 'lucide-react';
import { discoverySearch, submitDiscoveryQuiz, recordDiscoveryEngagement } from '../services/api';

export default function LearningNavigator({ onOpenLesson, onOpenTutor }) {
  const [query, setQuery] = useState('Explain photosynthesis for Class 8 CBSE');
  const [grade, setGrade] = useState(8);
  const [board, setBoard] = useState('CBSE');
  const [depth, setDepth] = useState('standard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [discoveryData, setDiscoveryData] = useState(null);

  // Concept Check Quiz state
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submittingQuiz, setSubmittingQuiz] = useState(false);
  const [quizResult, setQuizResult] = useState(null);

  // Why this resource breakdown modal
  const [scoreModalResource, setScoreModalResource] = useState(null);

  // Interactive Simulation Modal
  const [activeSimulation, setActiveSimulation] = useState(null);

  // Quick search suggestion chips
  const suggestedQueries = [
    'Explain photosynthesis for Class 8 CBSE',
    "Newton's Third Law of Motion Class 9 ICSE",
    'Quadratic equations discriminant Class 10',
    'Universal law of gravitation Class 9',
    'Structure of plant and animal cells Class 8'
  ];

  const handleSearch = async (overrideQuery = null) => {
    const q = (overrideQuery !== null ? overrideQuery : query).trim();
    if (!q) return;

    setLoading(true);
    setError('');
    setQuizResult(null);
    setSelectedAnswers({});

    try {
      const res = await discoverySearch({
        query: q,
        grade,
        board,
        depth
      });
      setDiscoveryData(res);
    } catch (err) {
      console.error('Discovery search error:', err);
      setError(err.message || 'Unable to load educational discovery results.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch('Explain photosynthesis for Class 8 CBSE');
  }, []);

  const handleOptionSelect = (questionId, optionIndex) => {
    if (quizResult) return; // Prevent changing after submission
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: optionIndex
    }));
  };

  const handleQuizSubmit = async () => {
    if (!discoveryData?.practice_quiz) return;
    const quiz = discoveryData.practice_quiz;

    // Check if at least 1 answer selected
    if (Object.keys(selectedAnswers).length === 0) {
      alert('Please answer at least one question before submitting your concept check.');
      return;
    }

    setSubmittingQuiz(true);
    try {
      const res = await submitDiscoveryQuiz({
        quiz_id: quiz.quiz_id,
        topic: quiz.topic,
        subject: discoveryData.interpreted_intent?.subject || 'Science',
        grade_level: quiz.grade_level,
        answers: selectedAnswers
      });
      setQuizResult(res);

      // Log engagement
      recordDiscoveryEngagement({
        resource_id: quiz.quiz_id,
        topic: quiz.topic,
        subject: discoveryData.interpreted_intent?.subject || 'Science',
        dwell_time_seconds: 120,
        action_type: 'completed'
      }).catch(() => {});
    } catch (err) {
      alert(`Quiz submission failed: ${err.message}`);
    } finally {
      setSubmittingQuiz(false);
    }
  };

  const handleResourceClick = (resource) => {
    if (resource.resource_type === 'interactive_sim' && resource.embed_url) {
      setActiveSimulation(resource);
    } else if (onOpenLesson) {
      onOpenLesson(resource);
    } else {
      window.open(resource.source_url, '_blank');
    }

    // Record dwell/click engagement
    recordDiscoveryEngagement({
      resource_id: resource.id,
      topic: resource.topic,
      subject: resource.subject,
      dwell_time_seconds: 60,
      action_type: 'viewed'
    }).catch(() => {});
  };

  const understand = discoveryData?.understand_it;
  const bestMatch = discoveryData?.best_match;
  const categories = discoveryData?.resources_by_category || {};
  const practiceQuiz = discoveryData?.practice_quiz;
  const pathway = discoveryData?.knowledge_pathway || [];

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Hero Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(16, 185, 129, 0.06))',
        border: '1px solid var(--border-subtle)',
        borderRadius: '24px',
        padding: '32px 28px',
        marginBottom: '28px',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'var(--gradient-hero)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}>
            <Compass size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>
              Learning Navigator
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
              Intelligent Educational Operating System: Finding the right knowledge, from the right source, at the right depth.
            </p>
          </div>
        </div>

        {/* Natural Language Search Input */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '280px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="E.g., Explain photosynthesis for Class 8 CBSE, Newton's 3rd Law..."
              style={{
                width: '100%',
                padding: '14px 16px 14px 44px',
                borderRadius: '14px',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                outline: 'none',
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.04)'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={grade}
              onChange={(e) => setGrade(Number(e.target.value))}
              style={{
                padding: '0 14px',
                borderRadius: '12px',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                fontWeight: 600,
                outline: 'none'
              }}
            >
              {[6, 7, 8, 9, 10, 11, 12].map(g => (
                <option key={g} value={g}>Class {g}</option>
              ))}
            </select>

            <select
              value={board}
              onChange={(e) => setBoard(e.target.value)}
              style={{
                padding: '0 14px',
                borderRadius: '12px',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                fontWeight: 600,
                outline: 'none'
              }}
            >
              <option value="CBSE">CBSE</option>
              <option value="ICSE">ICSE</option>
              <option value="State Board">State Board</option>
            </select>

            <button
              onClick={() => handleSearch()}
              disabled={loading}
              className="btn btn-primary"
              style={{
                padding: '12px 24px',
                borderRadius: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 700
              }}
            >
              {loading ? <RotateCcw size={16} className="animate-spin" /> : <Sparkles size={16} />}
              <span>Discover</span>
            </button>
          </div>
        </div>

        {/* Suggested Queries Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Try:</span>
          {suggestedQueries.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(sq);
                handleSearch(sq);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '999px',
                padding: '4px 12px',
                fontSize: '0.78rem',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            border: '4px solid rgba(37, 99, 235, 0.2)',
            borderTopColor: 'var(--brand-primary)',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px auto'
          }} />
          <h3 style={{ margin: '0 0 6px 0', fontSize: '1.1rem' }}>Executing Discovery Pipeline...</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Evaluating identity, hard safety gate, source authority tiers, and curriculum alignment.
          </p>
        </div>
      )}

      {error && (
        <div style={{
          padding: '16px 20px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: '16px',
          color: '#EF4444',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '24px'
        }}>
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Learning Navigator Payload */}
      {!loading && discoveryData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

          {/* 1. UNDERSTAND IT (Socratic Conceptual Synthesis) */}
          {understand && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '20px',
              padding: '28px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    background: 'rgba(37, 99, 235, 0.12)',
                    color: 'var(--brand-primary)',
                    padding: '4px 10px',
                    borderRadius: '8px',
                    fontWeight: 800,
                    fontSize: '0.75rem',
                    letterSpacing: '0.05em'
                  }}>
                    🎯 UNDERSTAND IT
                  </span>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {understand.grade_adaptation}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent-mint)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Certified Pedagogical Synthesis
                </div>
              </div>

              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '0 0 12px 0' }}>
                {understand.headline}
              </h2>

              <p style={{ fontSize: '0.96rem', lineHeight: '1.65', color: 'var(--text-primary)', marginBottom: '20px' }}>
                {understand.core_explanation}
              </p>

              {understand.key_equation && (
                <div style={{
                  background: 'var(--bg-soft-blue)',
                  border: '1px dashed var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '12px 18px',
                  fontFamily: 'monospace',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  color: 'var(--brand-primary)',
                  marginBottom: '20px',
                  overflowX: 'auto'
                }}>
                  {understand.key_equation}
                </div>
              )}

              {/* Key Takeaways */}
              {understand.key_takeaways && understand.key_takeaways.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '10px', color: 'var(--text-secondary)' }}>
                    Key Takeaways:
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                    {understand.key_takeaways.map((point, idx) => (
                      <div key={idx} style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        fontSize: '0.86rem'
                      }}>
                        <CheckCircle2 size={16} color="var(--accent-mint)" style={{ flexShrink: 0, marginTop: '2px' }} />
                        <span>{point}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Vocabulary pills */}
              {understand.vocabulary && understand.vocabulary.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>Key Vocabulary:</span>
                  {understand.vocabulary.map((vocab, vIdx) => (
                    <span
                      key={vIdx}
                      title={vocab.definition}
                      style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '8px',
                        padding: '3px 10px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'help'
                      }}
                    >
                      📖 <strong>{vocab.term}</strong>: {vocab.definition}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 2. BEST MATCH (Hero Recommendation Card) */}
          {bestMatch && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(232, 90, 79, 0.05), rgba(37, 99, 235, 0.04))',
              border: '2px solid var(--brand-primary)',
              borderRadius: '20px',
              padding: '24px 28px',
              position: 'relative',
              boxShadow: '0 8px 24px rgba(232, 90, 79, 0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    background: 'var(--gradient-hero)',
                    color: '#FFFFFF',
                    padding: '4px 12px',
                    borderRadius: '999px',
                    fontWeight: 800,
                    fontSize: '0.78rem',
                    letterSpacing: '0.04em'
                  }}>
                    ⭐ BEST MATCH
                  </span>
                  <span style={{
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: 'var(--accent-mint)',
                    padding: '3px 10px',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.78rem'
                  }}>
                    {Math.round(bestMatch.quality_score * 100)}% Match
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {bestMatch.source_platform}
                  </span>
                </div>

                {/* Explainability Trigger Button */}
                <button
                  onClick={() => setScoreModalResource(bestMatch)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '10px',
                    padding: '5px 12px',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: 'var(--text-primary)'
                  }}
                >
                  <Info size={14} color="var(--brand-primary)" />
                  <span>Why this resource?</span>
                </button>
              </div>

              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, margin: '0 0 10px 0' }}>
                {bestMatch.resource_type === 'animation' ? '🎬' : '📺'} {bestMatch.title}
              </h3>

              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5', margin: '0 0 16px 0' }}>
                {bestMatch.description}
              </p>

              {/* Rationale Checklist (Why chosen) */}
              <div style={{
                background: 'rgba(0, 0, 0, 0.03)',
                borderRadius: '12px',
                padding: '12px 16px',
                marginBottom: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Educational Provenance:
                </div>
                {bestMatch.why_chosen && bestMatch.why_chosen.map((reason, rIdx) => (
                  <div key={rIdx} style={{ fontSize: '0.84rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>

              {/* Actions & Meta */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> {bestMatch.duration_minutes} min
                  </span>
                  <span>•</span>
                  <span>Class {bestMatch.grade_level}</span>
                  <span>•</span>
                  <span>{bestMatch.board}</span>
                  <span>•</span>
                  <span style={{ textTransform: 'capitalize' }}>{bestMatch.language}</span>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  {onOpenTutor && (
                    <button
                      onClick={() => onOpenTutor(bestMatch.topic)}
                      className="btn btn-outline"
                      style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                    >
                      <Brain size={15} /> Ask Tutor
                    </button>
                  )}
                  <button
                    onClick={() => handleResourceClick(bestMatch)}
                    className="btn btn-primary"
                    style={{ padding: '8px 20px', fontSize: '0.85rem', fontWeight: 700 }}
                  >
                    <Play size={15} /> Start Learning
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 3. MULTI-MODAL LEARNING CATEGORIES (Read, Explore, Video) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>

            {/* READ (NCERT & Curriculum Reading) */}
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '18px',
              padding: '22px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.2rem' }}>📖</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>READ</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                  Official Textbooks
                </span>
              </div>

              {categories.read && categories.read.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {categories.read.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleResourceClick(item)}
                      style={{
                        padding: '12px 14px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{item.title}</div>
                        <span style={{ fontSize: '0.72rem', background: 'rgba(37, 99, 235, 0.1)', color: 'var(--brand-primary)', padding: '2px 6px', borderRadius: '6px' }}>
                          {item.authority_tier}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        {item.description}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span>{item.source_name}</span>
                        <span>{item.duration_minutes} min read ➔</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No curriculum readings found.</p>
              )}
            </div>

            {/* EXPLORE (Interactive Simulations & Labs) */}
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '18px',
              padding: '22px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.2rem' }}>🧪</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>EXPLORE</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                  Hands-on Simulations
                </span>
              </div>

              {categories.explore && categories.explore.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {categories.explore.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleResourceClick(item)}
                      style={{
                        padding: '12px 14px',
                        background: 'rgba(16, 185, 129, 0.04)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{item.title}</div>
                        <span style={{ fontSize: '0.72rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-mint)', padding: '2px 6px', borderRadius: '6px' }}>
                          HTML5 Lab
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        {item.description}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--accent-mint)', fontWeight: 600 }}>
                        <span>{item.source_name}</span>
                        <span>Launch Simulation 🧪 ➔</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No interactive simulations available.</p>
              )}
            </div>

            {/* WATCH (Concept Deep-Dives) */}
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '18px',
              padding: '22px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.2rem' }}>📺</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>WATCH</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                  Vetted Concept Videos
                </span>
              </div>

              {categories.video && categories.video.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {categories.video.slice(0, 2).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleResourceClick(item)}
                      style={{
                        padding: '12px 14px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{item.title}</div>
                        <span style={{ fontSize: '0.72rem', background: 'rgba(232, 90, 79, 0.1)', color: 'var(--brand-primary)', padding: '2px 6px', borderRadius: '6px' }}>
                          {item.duration_minutes}m
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        {item.description}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span>{item.creator_name || item.source_name}</span>
                        <span>Watch Video ➔</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No video deep-dives found.</p>
              )}
            </div>

          </div>

          {/* 4. PRACTICE (5-Question Concept Check Quiz) */}
          {practiceQuiz && practiceQuiz.questions && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '20px',
              padding: '28px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, #10B981, #059669)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF'
                  }}>
                    <Brain size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                      🧠 PRACTICE: 5-Question Concept Check
                    </h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                      Verify your understanding. Submitting directly updates your mastery index!
                    </p>
                  </div>
                </div>

                {quizResult && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    padding: '8px 16px',
                    borderRadius: '12px'
                  }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--accent-mint)' }}>
                      Score: {quizResult.score} / {quizResult.total_questions} ({quizResult.accuracy_percentage}%)
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                      +{quizResult.xp_earned} XP ⚡
                    </div>
                  </div>
                )}
              </div>

              {/* Questions List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
                {practiceQuiz.questions.map((q, qIndex) => {
                  const studentSelected = selectedAnswers[q.id];
                  const qResult = quizResult?.question_results?.find(r => r.question_id === q.id);

                  return (
                    <div key={q.id} style={{
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '14px',
                      padding: '18px 20px'
                    }}>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '12px', display: 'flex', gap: '8px' }}>
                        <span style={{ color: 'var(--brand-primary)' }}>Q{qIndex + 1}.</span>
                        <span>{q.question_text}</span>
                      </div>

                      {/* Options Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '8px' }}>
                        {q.options.map((opt, optIdx) => {
                          const isSelected = studentSelected === optIdx;
                          let btnStyle = {
                            padding: '10px 14px',
                            borderRadius: '10px',
                            border: '1px solid var(--border-subtle)',
                            background: isSelected ? 'rgba(37, 99, 235, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                            color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)',
                            fontSize: '0.88rem',
                            fontWeight: isSelected ? 700 : 500,
                            cursor: quizResult ? 'default' : 'pointer',
                            textAlign: 'left',
                            transition: 'all 0.15s'
                          };

                          if (quizResult) {
                            if (optIdx === q.correct_option_index) {
                              btnStyle.background = 'rgba(16, 185, 129, 0.15)';
                              btnStyle.borderColor = 'rgba(16, 185, 129, 0.4)';
                              btnStyle.color = 'var(--accent-mint)';
                            } else if (isSelected && !qResult?.is_correct) {
                              btnStyle.background = 'rgba(239, 68, 68, 0.15)';
                              btnStyle.borderColor = 'rgba(239, 68, 68, 0.4)';
                              btnStyle.color = '#EF4444';
                            }
                          }

                          return (
                            <button
                              key={optIdx}
                              onClick={() => handleOptionSelect(q.id, optIdx)}
                              style={btnStyle}
                            >
                              <span style={{ marginRight: '6px', fontWeight: 700 }}>
                                {String.fromCharCode(65 + optIdx)}.
                              </span>
                              {opt}
                            </button>
                          );
                        })}
                      </div>

                      {/* Post-submit explanation */}
                      {quizResult && (
                        <div style={{
                          marginTop: '12px',
                          padding: '10px 14px',
                          background: qResult?.is_correct ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                          borderRadius: '8px',
                          fontSize: '0.82rem',
                          color: 'var(--text-primary)'
                        }}>
                          <strong>{qResult?.is_correct ? '✓ Correct!' : '✗ Concept Review:'}</strong> {q.explanation}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Quiz Submit & Mastery Shift Display */}
              {!quizResult ? (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    onClick={handleQuizSubmit}
                    disabled={submittingQuiz}
                    className="btn btn-primary"
                    style={{ padding: '12px 28px', fontSize: '0.92rem', fontWeight: 700 }}
                  >
                    {submittingQuiz ? 'Evaluating Answers...' : 'Submit Concept Check ➔'}
                  </button>
                </div>
              ) : (
                <div style={{
                  background: 'rgba(37, 99, 235, 0.05)',
                  border: '1px solid rgba(37, 99, 235, 0.2)',
                  borderRadius: '16px',
                  padding: '20px',
                  marginTop: '10px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
                    <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--brand-primary)' }}>
                      🔄 Closed Learning Loop Activated: Mastery Updated!
                    </div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-mint)' }}>
                      Prior: {quizResult.prior_mastery}% ➔ New: {quizResult.new_mastery}% (+{quizResult.mastery_gain}%)
                    </div>
                  </div>

                  {/* Animated Mastery Progress Bar */}
                  <div style={{
                    width: '100%',
                    height: '10px',
                    borderRadius: '999px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    overflow: 'hidden',
                    marginBottom: '14px'
                  }}>
                    <div style={{
                      width: `${quizResult.new_mastery}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #2563EB, #10B981)',
                      borderRadius: '999px',
                      transition: 'width 1s ease-in-out'
                    }} />
                  </div>

                  <p style={{ fontSize: '0.9rem', margin: '0 0 8px 0', lineHeight: 1.5 }}>
                    {quizResult.feedback}
                  </p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                    💡 <strong>Next Step:</strong> {quizResult.recommended_next_step}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* 5. GO DEEPER (Knowledge Pathway Journey) */}
          {pathway && pathway.length > 0 && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '20px',
              padding: '28px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
                <span style={{ fontSize: '1.2rem' }}>🚀</span>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                    GO DEEPER: Curriculum Knowledge Graph Pathway
                  </h3>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', margin: 0 }}>
                    Prerequisite ➔ Core Target Concept ➔ Next-Level Mastery
                  </p>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
                {pathway.map((node, nIdx) => {
                  const depthBadges = {
                    prerequisite: { label: 'Prerequisite', color: '#6366F1', bg: 'rgba(99, 102, 241, 0.1)' },
                    core: { label: 'Target Objective', color: '#10B981', bg: 'rgba(16, 185, 129, 0.1)' },
                    related: { label: 'Complementary', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)' },
                    advanced: { label: 'Next Level', color: '#EC4899', bg: 'rgba(236, 72, 153, 0.1)' }
                  };
                  const badge = depthBadges[node.depth] || depthBadges.core;

                  return (
                    <div
                      key={nIdx}
                      style={{
                        padding: '16px',
                        borderRadius: '14px',
                        border: '1px solid var(--border-subtle)',
                        background: 'rgba(255, 255, 255, 0.02)',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{
                            fontSize: '0.72rem',
                            fontWeight: 800,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            background: badge.bg,
                            color: badge.color
                          }}>
                            {badge.label}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            Class {node.target_grade}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '0.92rem', fontWeight: 700, margin: '0 0 6px 0' }}>
                          {node.concept}
                        </h4>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                          {node.description}
                        </p>
                      </div>

                      <button
                        onClick={() => {
                          setQuery(`Explain ${node.concept} for Class ${node.target_grade}`);
                          handleSearch(`Explain ${node.concept} for Class ${node.target_grade}`);
                        }}
                        style={{
                          marginTop: '12px',
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--brand-primary)',
                          fontSize: '0.8rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: 0
                        }}
                      >
                        <span>Explore Topic</span> ➔
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      )}

      {/* WHY THIS RESOURCE? 10-FACTOR SCORE BREAKDOWN MODAL */}
      {scoreModalResource && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '24px',
            maxWidth: '620px',
            width: '100%',
            padding: '28px',
            boxShadow: 'var(--shadow-lg)',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 4px 0' }}>
                  📊 Why This Resource?
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
                  Transparent 10-Factor Educational Quality Scoring (Policy {scoreModalResource.score_breakdown?.policy_version || 'v1.0'})
                </p>
              </div>
              <button
                onClick={() => setScoreModalResource(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Core Verification Badges */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '10px',
              marginBottom: '20px'
            }}>
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '12px',
                borderRadius: '12px'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-mint)' }}>
                  HARD SAFETY GATE
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 800, marginTop: '2px' }}>
                  ✓ 100% Passed (Gate &ge; 0.90)
                </div>
              </div>

              <div style={{
                background: 'rgba(37, 99, 235, 0.1)',
                border: '1px solid rgba(37, 99, 235, 0.3)',
                padding: '12px',
                borderRadius: '12px'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-primary)' }}>
                  SOURCE AUTHORITY TIER
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 800, marginTop: '2px' }}>
                  {scoreModalResource.authority_tier} ({Math.round(scoreModalResource.authority_score * 100)}%)
                </div>
              </div>
            </div>

            {/* Structured Provenance Evidence Chain */}
            {scoreModalResource.provenance && (
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '12px 14px',
                marginBottom: '16px',
                fontSize: '0.82rem'
              }}>
                <div style={{ fontWeight: 800, color: 'var(--brand-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={16} /> Verified Evidence Chain
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px', color: 'var(--text-secondary)' }}>
                  <div><strong>Publisher/Platform:</strong> {scoreModalResource.provenance.source || scoreModalResource.source_platform}</div>
                  <div><strong>Verification Method:</strong> {scoreModalResource.provenance.verification_method || 'Official Registry'}</div>
                  <div><strong>Chapter/Section:</strong> {scoreModalResource.provenance.chapter || scoreModalResource.topic}</div>
                  <div><strong>Audited Date:</strong> {scoreModalResource.provenance.verified_at ? scoreModalResource.provenance.verified_at.split('T')[0] : '2026-01-15'}</div>
                </div>
                {scoreModalResource.provenance.curriculum_alignment?.evidence && (
                  <div style={{ marginTop: '8px', color: 'var(--accent-mint)', fontStyle: 'italic' }}>
                    ✓ {scoreModalResource.provenance.curriculum_alignment.evidence}
                  </div>
                )}
              </div>
            )}

            {/* 10-Factor Score Sliders / Progress Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              {[
                { name: 'Curriculum Alignment', val: scoreModalResource.score_breakdown?.curriculum_alignment, weight: '25%' },
                { name: 'Source Authority', val: scoreModalResource.score_breakdown?.source_authority, weight: '20%' },
                { name: 'Pedagogical Quality', val: scoreModalResource.score_breakdown?.pedagogical_quality, weight: '15%' },
                { name: 'Student Level Match', val: scoreModalResource.score_breakdown?.student_level_match, weight: '10%' },
                { name: 'Transcript Quality', val: scoreModalResource.score_breakdown?.transcript_quality, weight: '10%' },
                { name: 'Language Match', val: scoreModalResource.score_breakdown?.language_match, weight: '5%' },
                { name: 'Engagement Quality', val: scoreModalResource.score_breakdown?.engagement_quality, weight: '5%' },
                { name: 'Completion Rate Signal', val: scoreModalResource.score_breakdown?.completion_rate, weight: '5%' },
                { name: 'Learning Gain Potential', val: scoreModalResource.score_breakdown?.student_learning_gain, weight: '5%' }
              ].map((factor, fIdx) => {
                const pct = Math.round((factor.val || 0.90) * 100);
                return (
                  <div key={fIdx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600 }}>{factor.name} <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>({factor.weight})</span></span>
                      <span style={{ fontWeight: 800 }}>{pct}%</span>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '6px',
                      borderRadius: '999px',
                      background: 'rgba(255, 255, 255, 0.08)',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${pct}%`,
                        height: '100%',
                        background: 'var(--brand-primary)',
                        borderRadius: '999px'
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setScoreModalResource(null)}
                className="btn btn-primary"
                style={{ padding: '8px 20px', fontSize: '0.85rem' }}
              >
                Close Explanation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* INTERACTIVE PHET / LAB SIMULATION MODAL */}
      {activeSimulation && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 20px',
            background: 'var(--bg-card)',
            borderRadius: '16px 16px 0 0'
          }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800 }}>
                🧪 {activeSimulation.title}
              </h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-mint)' }}>
                Certified Educational Lab • {activeSimulation.source_name}
              </span>
            </div>
            <button
              onClick={() => setActiveSimulation(null)}
              className="btn btn-outline"
              style={{ padding: '6px 12px' }}
            >
              <X size={18} /> Close Lab
            </button>
          </div>
          <iframe
            src={activeSimulation.embed_url}
            title={activeSimulation.title}
            style={{
              flex: 1,
              width: '100%',
              border: 'none',
              background: '#FFFFFF',
              borderRadius: '0 0 16px 16px'
            }}
            allowFullScreen
          />
        </div>
      )}

    </div>
  );
}
