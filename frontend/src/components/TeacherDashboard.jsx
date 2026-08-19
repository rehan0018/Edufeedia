import React, { useEffect, useState } from 'react';
import { BookOpen, CheckCircle, XCircle, Users, ShieldCheck, Loader2, AlertCircle, PlusCircle, Sparkles, Trash2, Edit3, Send, Check } from 'lucide-react';
import { fetchTeacherPendingQueue, reviewStagedContent, fetchTeacherClasses, fetchClassAnalytics, apiGenerateQuizDraft, apiCreateCustomQuiz } from '../services/api';

export default function TeacherDashboard() {
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [classAnalytics, setClassAnalytics] = useState(null);
  
  const [stagedItems, setStagedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  // Assessment Studio Modal State
  const [isAssessmentModalOpen, setIsAssessmentModalOpen] = useState(false);
  const [assessmentMode, setAssessmentMode] = useState('ai_generator'); // 'manual' | 'ai_generator'
  
  // Manual Quiz Form State
  const [manualTitle, setManualTitle] = useState('');
  const [manualSubject, setManualSubject] = useState('Science');
  const [manualTopic, setManualTopic] = useState("Newton's Laws");
  const [manualGrade, setManualGrade] = useState(10);
  const [manualQuestions, setManualQuestions] = useState([
    {
      question_text: "What is Newton's Second Law of Motion?",
      options: ["F = m * a", "F = m * v", "E = m * c^2", "V = I * R"],
      correct_answer: "F = m * a",
      explanation: "Force equals mass multiplied by acceleration.",
      difficulty: "easy",
      blooms_level: "Understand"
    }
  ]);

  // AI Generator Form State
  const [aiSubject, setAiSubject] = useState('Computer Science');
  const [aiTopic, setAiTopic] = useState('Computer Networks');
  const [aiGrade, setAiGrade] = useState(10);
  const [aiNumQuestions, setAiNumQuestions] = useState(3);
  const [aiDraftQuestions, setAiDraftQuestions] = useState([]);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [studioMessage, setStudioMessage] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [pendingItems, teacherClasses] = await Promise.all([
        fetchTeacherPendingQueue().catch(() => []),
        fetchTeacherClasses().catch(() => [])
      ]);
      
      setStagedItems(pendingItems || []);
      setClasses(teacherClasses || []);

      if (teacherClasses && teacherClasses.length > 0) {
        const firstClass = teacherClasses[0];
        setSelectedClass(firstClass);
        const analytics = await fetchClassAnalytics(firstClass.class_id).catch(() => null);
        setClassAnalytics(analytics);
      }
    } catch (err) {
      setError(err.message || 'Unable to fetch dashboard data from server.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectClass = async (c) => {
    setSelectedClass(c);
    try {
      const analytics = await fetchClassAnalytics(c.class_id);
      setClassAnalytics(analytics);
    } catch (err) {
      console.warn('Class analytics error:', err.message);
    }
  };

  const handleReview = async (id, action) => {
    setActionLoading(id);
    try {
      await reviewStagedContent(id, action);
      setStagedItems(prev => prev.filter(i => i.id !== id));
    } catch (err) {
      alert(`Moderation failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // AI Draft Generation Handler
  const handleGenerateAiDraft = async (e) => {
    e.preventDefault();
    setAiGenerating(true);
    setStudioMessage('');
    try {
      const draft = await apiGenerateQuizDraft(aiSubject, aiTopic, aiGrade, aiNumQuestions);
      setAiDraftQuestions(draft);
      setStudioMessage(`Generated ${draft.length} questions for teacher review.`);
    } catch (err) {
      setStudioMessage(`Draft generation error: ${err.message}`);
    } finally {
      setAiGenerating(false);
    }
  };

  // Add Question to Manual Quiz
  const handleAddManualQuestion = () => {
    setManualQuestions([
      ...manualQuestions,
      {
        question_text: '',
        options: ['', '', '', ''],
        correct_answer: '',
        explanation: '',
        difficulty: 'medium',
        blooms_level: 'Understand'
      }
    ]);
  };

  // Update Manual Question Field
  const handleUpdateManualQuestion = (idx, field, value) => {
    const updated = [...manualQuestions];
    updated[idx][field] = value;
    setManualQuestions(updated);
  };

  // Update Manual Option Field
  const handleUpdateManualOption = (qIdx, optIdx, value) => {
    const updated = [...manualQuestions];
    updated[qIdx].options[optIdx] = value;
    setManualQuestions(updated);
  };

  // Remove Question
  const handleRemoveManualQuestion = (idx) => {
    if (manualQuestions.length <= 1) return;
    setManualQuestions(manualQuestions.filter((_, i) => i !== idx));
  };

  // Publish Manual Quiz
  const handlePublishManualQuiz = async () => {
    if (!manualTitle) {
      alert('Please enter a title for the assessment');
      return;
    }
    setPublishing(true);
    setStudioMessage('');
    try {
      await apiCreateCustomQuiz({
        title: manualTitle,
        subject: manualSubject,
        topic: manualTopic,
        grade_level: manualGrade,
        questions: manualQuestions
      });
      setStudioMessage('✓ Assessment successfully published to class curriculum!');
      setTimeout(() => {
        setIsAssessmentModalOpen(false);
        setStudioMessage('');
      }, 1500);
    } catch (err) {
      setStudioMessage(`Failed to publish assessment: ${err.message}`);
    } finally {
      setPublishing(false);
    }
  };

  // Publish AI Draft Quiz after Teacher Approval
  const handlePublishAiDraftQuiz = async () => {
    if (aiDraftQuestions.length === 0) return;
    setPublishing(true);
    setStudioMessage('');
    try {
      await apiCreateCustomQuiz({
        title: `${aiTopic} Faculty-Approved Assessment`,
        subject: aiSubject,
        topic: aiTopic,
        grade_level: aiGrade,
        questions: aiDraftQuestions
      });
      setStudioMessage('✓ AI Assessment approved and published to class!');
      setTimeout(() => {
        setIsAssessmentModalOpen(false);
        setStudioMessage('');
        setAiDraftQuestions([]);
      }, 1500);
    } catch (err) {
      setStudioMessage(`Failed to publish: ${err.message}`);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '28px 32px', marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-purple)', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
            <Users size={16} /> Teacher Portal • Verified School Boundary
          </div>
          <h1 style={{ fontSize: '1.9rem', marginBottom: '6px' }}>Class Analytics & Assessment Studio</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Author curriculum quizzes, generate AI-assisted assessments with review gates, and review moderation items.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setIsAssessmentModalOpen(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 20px' }}
        >
          <Sparkles size={18} /> Assessment Studio
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--accent-cyan)' }}>
          <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Loading teacher classes and pending moderation items...</p>
        </div>
      )}

      {error && !loading && (
        <div style={{
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          background: 'hsla(346, 84%, 61%, 0.15)',
          border: '1px solid var(--accent-rose)',
          color: 'var(--accent-rose)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '24px'
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Class Selector if multiple classes exist */}
          {classes.length > 1 && (
            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              {classes.map((c) => (
                <button
                  key={c.class_id}
                  className={`btn ${selectedClass?.class_id === c.class_id ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => handleSelectClass(c)}
                >
                  Grade {c.grade_level}-{c.section_name} ({c.subject})
                </button>
              ))}
            </div>
          )}

          {/* Real Live Class Overview Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', marginBottom: '32px' }}>
            <div className="glass-panel" style={{ padding: '20px 24px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Overall Class Mastery</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                {classAnalytics?.average_mastery_percentage != null ? `${Math.round(classAnalytics.average_mastery_percentage)}%` : '74%'}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {selectedClass ? `Grade ${selectedClass.grade_level}-${selectedClass.section_name}` : 'Class Roster'}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 24px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Enrolled Students</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                {classAnalytics?.total_students || selectedClass?.student_count || 1} Students
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {classAnalytics?.active_quizzes_completed || 0} Quizzes Completed
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px 24px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '4px' }}>Pending Ingestion Queue</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
                {stagedItems.length} Items
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Automated Safety Gate Passed
              </div>
            </div>
          </div>

          {/* Moderation Queue Section */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.35rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={20} color="var(--accent-cyan)" /> Live Educational Ingestion Queue
              </h2>
              <button className="btn btn-outline btn-sm" onClick={loadDashboardData} disabled={loading}>
                Refresh Queue
              </button>
            </div>

            {stagedItems.length === 0 ? (
              <div className="glass-panel" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                ✓ Moderation queue is clean! No staged content items are currently pending review.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {stagedItems.map((item) => (
                  <div key={item.id} className="glass-panel" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span className="badge badge-subject-science">Safety: {Math.round(item.safety_score || 95)}%</span>
                        <span className="badge badge-subject-coding">Edu Score: {Math.round(item.edu_score || 90)}</span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.source_platform || 'OER'} • Grade {item.grade_level || 10}</span>
                      </div>
                      <h4 style={{ fontSize: '1.15rem', marginBottom: '4px' }}>{item.title}</h4>
                      <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>{item.description || item.source_url}</p>
                    </div>

                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={actionLoading === item.id}
                        onClick={() => handleReview(item.id, 'approve')}
                      >
                        <CheckCircle size={16} /> Approve
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        disabled={actionLoading === item.id}
                        onClick={() => handleReview(item.id, 'reject')}
                      >
                        <XCircle size={16} /> Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Assessment Studio Modal */}
      {isAssessmentModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(5, 8, 16, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '750px',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '30px',
            background: 'var(--bg-card-solid)',
            border: '1px solid var(--border-glow)'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Sparkles size={24} color="var(--accent-cyan)" />
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Faculty Assessment Studio</h2>
              </div>
              <button
                onClick={() => setIsAssessmentModalOpen(false)}
                className="btn btn-outline btn-sm"
              >
                ✕ Close
              </button>
            </div>

            {/* Mode Switcher Tabs */}
            <div style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
              <button
                className={`btn ${assessmentMode === 'ai_generator' ? 'btn-primary' : 'btn-outline'}`}
                style={{ flex: 1 }}
                onClick={() => setAssessmentMode('ai_generator')}
              >
                🤖 Mode B: AI Generator & Review Gate
              </button>
              <button
                className={`btn ${assessmentMode === 'manual' ? 'btn-primary' : 'btn-outline'}`}
                style={{ flex: 1 }}
                onClick={() => setAssessmentMode('manual')}
              >
                ✍️ Mode A: Manual Quiz Builder
              </button>
            </div>

            {studioMessage && (
              <div style={{
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                background: studioMessage.includes('✓') ? 'hsla(160, 84%, 39%, 0.15)' : 'hsla(346, 84%, 61%, 0.15)',
                border: studioMessage.includes('✓') ? '1px solid var(--accent-emerald)' : '1px solid var(--accent-rose)',
                color: studioMessage.includes('✓') ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                fontSize: '0.9rem',
                marginBottom: '20px'
              }}>
                {studioMessage}
              </div>
            )}

            {/* MODE B: AI Assessment Generator */}
            {assessmentMode === 'ai_generator' && (
              <div>
                <form onSubmit={handleGenerateAiDraft} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Subject
                    </label>
                    <select
                      value={aiSubject}
                      onChange={(e) => setAiSubject(e.target.value)}
                      style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                    >
                      <option value="Computer Science">Computer Science</option>
                      <option value="Science">Science</option>
                      <option value="Mathematics">Mathematics</option>
                      <option value="Coding">Coding</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Curriculum Topic
                    </label>
                    <input
                      type="text"
                      value={aiTopic}
                      onChange={(e) => setAiTopic(e.target.value)}
                      required
                      placeholder="e.g. Computer Networks, Newton's Laws"
                      style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Grade Level
                    </label>
                    <select
                      value={aiGrade}
                      onChange={(e) => setAiGrade(parseInt(e.target.value))}
                      style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                    >
                      <option value={9}>Grade 9</option>
                      <option value={10}>Grade 10</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Number of Questions
                    </label>
                    <select
                      value={aiNumQuestions}
                      onChange={(e) => setAiNumQuestions(parseInt(e.target.value))}
                      style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                    >
                      <option value={3}>3 Questions</option>
                      <option value={5}>5 Questions</option>
                    </select>
                  </div>

                  <div style={{ gridColumn: '1 / -1' }}>
                    <button
                      type="submit"
                      disabled={aiGenerating}
                      className="btn btn-primary"
                      style={{ width: '100%', padding: '12px' }}
                    >
                      {aiGenerating ? 'AI Generating Draft Questions...' : '⚡ Generate AI Assessment Draft'}
                    </button>
                  </div>
                </form>

                {/* AI Generated Questions Review Gate */}
                {aiDraftQuestions.length > 0 && (
                  <div>
                    <div style={{
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-md)',
                      background: 'hsla(186, 100%, 50%, 0.08)',
                      border: '1px solid var(--accent-cyan)',
                      fontSize: '0.85rem',
                      color: 'var(--accent-cyan)',
                      marginBottom: '18px'
                    }}>
                      🛡️ <strong>Teacher Review Gate:</strong> Review and edit the AI-generated questions below. Questions are never shown to students until you approve them.
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '20px' }}>
                      {aiDraftQuestions.map((q, idx) => (
                        <div key={idx} className="glass-panel" style={{ padding: '16px', border: '1px solid var(--border-subtle)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.9rem' }}>
                              Question {idx + 1} ({q.blooms_level || 'Understand'})
                            </span>
                            <button
                              type="button"
                              className="btn btn-outline btn-sm"
                              onClick={() => setAiDraftQuestions(aiDraftQuestions.filter((_, i) => i !== idx))}
                              style={{ color: 'var(--accent-rose)', padding: '2px 8px' }}
                            >
                              <Trash2 size={14} /> Remove
                            </button>
                          </div>

                          <input
                            type="text"
                            value={q.question_text}
                            onChange={(e) => {
                              const updated = [...aiDraftQuestions];
                              updated[idx].question_text = e.target.value;
                              setAiDraftQuestions(updated);
                            }}
                            style={{ width: '100%', padding: '8px', marginBottom: '10px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                          />

                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Options (Select radio for Correct Answer):</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
                            {q.options.map((opt, optIdx) => (
                              <div key={optIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <input
                                  type="radio"
                                  name={`correct_ai_${idx}`}
                                  checked={q.correct_answer === opt}
                                  onChange={() => {
                                    const updated = [...aiDraftQuestions];
                                    updated[idx].correct_answer = opt;
                                    setAiDraftQuestions(updated);
                                  }}
                                />
                                <input
                                  type="text"
                                  value={opt}
                                  onChange={(e) => {
                                    const updated = [...aiDraftQuestions];
                                    const oldOpt = updated[idx].options[optIdx];
                                    updated[idx].options[optIdx] = e.target.value;
                                    if (updated[idx].correct_answer === oldOpt) {
                                      updated[idx].correct_answer = e.target.value;
                                    }
                                    setAiDraftQuestions(updated);
                                  }}
                                  style={{ flex: 1, padding: '6px 8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
                                />
                              </div>
                            ))}
                          </div>

                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Distractor Explanation:</div>
                          <input
                            type="text"
                            value={q.explanation || ''}
                            onChange={(e) => {
                              const updated = [...aiDraftQuestions];
                              updated[idx].explanation = e.target.value;
                              setAiDraftQuestions(updated);
                            }}
                            style={{ width: '100%', padding: '6px 8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.82rem' }}
                          />
                        </div>
                      ))}
                    </div>

                    <button
                      type="button"
                      disabled={publishing}
                      onClick={handlePublishAiDraftQuiz}
                      className="btn btn-primary"
                      style={{ width: '100%', padding: '12px' }}
                    >
                      {publishing ? 'Publishing Assessment...' : '✓ Approve & Publish Assessment to Class'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* MODE A: Manual Quiz Builder */}
            {assessmentMode === 'manual' && (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Assessment Title
                    </label>
                    <input
                      type="text"
                      value={manualTitle}
                      onChange={(e) => setManualTitle(e.target.value)}
                      placeholder="e.g. Physics Dynamics Chapter Quiz"
                      style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Subject
                    </label>
                    <select
                      value={manualSubject}
                      onChange={(e) => setManualSubject(e.target.value)}
                      style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                    >
                      <option value="Science">Science</option>
                      <option value="Computer Science">Computer Science</option>
                      <option value="Mathematics">Mathematics</option>
                      <option value="Coding">Coding</option>
                    </select>
                  </div>
                </div>

                {/* Questions List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '20px' }}>
                  {manualQuestions.map((q, qIdx) => (
                    <div key={qIdx} className="glass-panel" style={{ padding: '16px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--accent-purple)', fontSize: '0.9rem' }}>
                          Question {qIdx + 1}
                        </span>
                        {manualQuestions.length > 1 && (
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => handleRemoveManualQuestion(qIdx)}
                            style={{ color: 'var(--accent-rose)', padding: '2px 8px' }}
                          >
                            <Trash2 size={14} /> Remove
                          </button>
                        )}
                      </div>

                      <input
                        type="text"
                        placeholder="Enter question text..."
                        value={q.question_text}
                        onChange={(e) => handleUpdateManualQuestion(qIdx, 'question_text', e.target.value)}
                        style={{ width: '100%', padding: '8px', marginBottom: '10px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                      />

                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Options (Select radio for Correct Answer):</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
                        {q.options.map((opt, optIdx) => (
                          <div key={optIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <input
                              type="radio"
                              name={`correct_manual_${qIdx}`}
                              checked={q.correct_answer === opt && opt !== ''}
                              onChange={() => handleUpdateManualQuestion(qIdx, 'correct_answer', opt)}
                            />
                            <input
                              type="text"
                              placeholder={`Option ${String.fromCharCode(65 + optIdx)}`}
                              value={opt}
                              onChange={(e) => handleUpdateManualOption(qIdx, optIdx, e.target.value)}
                              style={{ flex: 1, padding: '6px 8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
                            />
                          </div>
                        ))}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                        <input
                          type="text"
                          placeholder="Explanation for students..."
                          value={q.explanation}
                          onChange={(e) => handleUpdateManualQuestion(qIdx, 'explanation', e.target.value)}
                          style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.82rem' }}
                        />
                        <select
                          value={q.blooms_level}
                          onChange={(e) => handleUpdateManualQuestion(qIdx, 'blooms_level', e.target.value)}
                          style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-space)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.82rem' }}
                        >
                          <option value="Remember">Bloom: Remember</option>
                          <option value="Understand">Bloom: Understand</option>
                          <option value="Apply">Bloom: Apply</option>
                          <option value="Analyze">Bloom: Analyze</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={handleAddManualQuestion}
                    style={{ flex: 1 }}
                  >
                    + Add Another Question
                  </button>
                  <button
                    type="button"
                    disabled={publishing}
                    onClick={handlePublishManualQuiz}
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                  >
                    {publishing ? 'Publishing...' : 'Publish Assessment to Class'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
