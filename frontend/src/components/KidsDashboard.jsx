import React, { useState, useEffect } from 'react';
import {
  Sparkles, Star, Award, Flame, Moon, Compass, Lock,
  Play, BookOpen, CheckCircle2, Search, ArrowRight, HelpCircle,
  RotateCcw, Info, Heart, Volume2, ShieldCheck, ChevronRight
} from 'lucide-react';
import {
  fetchKidsAdventure,
  fetchKidsFeed,
  fetchKidsAchievements,
  fetchKidsScreenTimeStatus,
  recordKidsActivity,
  submitKidsQuiz,
  searchKidsContent
} from '../services/api';
import BedtimeCurfewScreen from './BedtimeCurfewScreen';
import InteractiveActivityPlayer from './InteractiveActivityPlayer';
import WhySeeingThisModal from './WhySeeingThisModal';

export default function KidsDashboard({ child, onOpenParentGate, onSwitchChild }) {
  const [adventure, setAdventure] = useState(null);
  const [feed, setFeed] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [screenTimeStatus, setScreenTimeStatus] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(true);

  // Active Interactive Player item
  const [activeInteractiveItem, setActiveInteractiveItem] = useState(null);

  // Why am I seeing this modal state
  const [whyModalOpen, setWhyModalOpen] = useState(false);
  const [activeWhyData, setActiveWhyData] = useState(null);

  // Mini-Quiz modal state
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [quizResult, setQuizResult] = useState(null);
  const [selectedQuizOption, setSelectedQuizOption] = useState('');

  const childId = child?.id || 'c-aarav-07';

  const loadKidsData = async () => {
    try {
      setLoading(true);
      const [advRes, feedRes, achRes, stRes] = await Promise.all([
        fetchKidsAdventure(childId).catch(() => null),
        fetchKidsFeed(childId, 8).catch(() => ({ items: [] })),
        fetchKidsAchievements(childId).catch(() => ({ achievements: [] })),
        fetchKidsScreenTimeStatus(childId).catch(() => null)
      ]);

      setAdventure(advRes);
      setFeed(feedRes?.items || []);
      setAchievements(achRes?.achievements || []);
      setScreenTimeStatus(stRes);
      setLoading(false);
    } catch (err) {
      console.error("Error loading Kids Mode data:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKidsData();
  }, [childId]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const res = await searchKidsContent(childId, searchQuery);
      setSearchResults(res.items || []);
    } catch (err) {
      console.error("Kids search error:", err);
    }
  };

  const handleOpenWhySeeingThis = (item) => {
    setActiveWhyData({
      title: item.title,
      reasons: item.why_am_i_seeing_this || [
        `Designed for ${child?.name || 'your child'}'s age group.`,
        `Category '${item.category}' is approved in parent controls.`,
        "Promotes a healthy learning balance without repetitive watch loops."
      ],
      learning_balance_note: "Balances STEM concepts with creative art and life skills."
    });
    setWhyModalOpen(true);
  };

  const handleCompleteActivity = async (itemId, reaction) => {
    try {
      await recordKidsActivity(childId, {
        content_item_id: itemId,
        activity_type: 'interactive',
        dwell_time_seconds: 240,
        completed: true,
        child_reaction: reaction
      });
      loadKidsData(); // Refresh stars and streak
    } catch (err) {
      console.error("Failed to record activity:", err);
    }
  };

  const handleQuizSubmit = async (option) => {
    setSelectedQuizOption(option);
    try {
      const res = await submitKidsQuiz(childId, "k-quiz-plant-01", option);
      setQuizResult(res);
    } catch (err) {
      console.error("Quiz submission error:", err);
    }
  };

  // If bedtime curfew or daily limit is locked, render the friendly curfew screen
  if (screenTimeStatus?.is_locked) {
    return (
      <BedtimeCurfewScreen
        childName={child?.name || 'Aarav'}
        curfewHours={screenTimeStatus.curfew_hours}
        message={screenTimeStatus.lock_message}
        onOpenParentGate={onOpenParentGate}
      />
    );
  }

  const categories = [
    { id: 'ALL', label: '🌟 All Adventures' },
    { id: 'Life Skills', label: '💰 Money & Life Skills' },
    { id: 'STEM', label: '🔬 Science & Space' },
    { id: 'Creativity', label: '🎨 Art & Origami' },
    { id: 'Philosophy & Values', label: '🪷 Values & Stories' },
    { id: 'World', label: '🌍 World & Nature' }
  ];

  const displayedItems = searchResults !== null
    ? searchResults
    : (selectedCategory === 'ALL' ? feed : feed.filter(f => f.category === selectedCategory));

  return (
    <div className="kids-mode-wrapper" style={{ padding: '24px 20px', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

        {/* Top Floating Mascot & Parent Gate Bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(12px)',
          borderRadius: '32px',
          padding: '14px 24px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.06)',
          border: '3px solid #E2DED0',
          marginBottom: '28px',
          flexWrap: 'wrap',
          gap: '14px'
        }}>
          {/* Mascot & Name */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div className="mascot-avatar-frame" style={{ width: '60px', height: '60px', fontSize: '2rem' }}>
              {child?.avatar_mascot === 'dino' ? '🦖' : (child?.avatar_mascot === 'robot' ? '🤖' : '🦊')}
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#E85A4F', textTransform: 'uppercase' }}>
                EduFeedia Kids Mode
              </div>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0 }}>
                Hi, {child?.name || 'Aarav'}! 🚀
              </h1>
            </div>
          </div>

          {/* Stars & Streak Counter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, #FFD166 0%, #FFB703 100%)',
              color: '#78350F',
              padding: '8px 16px',
              borderRadius: '20px',
              fontWeight: 800,
              fontSize: '1rem',
              boxShadow: '0 4px 10px rgba(255, 183, 3, 0.25)'
            }}>
              <Star size={18} fill="#78350F" />
              <span>{child?.stars_count || 18} Stars</span>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(232, 90, 79, 0.12)',
              color: '#E85A4F',
              padding: '8px 16px',
              borderRadius: '20px',
              fontWeight: 800,
              fontSize: '1rem'
            }}>
              <Flame size={18} />
              <span>{child?.streak_count || 5} Day Streak</span>
            </div>

            {/* Parent Gate Lock */}
            <button
              onClick={onOpenParentGate}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: '#2563EB',
                color: '#FFF',
                border: 'none',
                padding: '10px 18px',
                borderRadius: '20px',
                fontWeight: 700,
                fontSize: '0.88rem',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
              }}
            >
              <Lock size={16} /> Parent Hub
            </button>
          </div>
        </div>

        {/* 🌟 Section 1: Today's Adventure (5-Step Linear Learning Quest) */}
        {adventure && (
          <div className="kids-card" style={{ padding: '28px 32px', marginBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <span className="kids-pill-badge" style={{ background: 'rgba(255, 122, 89, 0.15)', color: '#FF7A59', marginBottom: '6px' }}>
                  🌟 Today's Adventure Quest
                </span>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '4px 0 0 0' }}>
                  {adventure.theme_title}
                </h2>
              </div>

              <div style={{
                background: 'rgba(52, 191, 163, 0.15)',
                color: '#0D9488',
                padding: '6px 16px',
                borderRadius: '20px',
                fontWeight: 800,
                fontSize: '0.9rem'
              }}>
                Step 3 of 5 In Progress ✨
              </div>
            </div>

            {/* 5 Milestone Steps */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginBottom: '20px' }}>
              {adventure.steps.map((step) => (
                <div
                  key={step.step_number}
                  className={`kids-adventure-step ${step.status}`}
                  style={{
                    cursor: step.step_type === 'interactive_activity' || step.step_type === 'mini_quiz' ? 'pointer' : 'default',
                    borderWidth: step.status === 'active' ? '3px' : '2px'
                  }}
                  onClick={() => {
                    if (step.step_type === 'interactive_activity') {
                      // Open interactive choice game
                      const interactiveItem = feed.find(f => f.interactive) || {
                        id: 'k-content-01',
                        title: "Money Adventure: The ₹100 Dilemma"
                      };
                      setActiveInteractiveItem(interactiveItem);
                    } else if (step.step_type === 'mini_quiz') {
                      setQuizModalOpen(true);
                      setQuizResult(null);
                    }
                  }}
                >
                  <div style={{
                    fontSize: '2rem',
                    width: '48px',
                    height: '48px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: '16px',
                    background: step.status === 'completed' ? 'rgba(52, 191, 163, 0.15)' : (step.status === 'active' ? 'rgba(232, 90, 79, 0.15)' : 'rgba(0,0,0,0.05)')
                  }}>
                    {step.status === 'completed' ? '✅' : step.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 800, color: step.status === 'active' ? '#E85A4F' : 'var(--text-muted)' }}>
                        STEP 0{step.step_number} • {step.duration_label}
                      </span>
                      {step.status === 'active' && (
                        <span style={{ background: '#E85A4F', color: '#FFF', padding: '2px 8px', borderRadius: '10px', fontSize: '0.72rem', fontWeight: 800 }}>
                          TAP TO PLAY 🎮
                        </span>
                      )}
                    </div>
                    <div style={{ fontWeight: 800, fontSize: '0.98rem', marginTop: '2px', color: 'var(--text-primary)' }}>
                      {step.title}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {step.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ textAlign: 'center' }}>
              <button
                onClick={() => {
                  const interactiveItem = feed.find(f => f.interactive) || {
                    id: 'k-content-01',
                    title: "Money Adventure: The ₹100 Dilemma"
                  };
                  setActiveInteractiveItem(interactiveItem);
                }}
                className="kids-btn-fun"
              >
                Continue Sparky's ₹100 Choice Game! 🎮 🚀
              </button>
            </div>
          </div>
        )}

        {/* Section 2: Safe Search & Filter Bar */}
        <div style={{ marginBottom: '24px' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={20} style={{ position: 'absolute', top: '16px', left: '20px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search safe cartoon lessons (e.g. Planets, Origami, Money, Nature)..."
                style={{
                  width: '100%',
                  padding: '14px 20px 14px 52px',
                  borderRadius: '24px',
                  border: '3px solid #E2DED0',
                  background: 'rgba(255, 255, 255, 0.9)',
                  fontSize: '1rem',
                  fontWeight: 600
                }}
              />
            </div>
            <button type="submit" className="kids-btn-fun" style={{ padding: '12px 24px' }}>
              Search 🔍
            </button>
            {searchResults !== null && (
              <button
                type="button"
                onClick={() => { setSearchResults(null); setSearchQuery(''); }}
                style={{ background: '#FFF', border: '2px solid #E2DED0', borderRadius: '20px', padding: '0 18px', fontWeight: 700, cursor: 'pointer' }}
              >
                Clear
              </button>
            )}
          </form>

          {/* Category Pills */}
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '6px' }}>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => { setSelectedCategory(cat.id); setSearchResults(null); }}
                style={{
                  whiteSpace: 'nowrap',
                  padding: '10px 18px',
                  borderRadius: '20px',
                  border: selectedCategory === cat.id ? '2px solid #E85A4F' : '2px solid #E2DED0',
                  background: selectedCategory === cat.id ? '#E85A4F' : 'rgba(255, 255, 255, 0.85)',
                  color: selectedCategory === cat.id ? '#FFFFFF' : 'var(--text-primary)',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Section 3: Recommended Learning Cards */}
        <div style={{ marginBottom: '36px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0 }}>
              Curated for {child?.name || 'Aarav'} 🌈
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              100% Fail-Closed Safety • Balanced Learning Engine
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            {displayedItems.map((item) => (
              <div key={item.id} className="kids-card" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <span className="kids-pill-badge" style={{ background: 'rgba(37, 99, 235, 0.12)', color: '#2563EB' }}>
                    {item.thumbnail_icon || '⭐'} {item.category}
                  </span>

                  <button
                    onClick={() => handleOpenWhySeeingThis(item)}
                    title="Why was this recommended?"
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                  >
                    <Info size={18} />
                  </button>
                </div>

                <h4 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '8px', lineHeight: '1.3' }}>
                  {item.title}
                </h4>

                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '18px' }}>
                  {item.description}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '2px solid #F0EDE4', paddingTop: '14px' }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                    ⏱️ {item.duration_label || '5 min lesson'}
                  </span>

                  <button
                    onClick={() => {
                      if (item.interactive || item.interactive_payload) {
                        setActiveInteractiveItem(item);
                      } else {
                        // Open quiz or activity
                        setQuizModalOpen(true);
                      }
                    }}
                    className="kids-btn-fun"
                    style={{ padding: '8px 18px', fontSize: '0.9rem' }}
                  >
                    Start 🎬 ✨
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: Star Badges & Curiosity Collection */}
        <div className="kids-card" style={{ padding: '28px 32px', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <Award size={26} color="#FFD166" />
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0 }}>
              {child?.name || 'Aarav'}'s Curiosity Badges
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
            {achievements.map((ach) => (
              <div
                key={ach.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '14px 18px',
                  borderRadius: '20px',
                  background: 'rgba(255, 209, 102, 0.12)',
                  border: '2px solid rgba(255, 209, 102, 0.4)'
                }}
              >
                <span style={{ fontSize: '2.4rem' }}>{ach.icon}</span>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.95rem' }}>{ach.title}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{ach.description}</div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#D97706', marginTop: '2px' }}>
                    ⭐ +{ach.stars_awarded} Stars
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Interactive Choice Game Modal */}
      {activeInteractiveItem && (
        <InteractiveActivityPlayer
          item={activeInteractiveItem}
          childId={childId}
          onClose={() => setActiveInteractiveItem(null)}
          onComplete={handleCompleteActivity}
        />
      )}

      {/* "Why am I seeing this?" Transparency Modal */}
      <WhySeeingThisModal
        isOpen={whyModalOpen}
        onClose={() => setWhyModalOpen(false)}
        explanation={activeWhyData}
      />

      {/* Kids Mini Quiz Modal */}
      {quizModalOpen && (
        <div className="modal-backdrop">
          <div className="kids-card" style={{ maxWidth: '520px', width: '100%', padding: '32px 28px', textAlign: 'center', position: 'relative' }}>
            <button
              onClick={() => setQuizModalOpen(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
            >
              <X size={20} />
            </button>

            <span style={{ fontSize: '3rem' }}>🌱</span>
            <span className="kids-pill-badge" style={{ background: 'rgba(52, 191, 163, 0.15)', color: '#0D9488', display: 'inline-flex', margin: '8px auto' }}>
              Mini Quiz Challenge
            </span>
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '8px' }}>
              What do green leaves need from the sky to bake their food?
            </h3>

            {!quizResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', margin: '20px 0' }}>
                {["Sunlight ☀️", "Chocolate 🍫", "Television 📺"].map((opt) => (
                  <button
                    key={opt}
                    onClick={() => handleQuizSubmit(opt.split(' ')[0])}
                    className="kids-reaction-btn"
                    style={{
                      flexDirection: 'row',
                      justifyContent: 'space-between',
                      padding: '14px 20px',
                      fontSize: '1rem',
                      fontWeight: 800
                    }}
                  >
                    <span>{opt}</span>
                    <ArrowRight size={18} color="#FF7A59" />
                  </button>
                ))}
              </div>
            ) : (
              <div style={{ padding: '16px 0', animation: 'fadeIn 0.25s ease-out' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>
                  {quizResult.is_correct ? '🎉 ⭐⭐⭐' : '🌟'}
                </div>
                <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: quizResult.is_correct ? '#0D9488' : '#FF7A59', marginBottom: '8px' }}>
                  {quizResult.is_correct ? "You Got It Right!" : "Almost! Let's Discover Why"}
                </h4>
                <p style={{ fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: '1.5', marginBottom: '16px' }}>
                  {quizResult.positive_feedback}
                </p>
                {quizResult.fun_fact && (
                  <div style={{ background: 'rgba(255, 209, 102, 0.2)', padding: '12px 16px', borderRadius: '16px', fontSize: '0.85rem', marginBottom: '20px' }}>
                    💡 <strong>Fun Fact:</strong> {quizResult.fun_fact}
                  </div>
                )}
                <button
                  onClick={() => setQuizModalOpen(false)}
                  className="kids-btn-fun"
                  style={{ width: '100%', justifyContent: 'center' }}
                >
                  Collect {quizResult.stars_awarded} Stars & Close ⭐
                </button>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
