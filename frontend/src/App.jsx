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
import { getSession, clearAuthSession, fetchDailyPlanFeed } from './services/api';

export default function App() {
  const [session, setSession] = useState(getSession());
  const [currentTab, setCurrentTab] = useState('feed');
  const [dailyPlan, setDailyPlan] = useState(null);
  const [loadingFeed, setLoadingFeed] = useState(false);
  const [feedError, setFeedError] = useState('');
  
  const [activeLesson, setActiveLesson] = useState(null);
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [quizLessonTarget, setQuizLessonTarget] = useState(null);
  const [tutorFocusTopic, setTutorFocusTopic] = useState("Newton's Laws");

  useEffect(() => {
    if (session.user && session.user.role === 'student') {
      loadFeed();
    }
  }, [session.user]);

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
    if (user.role === 'teacher' || user.role === 'school_admin') setCurrentTab('teacher');
    else if (user.role === 'parent') setCurrentTab('parent');
    else setCurrentTab('feed');
  };

  const handleLogout = () => {
    clearAuthSession();
    setSession({ user: null, role: 'student', token: '' });
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
    // Re-fetch fresh daily plan from backend after real quiz attempt is stored
    loadFeed();
  };

  if (!session.user) {
    return <AuthScreen onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div>
      {/* Ambient background glow orbs */}
      <div className="bg-ambient-orb orb-1"></div>
      <div className="bg-ambient-orb orb-2"></div>

      <Navbar
        currentTab={currentTab}
        setTab={setCurrentTab}
        user={session.user}
        onLogout={handleLogout}
      />

      <main style={{ position: 'relative', zIndex: 1, paddingBottom: '60px' }}>
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

        {currentTab === 'teacher' && <TeacherDashboard />}

        {currentTab === 'parent' && <ParentDashboard />}
      </main>

      {/* Lesson Player Modal */}
      {activeLesson && (
        <ContentPlayerModal
          lesson={activeLesson}
          onClose={() => setActiveLesson(null)}
          onCompleteAndQuiz={handleCompleteAndQuiz}
          onOpenTutor={handleOpenTutorFromLesson}
        />
      )}

      {/* Quiz Modal */}
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
    </div>
  );
}
