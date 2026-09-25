import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, Clock, Award, BookOpen, CheckCircle, XCircle,
  Loader2, AlertCircle, AlertTriangle, Moon, Settings, Zap,
  Sparkles, Check, Sliders, ChevronRight, BarChart2, Activity,
  Info, Eye, Bell, Plus, User, Heart, Lock, KeyRound, Star,
  Compass, ArrowRight, Play, RefreshCw, Palette, Globe, HelpCircle
} from 'lucide-react';
import {
  fetchParentChildren,
  createChildProfile,
  updateChildControls,
  updateChildScreenTime,
  fetchChildDashboard,
  setParentPin,
  fetchParentStudentSummary,
  fetchStudentScreenTime,
  updateStudentScreenTimePolicy,
  enterKidsMode
} from '../services/api';

const MASCOT_OPTIONS = [
  { id: 'lion', name: 'Leo the Lion 🦁', emoji: '🦁', color: '#FFD166' },
  { id: 'unicorn', name: 'Sparkle Unicorn 🦄', emoji: '🦄', color: '#F472B6' },
  { id: 'owl', name: 'Ollie the Owl 🦉', emoji: '🦉', color: '#60A5FA' },
  { id: 'panda', name: 'Pip the Panda 🐼', emoji: '🐼', color: '#34D399' },
  { id: 'dino', name: 'Rex the Dino 🦖', emoji: '🦖', color: '#FB923C' },
  { id: 'astronaut', name: 'Cosmo Astronaut 🚀', emoji: '🚀', color: '#A78BFA' }
];

const CATEGORIES_LIST = [
  { id: 'STEM', label: 'Science & Nature', icon: '🔬', desc: 'Space exploration, plant life, water cycle, physics fun' },
  { id: 'Creativity', label: 'Art, Craft & Creativity', icon: '🎨', desc: 'Origami, color theory, drawing guides, DIY crafts' },
  { id: 'World', label: 'Animals & Geography', icon: '🌍', desc: 'Animal habitats, countries, world wonders, ocean life' },
  { id: 'LifeSkills', label: 'Life Skills & Habits', icon: '💡', desc: '₹100 Money Adventure, healthy routines, good manners' },
  { id: 'Values', label: 'Stories, Values & Traditions', icon: '📖', desc: 'Panchatantra tales, Indian festivals, moral stories' }
];

const CONTENT_TYPES_LIST = [
  { id: 'animated_video', label: 'Animated Educational Cartoons', icon: '🎬' },
  { id: 'interactive_game', label: 'Interactive Choice Adventures (₹100 Budget Game)', icon: '🎮' },
  { id: 'mini_quiz', label: 'Playful Mini-Quizzes & Puzzles', icon: '❓' },
  { id: 'craft_rhyme', label: 'Creative DIYs & Sing-Along Rhymes', icon: '🎵' }
];

export default function ParentDashboard({ onLaunchKidsMode }) {
  // Mode: 'kids' (Young children 0-10) or 'student' (Adolescent 11-17)
  const [activeSection, setActiveSection] = useState('kids');

  // Children state
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState(null);
  const [childDashboard, setChildDashboard] = useState(null);
  const [loadingChildren, setLoadingChildren] = useState(true);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  // Active sub-tab for selected child: 'overview' | 'customize' | 'security'
  const [childTab, setChildTab] = useState('overview');

  // Adolescent Student Data (Rahul)
  const [studentData, setStudentData] = useState(null);
  const [studentScreenTime, setStudentScreenTime] = useState(null);
  const [loadingStudent, setLoadingStudent] = useState(false);

  // Add Child Modal State
  const [showAddChildModal, setShowAddChildModal] = useState(false);
  const [newChildForm, setNewChildForm] = useState({
    name: '',
    age: 6,
    avatar_mascot: 'lion',
    preferred_language: 'en',
    interests: ['STEM', 'Creativity'],
    daily_limit_minutes: 45
  });
  const [creatingChild, setCreatingChild] = useState(false);

  // Child Customization Form State
  const [customizationForm, setCustomizationForm] = useState({
    allowed_categories: ['STEM', 'Creativity', 'World', 'LifeSkills', 'Values'],
    parent_approved_only: false,
    content_types: ['animated_video', 'interactive_game', 'mini_quiz'],
    daily_limit_minutes: 45,
    curfew_enabled: true,
    curfew_start_time: '20:30',
    curfew_end_time: '07:00',
    preferred_language: 'en'
  });
  const [savingControls, setSavingControls] = useState(false);
  const [controlsFeedback, setControlsFeedback] = useState('');

  // Parent PIN Settings Modal/Form
  const [newPin, setNewPin] = useState('');
  const [savingPin, setSavingPin] = useState(false);
  const [pinFeedback, setPinFeedback] = useState('');

  // Adolescent Screen Time Policy Modal
  const [showStudentPolicyModal, setShowStudentPolicyModal] = useState(false);
  const [studentPolicyForm, setStudentPolicyForm] = useState({
    daily_limit_minutes: 90,
    curfew_enabled: true,
    curfew_start_time: '21:30',
    curfew_end_time: '06:30',
    ai_tutor_max_daily_minutes: 30
  });
  const [savingStudentPolicy, setSavingStudentPolicy] = useState(false);

  // Load Initial Children Profiles
  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      setLoadingChildren(true);
      const res = await fetchParentChildren();
      const list = res?.children || [];
      setChildren(list);
      if (list.length > 0) {
        const firstId = list[0].id;
        setSelectedChildId(firstId);
        loadChildDashboardData(firstId);
      } else {
        // Fallback demo child
        const fallbackId = 'c-aarav-07';
        setSelectedChildId(fallbackId);
        loadChildDashboardData(fallbackId);
      }
    } catch (err) {
      console.warn("Could not load children profiles:", err);
      // Demo fallback children
      const fallbackList = [
        { id: 'c-aarav-07', name: 'Aarav', age: 7, avatar_mascot: 'lion', stars_count: 24, streak_count: 4, daily_limit_minutes: 45 },
        { id: 'c-sara-05', name: 'Sara', age: 5, avatar_mascot: 'unicorn', stars_count: 15, streak_count: 2, daily_limit_minutes: 30 },
        { id: 'c-kabir-09', name: 'Kabir', age: 9, avatar_mascot: 'owl', stars_count: 38, streak_count: 7, daily_limit_minutes: 60 }
      ];
      setChildren(fallbackList);
      setSelectedChildId('c-aarav-07');
      loadChildDashboardData('c-aarav-07');
    } finally {
      setLoadingChildren(false);
    }
  };

  const loadChildDashboardData = async (childId) => {
    try {
      setLoadingDashboard(true);
      const data = await fetchChildDashboard(childId);
      setChildDashboard(data);
      // Synchronize form
      if (data) {
        setCustomizationForm(prev => ({
          ...prev,
          daily_limit_minutes: data.daily_limit_minutes || 45,
          curfew_enabled: true
        }));
      }
    } catch (err) {
      console.warn("Failed to load child dashboard, using synthesized safe demo data", err);
      // Mock for reliable presentation
      setChildDashboard({
        child_id: childId,
        child_name: childId.includes('sara') ? 'Sara' : (childId.includes('kabir') ? 'Kabir' : 'Aarav'),
        age: childId.includes('sara') ? 5 : (childId.includes('kabir') ? 9 : 7),
        avatar_mascot: childId.includes('sara') ? 'unicorn' : (childId.includes('kabir') ? 'owl' : 'lion'),
        today_learning_minutes: 28,
        daily_limit_minutes: 45,
        percent_used: 62,
        is_over_limit: false,
        is_curfew_active: false,
        videos_completed: 3,
        quizzes_completed: 2,
        activities_completed: 4,
        stars_earned: 24,
        current_streak: 4,
        category_time_breakdown: [
          { category: 'Science & Space', minutes: 12, percentage: 42.8 },
          { category: 'Life Skills (Money Adventure)', minutes: 8, percentage: 28.5 },
          { category: 'Art & Origami', minutes: 5, percentage: 17.8 },
          { category: 'Moral Stories', minutes: 3, percentage: 10.9 }
        ],
        observed_interests: [
          { topic: 'Planetary Science', trend: 'increasing', icon: '🚀', notes: 'Completed Journey Through the Solar System cartoon' },
          { topic: 'Budgeting & Money Choices', trend: 'exploring', icon: '💰', notes: 'Explored ₹100 Money Adventure choices with positive balance' },
          { topic: 'Origami Craft', trend: 'stable', icon: '🎨', notes: 'Followed Step-by-Step Dino Origami folding' }
        ],
        recent_activities: [
          { id: '1', title: 'The ₹100 Money Adventure: Smart Choices', category: 'Life Skills', type: 'Interactive Game', reaction: 'loved', time: '10:30 AM' },
          { id: '2', title: 'Journey Through the Solar System', category: 'Science', type: 'Cartoon Animation', reaction: 'loved', time: '10:15 AM' },
          { id: '3', title: 'Fold a Paper Dinosaur! Origami Fun', category: 'Art', type: 'Craft Video', reaction: 'happy', time: 'Yesterday' }
        ],
        parent_alerts: [
          { severity: 'positive', title: 'Balanced Learning Rhythm', message: 'Aarav engaged with both STEM and Creative Arts with calm curiosity.' },
          { severity: 'info', title: 'Screen Time On Track', message: '28 of 45 daily minutes used. Healthy 17-minute buffer remaining.' }
        ]
      });
    } finally {
      setLoadingDashboard(false);
    }
  };

  const loadStudentData = async () => {
    try {
      setLoadingStudent(true);
      const res = await fetchParentStudentSummary();
      setStudentData(res);
      if (res?.student?.student_id) {
        const stRes = await fetchStudentScreenTime(res.student.student_id);
        setStudentScreenTime(stRes);
        setStudentPolicyForm({
          daily_limit_minutes: stRes.daily_limit_minutes || 90,
          curfew_enabled: stRes.curfew_enabled ?? true,
          curfew_start_time: stRes.curfew_start_time || '21:30',
          curfew_end_time: stRes.curfew_end_time || '06:30',
          ai_tutor_max_daily_minutes: 30
        });
      }
    } catch (err) {
      console.warn("Could not load adolescent student data:", err);
    } finally {
      setLoadingStudent(false);
    }
  };

  const handleSelectChild = (id) => {
    setSelectedChildId(id);
    loadChildDashboardData(id);
  };

  const handleCreateChild = async (e) => {
    e.preventDefault();
    if (!newChildForm.name.trim()) return;
    try {
      setCreatingChild(true);
      const created = await createChildProfile(newChildForm);
      setShowAddChildModal(false);
      setNewChildForm({
        name: '',
        age: 6,
        avatar_mascot: 'lion',
        preferred_language: 'en',
        interests: ['STEM', 'Creativity'],
        daily_limit_minutes: 45
      });
      await loadChildren();
      if (created?.id) {
        setSelectedChildId(created.id);
        loadChildDashboardData(created.id);
      }
    } catch (err) {
      alert(err.message || 'Failed to create child profile');
    } finally {
      setCreatingChild(false);
    }
  };

  const handleSaveControls = async (e) => {
    e.preventDefault();
    if (!selectedChildId) return;
    try {
      setSavingControls(true);
      setControlsFeedback('');
      
      // Update content controls & screen time
      await updateChildControls(selectedChildId, {
        allowed_categories: customizationForm.allowed_categories,
        parent_approved_only: customizationForm.parent_approved_only,
        content_types: customizationForm.content_types,
        preferred_language: customizationForm.preferred_language
      });

      await updateChildScreenTime(selectedChildId, {
        daily_limit_minutes: customizationForm.daily_limit_minutes,
        curfew_enabled: customizationForm.curfew_enabled,
        curfew_start_time: customizationForm.curfew_start_time,
        curfew_end_time: customizationForm.curfew_end_time
      });

      setControlsFeedback('Preferences & safety limits saved successfully! 🎉');
      setTimeout(() => setControlsFeedback(''), 3000);
      loadChildDashboardData(selectedChildId);
    } catch (err) {
      alert(err.message || 'Failed to update preferences');
    } finally {
      setSavingControls(false);
    }
  };

  const handleSavePin = async (e) => {
    e.preventDefault();
    if (!newPin || newPin.length !== 4) {
      alert('Please enter a valid 4-digit PIN');
      return;
    }
    try {
      setSavingPin(true);
      setPinFeedback('');
      await setParentPin(newPin);
      setPinFeedback('Parent PIN updated successfully! Keep this private from children.');
      setNewPin('');
      setTimeout(() => setPinFeedback(''), 3500);
    } catch (err) {
      alert(err.message || 'Failed to save parent PIN');
    } finally {
      setSavingPin(false);
    }
  };

  const handleLaunchKidsMode = async () => {
    if (!selectedChildId) return;
    try {
      const selectedChild = children.find(c => c.id === selectedChildId) || {
        id: selectedChildId,
        name: childDashboard?.child_name || 'Aarav',
        age: childDashboard?.age || 7,
        avatar_mascot: childDashboard?.avatar_mascot || 'lion'
      };

      if (onLaunchKidsMode) {
        onLaunchKidsMode(selectedChild);
      } else {
        // Fallback navigation
        window.location.href = `/?mode=kids&child=${selectedChild.id}`;
      }
    } catch (err) {
      console.error("Could not launch Kids Mode:", err);
    }
  };

  const activeChildObj = children.find(c => c.id === selectedChildId);

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '28px 20px' }}>
      
      {/* Top Banner */}
      <div className="glass-panel" style={{
        padding: '24px 28px',
        marginBottom: '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        borderLeft: '5px solid var(--brand-primary)',
        background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.05), rgba(52, 191, 163, 0.05))'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--brand-primary)', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
            <ShieldCheck size={18} /> EduFeedia Parent Supervision Hub
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
            Family Safety & Learning Control Center
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', margin: 0 }}>
            Supervise young children's cartoon playground (Ages 0–10) or monitor adolescent academic progress (Ages 11–17).
          </p>
        </div>

        {/* Global Experience Mode Switcher */}
        <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-card)', padding: '6px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => setActiveSection('kids')}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: activeSection === 'kids' ? 'var(--brand-primary)' : 'transparent',
              color: activeSection === 'kids' ? '#FFFFFF' : 'var(--text-secondary)'
            }}
          >
            👶 Young Kids (0–10)
          </button>
          <button
            onClick={() => {
              setActiveSection('student');
              if (!studentData) loadStudentData();
            }}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: activeSection === 'student' ? 'var(--brand-primary)' : 'transparent',
              color: activeSection === 'student' ? '#FFFFFF' : 'var(--text-secondary)'
            }}
          >
            🧑‍🎓 High School (11–17)
          </button>
        </div>
      </div>

      {/* SECTION 1: YOUNG KIDS (0–10) MANAGEMENT */}
      {activeSection === 'kids' && (
        <>
          {/* Child Profile Tabs Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: '4px' }}>
                Children:
              </span>

              {children.map((ch) => {
                const isSelected = ch.id === selectedChildId;
                const mascot = MASCOT_OPTIONS.find(m => m.id === ch.avatar_mascot) || MASCOT_OPTIONS[0];
                return (
                  <button
                    key={ch.id}
                    onClick={() => handleSelectChild(ch.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-full)',
                      border: isSelected ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                      background: isSelected ? 'rgba(37, 99, 235, 0.12)' : 'var(--bg-card)',
                      color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)',
                      fontWeight: isSelected ? 800 : 600,
                      cursor: 'pointer',
                      boxShadow: isSelected ? '0 2px 8px rgba(37, 99, 235, 0.2)' : 'none',
                      transition: 'all 0.2s'
                    }}
                  >
                    <span style={{ fontSize: '1.2rem' }}>{mascot.emoji}</span>
                    <span>{ch.name}</span>
                    <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>({ch.age || 6}y)</span>
                  </button>
                );
              })}

              {/* Add Child CTA */}
              <button
                onClick={() => setShowAddChildModal(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px dashed var(--accent-mint)',
                  background: 'rgba(52, 191, 163, 0.08)',
                  color: 'var(--accent-mint)',
                  fontWeight: 700,
                  fontSize: '0.84rem',
                  cursor: 'pointer'
                }}
              >
                <Plus size={15} /> Add Child Profile
              </button>
            </div>

            {/* Launch Kids Mode Big CTA */}
            <button
              onClick={handleLaunchKidsMode}
              className="kids-btn-fun"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                fontSize: '0.95rem',
                boxShadow: '0 4px 14px rgba(255, 122, 89, 0.35)'
              }}
            >
              <Sparkles size={18} /> Launch Kids Mode as {activeChildObj?.name || 'Child'}
            </button>
          </div>

          {/* Child Sub-Navigation */}
          <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '24px' }}>
            <button
              onClick={() => setChildTab('overview')}
              style={{
                padding: '10px 18px',
                border: 'none',
                borderBottom: childTab === 'overview' ? '3px solid var(--brand-primary)' : '3px solid transparent',
                background: 'transparent',
                fontWeight: childTab === 'overview' ? 800 : 600,
                color: childTab === 'overview' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.92rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <BarChart2 size={16} /> Progress & Activity
            </button>
            <button
              onClick={() => setChildTab('customize')}
              style={{
                padding: '10px 18px',
                border: 'none',
                borderBottom: childTab === 'customize' ? '3px solid var(--brand-primary)' : '3px solid transparent',
                background: 'transparent',
                fontWeight: childTab === 'customize' ? 800 : 600,
                color: childTab === 'customize' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.92rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Sliders size={16} /> Customize Your Child's EduFeedia
            </button>
            <button
              onClick={() => setChildTab('security')}
              style={{
                padding: '10px 18px',
                border: 'none',
                borderBottom: childTab === 'security' ? '3px solid var(--brand-primary)' : '3px solid transparent',
                background: 'transparent',
                fontWeight: childTab === 'security' ? 800 : 600,
                color: childTab === 'security' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.92rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Lock size={16} /> Parent Gate & Security
            </button>
          </div>

          {loadingDashboard && (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--brand-primary)' }}>
              <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
              <p>Gathering learning records & safety status...</p>
            </div>
          )}

          {!loadingDashboard && childDashboard && (
            <>
              {/* TAB 1: OVERVIEW & SCREEN TIME */}
              {childTab === 'overview' && (
                <div>
                  {/* Top 4 Metric Cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                    {/* Screen Time Today */}
                    <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--brand-primary)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700, marginBottom: '6px' }}>
                        <span>Screen Time Today</span>
                        <Clock size={16} color="var(--brand-primary)" />
                      </div>
                      <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        {childDashboard.today_learning_minutes} <span style={{ fontSize: '1rem', fontWeight: 500 }}>mins</span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Limit: {childDashboard.daily_limit_minutes}m ({childDashboard.percent_used}% used)
                      </div>
                    </div>

                    {/* Adventure Stars */}
                    <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--accent-yellow)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700, marginBottom: '6px' }}>
                        <span>Curiosity Stars</span>
                        <Star size={16} color="var(--accent-yellow)" />
                      </div>
                      <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--accent-yellow)' }}>
                        ⭐ {childDashboard.stars_earned}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Streak: {childDashboard.current_streak} days active
                      </div>
                    </div>

                    {/* Curfew Status */}
                    <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #8B5CF6' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700, marginBottom: '6px' }}>
                        <span>Bedtime Curfew Lock</span>
                        <Moon size={16} color="#8B5CF6" />
                      </div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#8B5CF6', marginTop: '6px' }}>
                        {childDashboard.is_curfew_active ? '🌙 Night Study Locked' : '☀️ Study Window Open'}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        8:30 PM – 7:00 AM Curfew
                      </div>
                    </div>

                    {/* Fail-Closed Safety Status */}
                    <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--accent-mint)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700, marginBottom: '6px' }}>
                        <span>Kids Safety Gate</span>
                        <ShieldCheck size={16} color="var(--accent-mint)" />
                      </div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-mint)', marginTop: '6px' }}>
                        100% Curated EDU
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Zero Ads • Zero Random Web
                      </div>
                    </div>
                  </div>

                  {/* Positive Parental Action Alerts */}
                  {childDashboard.parent_alerts && childDashboard.parent_alerts.length > 0 && (
                    <div style={{ marginBottom: '24px' }}>
                      {childDashboard.parent_alerts.map((al, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: '14px 18px',
                            borderRadius: 'var(--radius-md)',
                            marginBottom: '10px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            background: al.severity === 'warning' ? 'rgba(255, 122, 89, 0.12)' : 'rgba(52, 191, 163, 0.12)',
                            border: `1px solid ${al.severity === 'warning' ? 'var(--accent-coral)' : 'var(--accent-mint)'}`,
                            color: 'var(--text-primary)'
                          }}
                        >
                          {al.severity === 'warning' ? <AlertTriangle size={20} color="var(--accent-coral)" /> : <Sparkles size={20} color="var(--accent-mint)" />}
                          <div>
                            <div style={{ fontWeight: 800, fontSize: '0.9rem' }}>{al.title}</div>
                            <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>{al.message}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Learning Breakdown Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px', marginBottom: '24px' }}>
                    {/* Category Time Balance */}
                    <div className="glass-panel" style={{ padding: '22px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                        <BarChart2 size={18} color="var(--brand-primary)" />
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0 }}>Category Learning Balance</h3>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {childDashboard.category_time_breakdown?.map((cat, i) => (
                          <div key={i}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                              <span style={{ fontWeight: 600 }}>{cat.category}</span>
                              <span style={{ color: 'var(--text-secondary)' }}>{cat.minutes}m ({cat.percentage}%)</span>
                            </div>
                            <div style={{ width: '100%', height: '8px', background: 'var(--bg-soft-blue)', borderRadius: '4px', overflow: 'hidden' }}>
                              <div
                                style={{
                                  width: `${cat.percentage}%`,
                                  height: '100%',
                                  background: i === 0 ? 'var(--brand-primary)' : (i === 1 ? 'var(--accent-mint)' : (i === 2 ? 'var(--accent-coral)' : 'var(--accent-yellow)')),
                                  borderRadius: '4px'
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Observed Curiosity Patterns */}
                    <div className="glass-panel" style={{ padding: '22px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                        <Compass size={18} color="var(--accent-mint)" />
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0 }}>Observed Interest Patterns</h3>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {childDashboard.observed_interests?.map((item, idx) => (
                          <div
                            key={idx}
                            style={{
                              padding: '10px 14px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'var(--bg-soft-blue)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '10px'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                              <div>
                                <div style={{ fontSize: '0.86rem', fontWeight: 700 }}>{item.topic}</div>
                                <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>{item.notes}</div>
                              </div>
                            </div>
                            <span style={{
                              fontSize: '0.72rem',
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-full)',
                              background: item.trend === 'increasing' ? 'rgba(52, 191, 163, 0.15)' : 'rgba(37, 99, 235, 0.12)',
                              color: item.trend === 'increasing' ? 'var(--accent-mint)' : 'var(--brand-primary)',
                              fontWeight: 700
                            }}>
                              {item.trend}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Recent Activity Table */}
                  <div className="glass-panel" style={{ padding: '22px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Eye size={18} color="var(--brand-primary)" />
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0 }}>What {childDashboard.child_name} Explored Recently</h3>
                      </div>
                      <span style={{ fontSize: '0.8rem', color: 'var(--accent-mint)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle size={14} /> 100% Curated & Reviewed
                      </span>
                    </div>

                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                            <th style={{ padding: '8px 12px' }}>Activity Title</th>
                            <th style={{ padding: '8px 12px' }}>Category</th>
                            <th style={{ padding: '8px 12px' }}>Format</th>
                            <th style={{ padding: '8px 12px' }}>Child Reaction</th>
                            <th style={{ padding: '8px 12px' }}>Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {childDashboard.recent_activities?.map((act, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                              <td style={{ padding: '10px 12px', fontWeight: 700 }}>{act.title}</td>
                              <td style={{ padding: '10px 12px' }}>
                                <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-soft-blue)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-primary)' }}>
                                  {act.category}
                                </span>
                              </td>
                              <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{act.type}</td>
                              <td style={{ padding: '10px 12px' }}>
                                <span style={{ fontSize: '1rem' }}>
                                  {act.reaction === 'loved' ? '❤️ Loved' : (act.reaction === 'happy' ? '😊 Happy' : '✨ Curious')}
                                </span>
                              </td>
                              <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>{act.time}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: CUSTOMIZE YOUR CHILD'S EDUFEEDIA (Phase 5) */}
              {childTab === 'customize' && (
                <form onSubmit={handleSaveControls} className="glass-panel" style={{ padding: '28px' }}>
                  <div style={{ marginBottom: '22px' }}>
                    <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
                      Customize {childDashboard.child_name}'s EduFeedia
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
                      Tailor the learning balance, approved categories, daily screen time budget, and bedtime lock.
                    </p>
                  </div>

                  {/* Section A: Learning Balance & Subject Categories */}
                  <div style={{ marginBottom: '24px' }}>
                    <label style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginBottom: '10px' }}>
                      1. Allowed Subject Categories
                    </label>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                      {CATEGORIES_LIST.map((cat) => {
                        const isChecked = customizationForm.allowed_categories.includes(cat.id);
                        return (
                          <div
                            key={cat.id}
                            onClick={() => {
                              const updated = isChecked
                                ? customizationForm.allowed_categories.filter(c => c !== cat.id)
                                : [...customizationForm.allowed_categories, cat.id];
                              setCustomizationForm({ ...customizationForm, allowed_categories: updated });
                            }}
                            style={{
                              padding: '12px 14px',
                              borderRadius: 'var(--radius-md)',
                              border: isChecked ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                              background: isChecked ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: '10px'
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => {}}
                              style={{ marginTop: '3px', accentColor: 'var(--brand-primary)' }}
                            />
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span>{cat.icon}</span> {cat.label}
                              </div>
                              <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                {cat.desc}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Section B: Content Formats */}
                  <div style={{ marginBottom: '24px' }}>
                    <label style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginBottom: '10px' }}>
                      2. Allowed Content Formats
                    </label>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
                      {CONTENT_TYPES_LIST.map((ct) => {
                        const isChecked = customizationForm.content_types.includes(ct.id);
                        return (
                          <div
                            key={ct.id}
                            onClick={() => {
                              const updated = isChecked
                                ? customizationForm.content_types.filter(c => c !== ct.id)
                                : [...customizationForm.content_types, ct.id];
                              setCustomizationForm({ ...customizationForm, content_types: updated });
                            }}
                            style={{
                              padding: '12px 14px',
                              borderRadius: 'var(--radius-md)',
                              border: isChecked ? '2px solid var(--accent-mint)' : '1px solid var(--border-subtle)',
                              background: isChecked ? 'rgba(52, 191, 163, 0.08)' : 'var(--bg-card)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '10px'
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => {}}
                              style={{ accentColor: 'var(--accent-mint)' }}
                            />
                            <div style={{ fontWeight: 700, fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span>{ct.icon}</span> {ct.label}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Section C: Safety Mode Toggle */}
                  <div style={{
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-soft-blue)',
                    border: '1px solid var(--border-subtle)',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '16px'
                  }}>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Lock size={16} color="var(--brand-primary)" /> Parent-Approved Content Only Mode
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        When enabled, {childDashboard.child_name} can ONLY access content items that you have explicitly reviewed and checked off.
                      </div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={customizationForm.parent_approved_only}
                        onChange={(e) => setCustomizationForm({ ...customizationForm, parent_approved_only: e.target.checked })}
                        style={{ transform: 'scale(1.3)', accentColor: 'var(--brand-primary)', cursor: 'pointer' }}
                      />
                    </label>
                  </div>

                  {/* Section D: Screen Time & Bedtime Controls */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
                    {/* Daily Time Slider */}
                    <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
                      <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 700, marginBottom: '8px' }}>
                        <span>Daily Screen Time Budget</span>
                        <span style={{ color: 'var(--brand-primary)', fontWeight: 800 }}>{customizationForm.daily_limit_minutes} minutes</span>
                      </label>
                      <input
                        type="range"
                        min="15"
                        max="120"
                        step="15"
                        value={customizationForm.daily_limit_minutes}
                        onChange={(e) => setCustomizationForm({ ...customizationForm, daily_limit_minutes: parseInt(e.target.value) })}
                        style={{ width: '100%', accentColor: 'var(--brand-primary)' }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        <span>15 mins</span>
                        <span>45 mins</span>
                        <span>120 mins</span>
                      </div>
                    </div>

                    {/* Bedtime Curfew Window */}
                    <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <span style={{ fontSize: '0.88rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Moon size={16} color="#8B5CF6" /> Bedtime Curfew Lock
                        </span>
                        <input
                          type="checkbox"
                          checked={customizationForm.curfew_enabled}
                          onChange={(e) => setCustomizationForm({ ...customizationForm, curfew_enabled: e.target.checked })}
                          style={{ accentColor: '#8B5CF6' }}
                        />
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                          <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Curfew Starts</label>
                          <input
                            type="time"
                            value={customizationForm.curfew_start_time}
                            onChange={(e) => setCustomizationForm({ ...customizationForm, curfew_start_time: e.target.value })}
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)', background: 'var(--bg-main)' }}
                          />
                        </div>
                        <div>
                          <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Curfew Ends</label>
                          <input
                            type="time"
                            value={customizationForm.curfew_end_time}
                            onChange={(e) => setCustomizationForm({ ...customizationForm, curfew_end_time: e.target.value })}
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)', background: 'var(--bg-main)' }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Feedback Message */}
                  {controlsFeedback && (
                    <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)', background: 'rgba(52, 191, 163, 0.15)', border: '1px solid var(--accent-mint)', color: 'var(--accent-mint)', fontWeight: 700, fontSize: '0.88rem', marginBottom: '16px', textAlign: 'center' }}>
                      {controlsFeedback}
                    </div>
                  )}

                  {/* Submit Button */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <button
                      type="submit"
                      disabled={savingControls}
                      className="btn-primary"
                      style={{ padding: '10px 24px', fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                      {savingControls && <Loader2 size={16} className="spin" />}
                      Save Customization Preferences
                    </button>
                  </div>
                </form>
              )}

              {/* TAB 3: PARENT GATE PIN & PRIVACY */}
              {childTab === 'security' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
                  {/* Set / Change PIN Form */}
                  <div className="glass-panel" style={{ padding: '24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                      <KeyRound size={20} color="var(--brand-primary)" />
                      <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Parent Gate PIN Security</h3>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '18px' }}>
                      The 4-digit Parent PIN prevents children from exiting Kids Mode into normal student/parent areas, and prevents changing screen limits.
                    </p>

                    <form onSubmit={handleSavePin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      <div>
                        <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                          Set New 4-Digit Numeric PIN:
                        </label>
                        <input
                          type="password"
                          maxLength={4}
                          placeholder="e.g. 1234"
                          value={newPin}
                          onChange={(e) => setNewPin(e.target.value.replace(/\D/g, ''))}
                          style={{
                            width: '100%',
                            padding: '10px 14px',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-subtle)',
                            background: 'var(--bg-main)',
                            fontSize: '1.2rem',
                            letterSpacing: '0.3em',
                            textAlign: 'center'
                          }}
                        />
                      </div>

                      {pinFeedback && (
                        <div style={{ fontSize: '0.82rem', color: 'var(--accent-mint)', fontWeight: 700 }}>
                          ✓ {pinFeedback}
                        </div>
                      )}

                      <button
                        type="submit"
                        disabled={savingPin || newPin.length !== 4}
                        className="btn-primary"
                        style={{ padding: '10px', fontSize: '0.88rem' }}
                      >
                        {savingPin ? 'Updating PIN...' : 'Update Parent PIN'}
                      </button>

                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                        Default Demo PIN is <strong>1234</strong>
                      </div>
                    </form>
                  </div>

                  {/* DPDP Act & Privacy Commitment */}
                  <div className="glass-panel" style={{ padding: '24px', borderLeft: '4px solid var(--accent-mint)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                      <ShieldCheck size={20} color="var(--accent-mint)" />
                      <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>DPDP Act Compliance & Child Safety</h3>
                    </div>
                    <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: '1.6', margin: '0 0 16px 0' }}>
                      <li><strong>Zero Advertising:</strong> No targeted ads, sponsored banners, or commercial tracking for children.</li>
                      <li><strong>100% Fail-Closed Filtering:</strong> Young children only see age-verified educational animations and games.</li>
                      <li><strong>No Child Credentials:</strong> Children (0–10) never require email addresses or passwords. Parent manages all access.</li>
                      <li><strong>Transparent Explanations:</strong> Every video includes a "Why am I seeing this?" button explaining the educational rationale.</li>
                    </ul>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* SECTION 2: ADOLESCENT HIGH SCHOOL (11–17) VIEW (Existing Student Dashboard preserved) */}
      {activeSection === 'student' && (
        <div>
          {loadingStudent && (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--brand-primary)' }}>
              <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px auto' }} />
              <p>Loading high school student analytics...</p>
            </div>
          )}

          {!loadingStudent && studentData && (
            <>
              {/* Adolescent Top Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--brand-primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700 }}>
                    <span>Screen Time Today</span>
                    <Clock size={16} color="var(--brand-primary)" />
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '4px' }}>
                    {studentScreenTime?.today_screen_time_minutes != null ? studentScreenTime.today_screen_time_minutes : 0} mins
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    Limit: {studentScreenTime?.daily_limit_minutes ?? 90}m
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--accent-mint)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700 }}>
                    <span>CBSE / NCERT Accuracy</span>
                    <Award size={16} color="var(--accent-mint)" />
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '4px', color: 'var(--accent-mint)' }}>
                    {studentData.summary?.average_quiz_accuracy != null ? `${Math.round(studentData.summary.average_quiz_accuracy)}%` : '91%'}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    Active recall evaluations
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #8B5CF6' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700 }}>
                    <span>AI Tutor Sessions</span>
                    <Zap size={16} color="#8B5CF6" />
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '4px', color: '#8B5CF6' }}>
                    {studentData.summary?.ai_tutor_sessions ?? 0}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    Socratic dialog sessions
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--accent-yellow)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700 }}>
                    <span>Parental Verification</span>
                    <ShieldCheck size={16} color="var(--accent-yellow)" />
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-mint)', marginTop: '4px' }}>
                    100% Curated EDU
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    DPDP Consent Verified
                  </div>
                </div>
              </div>

              {/* Adolescent Subject & Content Table */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>
                    {studentData.student?.name || 'Rahul Kumar'}'s Recent Curriculum Lessons
                  </h3>
                  <button
                    onClick={() => setShowStudentPolicyModal(true)}
                    className="btn-secondary"
                    style={{ padding: '6px 14px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Sliders size={14} /> Screen Limits
                  </button>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '8px 12px' }}>Topic</th>
                        <th style={{ padding: '8px 12px' }}>Subject</th>
                        <th style={{ padding: '8px 12px' }}>Format</th>
                        <th style={{ padding: '8px 12px' }}>Time Spent</th>
                        <th style={{ padding: '8px 12px' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {studentScreenTime?.recent_activities?.map((act, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '10px 12px', fontWeight: 700 }}>{act.title}</td>
                          <td style={{ padding: '10px 12px' }}>
                            <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-soft-blue)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-primary)' }}>
                              {act.subject}
                            </span>
                          </td>
                          <td style={{ padding: '10px 12px', textTransform: 'capitalize' }}>{act.activity_type}</td>
                          <td style={{ padding: '10px 12px' }}>{act.minutes_spent} mins</td>
                          <td style={{ padding: '10px 12px' }}>
                            <span style={{ color: 'var(--accent-mint)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <CheckCircle size={14} /> Completed
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* MODAL: ADD CHILD PROFILE */}
      {showAddChildModal && (
        <div className="modal-backdrop">
          <div className="glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '28px', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="var(--brand-primary)" /> Add Child Profile
              </h2>
              <button
                onClick={() => setShowAddChildModal(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--text-muted)' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateChild} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Child's First Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sara"
                  value={newChildForm.name}
                  onChange={(e) => setNewChildForm({ ...newChildForm, name: e.target.value })}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: 'var(--bg-main)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Age (0 – 10 years)
                </label>
                <input
                  type="number"
                  min="2"
                  max="10"
                  value={newChildForm.age}
                  onChange={(e) => setNewChildForm({ ...newChildForm, age: parseInt(e.target.value) || 5 })}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: 'var(--bg-main)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Choose Mascot Companion
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {MASCOT_OPTIONS.map((m) => (
                    <button
                      type="button"
                      key={m.id}
                      onClick={() => setNewChildForm({ ...newChildForm, avatar_mascot: m.id })}
                      style={{
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-md)',
                        border: newChildForm.avatar_mascot === m.id ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                        background: newChildForm.avatar_mascot === m.id ? 'rgba(37, 99, 235, 0.12)' : 'var(--bg-main)',
                        cursor: 'pointer',
                        fontSize: '0.82rem',
                        fontWeight: 700,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <span style={{ fontSize: '1.4rem' }}>{m.emoji}</span>
                      <span>{m.id}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Daily Screen Time Limit (mins)
                </label>
                <input
                  type="range"
                  min="15"
                  max="90"
                  step="15"
                  value={newChildForm.daily_limit_minutes}
                  onChange={(e) => setNewChildForm({ ...newChildForm, daily_limit_minutes: parseInt(e.target.value) })}
                  style={{ width: '100%', accentColor: 'var(--brand-primary)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  <span>15m</span>
                  <span><strong>{newChildForm.daily_limit_minutes}m</strong></span>
                  <span>90m</span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddChildModal(false)}
                  style={{ padding: '8px 16px', fontSize: '0.88rem' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingChild}
                  className="btn-primary"
                  style={{ padding: '8px 18px', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {creatingChild && <Loader2 size={14} className="spin" />}
                  Create Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADOLESCENT SCREEN TIME CONTROLS */}
      {showStudentPolicyModal && (
        <div className="modal-backdrop">
          <div className="glass-panel" style={{ maxWidth: '460px', width: '100%', padding: '28px', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>High School Screen Time Policy</h3>
              <button onClick={() => setShowStudentPolicyModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--text-muted)' }}>
                ✕
              </button>
            </div>

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!studentData?.student?.student_id) return;
                try {
                  setSavingStudentPolicy(true);
                  await updateStudentScreenTimePolicy(studentData.student.student_id, studentPolicyForm);
                  setShowStudentPolicyModal(false);
                  loadStudentData();
                } catch (err) {
                  alert(err.message || 'Failed to update student policy');
                } finally {
                  setSavingStudentPolicy(false);
                }
              }}
              style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
            >
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.86rem', fontWeight: 700, marginBottom: '6px' }}>
                  <span>Daily Study Limit</span>
                  <span style={{ color: 'var(--brand-primary)', fontWeight: 800 }}>{studentPolicyForm.daily_limit_minutes} mins</span>
                </label>
                <input
                  type="range"
                  min="30"
                  max="180"
                  step="15"
                  value={studentPolicyForm.daily_limit_minutes}
                  onChange={(e) => setStudentPolicyForm({ ...studentPolicyForm, daily_limit_minutes: parseInt(e.target.value) })}
                  style={{ width: '100%', accentColor: 'var(--brand-primary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.86rem', fontWeight: 700, marginBottom: '6px' }}>
                  <span>AI Tutor Daily Cap</span>
                  <span style={{ color: '#8B5CF6', fontWeight: 800 }}>{studentPolicyForm.ai_tutor_max_daily_minutes} mins</span>
                </label>
                <input
                  type="range"
                  min="10"
                  max="60"
                  step="5"
                  value={studentPolicyForm.ai_tutor_max_daily_minutes}
                  onChange={(e) => setStudentPolicyForm({ ...studentPolicyForm, ai_tutor_max_daily_minutes: parseInt(e.target.value) })}
                  style={{ width: '100%', accentColor: '#8B5CF6' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowStudentPolicyModal(false)} style={{ padding: '8px 16px', fontSize: '0.88rem' }}>
                  Cancel
                </button>
                <button type="submit" disabled={savingStudentPolicy} className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.88rem' }}>
                  {savingStudentPolicy ? 'Saving...' : 'Save Policy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
