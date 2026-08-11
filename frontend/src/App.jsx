import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DailyPlanFeed from './components/DailyPlanFeed';
import ContentPlayerModal from './components/ContentPlayerModal';
import QuizModal from './components/QuizModal';
import SocraticTutorChat from './components/SocraticTutorChat';
import MasteryDashboard from './components/MasteryDashboard';
import TeacherDashboard from './components/TeacherDashboard';
import ParentDashboard from './components/ParentDashboard';
import AuthScreen from './components/AuthScreen';
import { getSession, clearAuthSession, fetchDailyPlanFeed } from './services/api';

export default function App() {
  const [session, setSession] = useState(getSession());
  const [currentTab, setCurrentTab] = useState('feed');
  const [dailyPlan, setDailyPlan] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [tutorFocusTopic, setTutorFocusTopic] = useState("Newton's Laws");

  useEffect(() => {
    if (session.user) {
      fetchDailyPlanFeed().then(setDailyPlan);
    }
  }, [session.user]);

  const handleLoginSuccess = (user) => {
    setSession({ user, role: user.role, token: localStorage.getItem('edufeedia_token') });
    if (user.role === 'teacher') setCurrentTab('teacher');
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
    setQuizModalOpen(true);
  };

  const handleOpenTutorFromLesson = (topic) => {
    setActiveLesson(null);
    setTutorFocusTopic(topic || "Newton's Laws");
    setCurrentTab('tutor');
  };

  const handleQuizComplete = (score) => {
    // Refresh daily plan and XP after quiz attempt
    if (dailyPlan) {
      const updatedItems = dailyPlan.items.map(item => {
        if (item.topic === "Newton's Laws" || item.topic === "Human Respiration") {
          return { ...item, is_completed: true };
        }
        return item;
      });
      setDailyPlan({ ...dailyPlan, items: updatedItems, xp: (dailyPlan.xp || 350) + score * 20 });
    }
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
            onSelectLesson={handleSelectLesson}
            onOpenQuiz={() => setQuizModalOpen(true)}
            onOpenTutor={(topic) => handleOpenTutorFromLesson(topic)}
          />
        )}

        {currentTab === 'tutor' && (
          <SocraticTutorChat activeTopic={tutorFocusTopic} />
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
          lesson={activeLesson}
          onClose={() => setQuizModalOpen(false)}
          onQuizComplete={handleQuizComplete}
        />
      )}
    </div>
  );
}
