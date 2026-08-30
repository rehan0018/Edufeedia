import React, { useState, useEffect } from 'react';
import { Search, BookOpen, PlayCircle, CheckCircle2, Award, Clock, ShieldCheck, Sparkles, Filter } from 'lucide-react';
import { fetchExploreCatalog } from '../services/api';

const SUBJECT_CATEGORIES = ['All', 'Computer Science', 'Science', 'Mathematics', 'Coding', 'Space'];

export default function ExploreCatalog({ onOpenLesson, onOpenQuiz }) {
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [selectedGrade, setSelectedGrade] = useState('');
  const [error, setError] = useState('');

  const loadCatalog = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchExploreCatalog({
        query: searchQuery,
        subject: selectedSubject,
        grade_level: selectedGrade ? parseInt(selectedGrade) : undefined
      });
      setCatalog(data);
    } catch (err) {
      setError('Unable to load catalog items from the learning server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadCatalog();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedSubject, selectedGrade]);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px 16px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Sparkles size={24} color="var(--accent-cyan)" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Explore Curriculum Catalog</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Search trusted, verified lessons and diagnostic assessments across STEM and Computer Science for Grades 9–10.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '28px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
          <div style={{ flex: '1 1 300px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
            <input
              id="catalog-search-input"
              type="text"
              aria-label="Search curriculum concepts"
              placeholder="Search concepts (e.g. 'computer networks', 'electricity', 'newton', 'quadratic')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px 12px 42px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-space)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Filter size={16} color="var(--text-muted)" />
            <select
              id="catalog-grade-filter"
              aria-label="Filter by Grade Level"
              value={selectedGrade}
              onChange={(e) => setSelectedGrade(e.target.value)}
              style={{
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-space)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="">All Grades</option>
              <option value="9">Grade 9</option>
              <option value="10">Grade 10</option>
            </select>
          </div>
        </div>

        {/* Subject Category Pills */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {SUBJECT_CATEGORIES.map((subj) => (
            <button
              key={subj}
              onClick={() => setSelectedSubject(subj)}
              className="btn btn-sm"
              style={{
                background: selectedSubject === subj ? 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))' : 'var(--bg-space)',
                color: selectedSubject === subj ? '#0a0f1d' : 'var(--text-secondary)',
                fontWeight: selectedSubject === subj ? 700 : 500,
                border: selectedSubject === subj ? 'none' : '1px solid var(--border-subtle)',
                borderRadius: '20px',
                padding: '6px 14px'
              }}
            >
              {subj}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div style={{
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          background: 'hsla(346, 84%, 61%, 0.15)',
          border: '1px solid var(--accent-rose)',
          color: 'var(--accent-rose)',
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-secondary)' }}>
          <div className="spinner" style={{ margin: '0 auto 16px auto' }}></div>
          <p>Querying verified curriculum resources...</p>
        </div>
      ) : catalog.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px 24px' }}>
          <BookOpen size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>No matching curriculum items found</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto 16px auto' }}>
            Try adjusting your search keywords or switching subject filters to discover lessons.
          </p>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => { setSearchQuery(''); setSelectedSubject('All'); setSelectedGrade(''); }}
          >
            Clear Filters
          </button>
        </div>
      ) : (
        /* Catalog Cards Grid */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '20px'
        }}>
          {catalog.map((item) => (
            <div
              key={item.id}
              className="glass-panel"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '20px',
                transition: 'transform 0.2s ease, border-color 0.2s ease',
                border: item.is_completed ? '1px solid hsla(160, 84%, 39%, 0.4)' : '1px solid var(--border-subtle)'
              }}
            >
              <div>
                {/* Header badges */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    padding: '4px 10px',
                    borderRadius: '12px',
                    background: item.subject === 'Computer Science' || item.subject === 'Coding'
                      ? 'hsla(186, 100%, 50%, 0.15)'
                      : item.subject === 'Mathematics'
                      ? 'hsla(263, 70%, 58%, 0.15)'
                      : 'hsla(160, 84%, 39%, 0.15)',
                    color: item.subject === 'Computer Science' || item.subject === 'Coding'
                      ? 'var(--accent-cyan)'
                      : item.subject === 'Mathematics'
                      ? 'var(--accent-purple)'
                      : 'var(--accent-emerald)'
                  }}>
                    {item.subject} • Grade {item.grade_level}
                  </span>

                  {item.is_completed && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-emerald)', fontSize: '0.8rem', fontWeight: 600 }}>
                      <CheckCircle2 size={15} /> Completed
                    </span>
                  )}
                </div>

                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px', lineHeight: 1.35 }}>
                  {item.title}
                </h3>

                <p style={{
                  color: 'var(--text-secondary)',
                  fontSize: '0.88rem',
                  lineHeight: 1.5,
                  marginBottom: '16px',
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  {item.description}
                </p>
              </div>

              <div>
                {/* Metadata Row */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  paddingTop: '12px',
                  borderTop: '1px solid var(--border-subtle)',
                  marginBottom: '16px',
                  fontSize: '0.82rem',
                  color: 'var(--text-muted)'
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> {item.duration_minutes ?? 12} min
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={14} color="var(--accent-emerald)" /> Safe EDU
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Award size={14} color="var(--accent-gold)" /> {item.edu_score ?? 98}% Score
                  </span>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ flex: 1, justifyContent: 'center' }}
                    onClick={() => onOpenLesson(item)}
                  >
                    <PlayCircle size={16} /> Open Lesson
                  </button>
                  <button
                    className="btn btn-outline btn-sm"
                    style={{ flex: 1, justifyContent: 'center' }}
                    onClick={() => onOpenQuiz(item)}
                  >
                    <BookOpen size={16} /> Take Quiz
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
