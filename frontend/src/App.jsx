import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DailyPlanFeed from './components/DailyPlanFeed';
import ContentPlayerModal from './components/ContentPlayerModal';
import QuizModal from './components/QuizModal';
import SocraticTutorChat from './components/SocraticTutorChat';
import MasteryDashboard from './components/MasteryDashboard';
import TeacherDashboard from './components/TeacherDashboard';
import ParentDashboard from './components/ParentDashboard';
import ExploreCatalog from './components/ExploreCatalog';
import ClassChallenges from './components/ClassChallenges';
import AuthScreen from './components/AuthScreen';
import KidsDashboard from './components/KidsDashboard';
import ParentGateModal from './components/ParentGateModal';
import { getSession, clearAuthSession, fetchDailyPlanFeed } from './services/api';

export default function App() {
  const [session, setSession] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const demo = params.get('demo');
      const mode = params.get('mode');
      if (demo === 'student' || mode === 'student') {
        return {
          user: { id: '2e67c476-5944-4d0a-9807-ffe7f5a115c8', email: 'rahul@apexschool.edu', role: 'student', first_name: 'Rahul', last_name: 'Kumar', xp_score: 420 },
          role: 'student',
          token: localStorage.getItem('edufeedia_token') || 'demo-token'
        };
      } else if (demo === 'teacher' || mode === 'teacher') {
        return {
          user: { id: '051ce768-1802-4ebd-8118-75d054675f75', email: 'sharma@apexschool.edu', role: 'teacher', first_name: 'Sunita', last_name: 'Sharma' },
          role: 'teacher',
          token: localStorage.getItem('edufeedia_token') || 'demo-token'
        };
      } else if (demo === 'parent' || demo === 'kids' || mode === 'parent' || mode === 'kids') {
        return {
          user: { id: '1c65a6a1-ee60-4fc6-907c-8f968b8fb4e0', email: 'parent@gmail.com', role: 'parent', first_name: 'Rajesh', last_name: 'Kumar' },
          role: 'parent',
          token: localStorage.getItem('edufeedia_token') || 'demo-token'
        };
      }
    }
    return getSession();
  });

  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('theme')) return params.get('theme');
    }
    return localStorage.getItem('edufeedia_theme') || 'light';
  });

  // Experience Mode: 'kids' (0–10) | 'student' (11–17) | 'parent' | 'teacher'
  const [experienceMode, setExperienceMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const mode = params.get('mode') || params.get('demo');
      if (mode === 'kids') return 'kids';
      if (mode === 'parent') return 'parent';
      if (mode === 'teacher') return 'teacher';
      if (mode === 'student') return 'student';
    }
    return 'student';
  });

  // Active Child Profile for Kids Mode
  const [activeChild, setActiveChild] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const childId = params.get('child');
      if (childId === 'c-sara-05') {
        return { id: 'c-sara-05', name: 'Sara', age: 5, avatar_mascot: 'unicorn', stars_count: 15, streak_count: 2 };
      } else if (childId === 'c-kabir-09') {
        return { id: 'c-kabir-09', name: 'Kabir', age: 9, avatar_mascot: 'owl', stars_count: 38, streak_count: 7 };
      }
    }
    return { id: 'c-aarav-07', name: 'Aarav', age: 7, avatar_mascot: 'lion', stars_count: 24, streak_count: 4 };
  });

  // Parent Gate Modal state (for leaving Kids Mode or modifying critical controls)
  const [parentGateOpen, setParentGateOpen] = useState(false);
  const [pendingTargetMode, setPendingTargetMode] = useState('parent');

  const [currentTab, setCurrentTab] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('tab')) return params.get('tab');
      if (params.get('demo') === 'teacher') return 'teacher';
      if (params.get('demo') === 'parent') return 'parent';
    }
    return 'feed';
  });

  const [dailyPlan, setDailyPlan] = useState(null);
  const [loadingFeed, setLoadingFeed] = useState(false);
  const [feedError, setFeedError] = useState('');
  
  const [activeLesson, setActiveLesson] = useState(null);
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [quizLessonTarget, setQuizLessonTarget] = useState(null);
  const [tutorFocusTopic, setTutorFocusTopic] = useState("Newton's Laws");

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('edufeedia_theme', theme);
  }, [theme]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const demo = params.get('demo') || params.get('mode');
      if (demo) {
        const creds = (demo === 'student') ? { email: 'rahul@apexschool.edu', password: 'Student123!' }
                    : (demo === 'teacher') ? { email: 'sharma@apexschool.edu', password: 'Teacher123!' }
                    : { email: 'parent@gmail.com', password: 'Parent123!' };
        fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(creds)
        }).then(r => r.json()).then(data => {
          if (data.access_token) {
            localStorage.setItem('edufeedia_token', data.access_token);
            localStorage.setItem('edufeedia_user', JSON.stringify(data.user));
            localStorage.setItem('edufeedia_role', data.role);
            setSession({ user: data.user, role: data.role, token: data.access_token });
            if (demo === 'student') {
              fetchDailyPlanFeed().then(plan => setDailyPlan(plan)).catch(() => {});
            }
          }
        }).catch(() => {});

        if (params.get('quiz')) {
          setQuizLessonTarget({
            id: '494947b7-ff7e-4411-9acc-23e8e8e1ef17',
            title: "Quadratic Equations Mastery Check",
            subject: 'Mathematics',
            grade_level: 10
          });
          setQuizModalOpen(true);
        }
      }
    }
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  useEffect(() => {
    if (session.user && session.user.role === 'student' && experienceMode === 'student') {
      loadFeed();
    }
  }, [session.user, experienceMode]);

  const loadFeed = async () => {
    setLoadingFeed(true);
    setFeedError('');
    try {
      const data = await fetchDailyPlanFeed();
      setDailyPlan(data);
    } catch (err) {
      setFeedError(err.message || 'Could not fetch daily recommendations');
    } finally {
      setLoadingFeed(false);
    }
  };

  const handleLoginSuccess = (user) => {
    setSession({ user, role: user.role, token: localStorage.getItem('edufeedia_token') });
    if (user.role === 'teacher' || user.role === 'school_admin') {
      setExperienceMode('teacher');
      setCurrentTab('teacher');
    } else if (user.role === 'parent') {
      setExperienceMode('parent');
      setCurrentTab('parent');
    } else {
      setExperienceMode('student');
      setCurrentTab('feed');
    }
  };

  const handleLogout = () => {
    clearAuthSession();
    setSession({ user: null, role: 'student', token: '' });
  };

  const handleSwitchExperience = (targetMode) => {
    if (experienceMode === 'kids' && targetMode !== 'kids') {
      // Must pass parent gate to leave kids mode
      setPendingTargetMode(targetMode);
      setParentGateOpen(true);
    } else {
      setExperienceMode(targetMode);
      if (targetMode === 'parent') setCurrentTab('parent');
      else if (targetMode === 'teacher') setCurrentTab('teacher');
      else if (targetMode === 'student') setCurrentTab('feed');
    }
  };

  const handleParentGateSuccess = () => {
    setExperienceMode(pendingTargetMode);
    if (pendingTargetMode === 'parent') setCurrentTab('parent');
    else if (pendingTargetMode === 'teacher') setCurrentTab('teacher');
    else if (pendingTargetMode === 'student') setCurrentTab('feed');
  };

  const handleSelectLesson = (lesson) => {
    setActiveLesson(lesson);
  };

  const handleCompleteAndQuiz = (lesson) => {
    setActiveLesson(null);
    setQuizLessonTarget(lesson);
    setQuizModalOpen(true);
  };

  const handleOpenTutorFromLesson = (topic) => {
    setActiveLesson(null);
    setTutorFocusTopic(topic || "Newton's Laws");
    setCurrentTab('tutor');
  };

  const handleQuizComplete = (result) => {
    loadFeed();
  };

  if (!session.user) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-main)', position: 'relative' }}>
        <div className="bg-ambient-orb orb-1"></div>
        <div className="bg-ambient-orb orb-2"></div>
        <AuthScreen onLoginSuccess={handleLoginSuccess} theme={theme} toggleTheme={toggleTheme} />
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-main)', position: 'relative' }}>
      {/* Ambient background glow orbs */}
      <div className="bg-ambient-orb orb-1"></div>
      <div className="bg-ambient-orb orb-2"></div>

      <Navbar
        currentTab={currentTab}
        setTab={setCurrentTab}
        user={session.user}
        onLogout={handleLogout}
        theme={theme}
        toggleTheme={toggleTheme}
        experienceMode={experienceMode}
        onSwitchExperience={handleSwitchExperience}
        activeChild={activeChild}
        onOpenParentGate={() => {
          setPendingTargetMode('parent');
          setParentGateOpen(true);
        }}
      />

      <main style={{ position: 'relative', zIndex: 1, paddingBottom: '60px' }}>
        {/* EXPERIENCE 1: EDUFEEDIA KIDS (0–10 YEARS) */}
        {experienceMode === 'kids' && (
          <KidsDashboard
            child={activeChild}
            onOpenParentGate={() => {
              setPendingTargetMode('parent');
              setParentGateOpen(true);
            }}
            onSwitchChild={(newChild) => setActiveChild(newChild)}
          />
        )}

        {/* EXPERIENCE 2: EDUFEEDIA PARENT HUB */}
        {experienceMode === 'parent' && (
          <ParentDashboard
            onLaunchKidsMode={(child) => {
              setActiveChild(child);
              setExperienceMode('kids');
            }}
          />
        )}

        {/* EXPERIENCE 3: EDUFEEDIA STUDENT (11–17 YEARS) */}
        {experienceMode === 'student' && (
          <>
            {currentTab === 'feed' && (
              <DailyPlanFeed
                dailyPlan={dailyPlan}
                loading={loadingFeed}
                error={feedError}
                onSelectLesson={handleSelectLesson}
                onOpenQuiz={() => {
                  setQuizLessonTarget(dailyPlan?.items?.[0] || null);
                  setQuizModalOpen(true);
                }}
                onOpenTutor={(topic) => handleOpenTutorFromLesson(topic)}
                onRetry={loadFeed}
              />
            )}

            {currentTab === 'explore' && (
              <ExploreCatalog
                onOpenLesson={handleSelectLesson}
                onOpenQuiz={(lesson) => {
                  setQuizLessonTarget(lesson);
                  setQuizModalOpen(true);
                }}
              />
            )}

            {currentTab === 'tutor' && (
              <SocraticTutorChat activeTopic={tutorFocusTopic} />
            )}

            {currentTab === 'challenges' && (
              <ClassChallenges />
            )}

            {currentTab === 'mastery' && (
              <MasteryDashboard
                onStartRevision={(topic) => {
                  setTutorFocusTopic(topic);
                  setCurrentTab('tutor');
                }}
              />
            )}
          </>
        )}

        {/* EXPERIENCE 4: TEACHER / FACULTY PORTAL */}
        {experienceMode === 'teacher' && (
          <TeacherDashboard />
        )}
      </main>

      {/* Lesson Player Modal (Student) */}
      {activeLesson && (
        <ContentPlayerModal
          lesson={activeLesson}
          onClose={() => setActiveLesson(null)}
          onCompleteAndQuiz={handleCompleteAndQuiz}
          onOpenTutor={handleOpenTutorFromLesson}
        />
      )}

      {/* Quiz Modal (Student) */}
      {quizModalOpen && (
        <QuizModal
          lesson={quizLessonTarget}
          onClose={() => {
            setQuizModalOpen(false);
            setQuizLessonTarget(null);
          }}
          onQuizComplete={handleQuizComplete}
        />
      )}

      {/* Parent Gate Modal (Protects exit from Kids Mode) */}
      <ParentGateModal
        isOpen={parentGateOpen}
        onClose={() => setParentGateOpen(false)}
        onSuccess={handleParentGateSuccess}
      />
    </div>
  );
}
