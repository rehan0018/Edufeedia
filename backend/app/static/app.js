// Edufeedia Client-Side Application Logic
const API_URL = window.location.origin + '/api/v1';

// Application State
let token = localStorage.getItem('edufeedia_token') || null;
let userRole = localStorage.getItem('edufeedia_role') || null;
let userId = localStorage.getItem('edufeedia_uid') || null;

// Student State
let currentFeed = [];
let activeQuiz = null;
let quizAnswers = {}; // question_id -> selected_answer
let activeQuestionIndex = 0;
let activeLesson = null;
let flashcardsDeck = [];
let activeFlashcardIndex = 0;

// Teacher State
let teacherClasses = [];
let selectedTeacherClassId = null;

// Parent State
let parentStudents = [];
let selectedParentStudentId = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkAuth();
});

// Event Listener Bindings
function setupEventListeners() {
  // Auth Tabs
  document.getElementById('tab-login').addEventListener('click', () => toggleAuthTabs('login'));
  document.getElementById('tab-register').addEventListener('click', () => toggleAuthTabs('register'));

  // Auth Forms
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('register-form').addEventListener('submit', handleRegister);

  // Logout
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Student Nav Tab Switcher
  const studentNavTabs = document.querySelectorAll('#student-nav-menu .nav-tab');
  studentNavTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      studentNavTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      switchStudentSubView(tab.dataset.tab);
    });
  });

  // Learning Modal Controls
  document.getElementById('btn-close-learning').addEventListener('click', closeLearningModal);
  document.getElementById('btn-complete-lesson').addEventListener('click', markLessonCompleted);

  // Quiz Modal Controls
  document.getElementById('btn-close-quiz').addEventListener('click', closeQuizModal);
  document.getElementById('btn-prev-question').addEventListener('click', () => navigateQuiz(-1));
  document.getElementById('btn-next-question').addEventListener('click', () => navigateQuiz(1));
  document.getElementById('btn-submit-quiz').addEventListener('click', submitQuizAnswers);
  document.getElementById('btn-finish-quiz').addEventListener('click', closeQuizModal);

  // Explore Search & Filters
  const searchInput = document.getElementById('explore-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => filterExploreLibrary());
  }

  const subjectPills = document.querySelectorAll('#explore-subject-filters .filter-pill');
  subjectPills.forEach(pill => {
    pill.addEventListener('click', () => {
      subjectPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      filterExploreLibrary();
    });
  });

  // Student Settings Form
  const settingsForm = document.getElementById('settings-profile-form');
  if (settingsForm) {
    settingsForm.addEventListener('submit', handleSaveStudentProfile);
  }

  // Teacher Modals & Selectors
  const teacherSelect = document.getElementById('teacher-class-select');
  if (teacherSelect) {
    teacherSelect.addEventListener('change', (e) => {
      selectedTeacherClassId = e.target.value;
      if (selectedTeacherClassId) {
        loadClassAnalytics(selectedTeacherClassId);
      }
    });
  }

  document.getElementById('btn-open-create-quiz').addEventListener('click', openTeacherQuizModal);
  document.getElementById('btn-close-teacher-quiz').addEventListener('click', closeTeacherQuizModal);
  document.getElementById('teacher-quiz-form').addEventListener('submit', handleTeacherCreateQuiz);

  document.getElementById('btn-open-create-assign').addEventListener('click', openTeacherAssignModal);
  document.getElementById('btn-close-teacher-assign').addEventListener('click', closeTeacherAssignModal);
  document.getElementById('teacher-assign-form').addEventListener('submit', handleTeacherCreateAssignment);

  // Parent Student Selection
  const parentStudentSelect = document.getElementById('student-select');
  if (parentStudentSelect) {
    parentStudentSelect.addEventListener('change', (e) => {
      if (e.target.value) {
        loadStudentProgressForParent(e.target.value);
      }
    });
  }
}

// Check & Restore Authentication
function checkAuth() {
  const authScreen = document.getElementById('auth-screen');
  const studentScreen = document.getElementById('student-screen');
  const teacherScreen = document.getElementById('teacher-screen');
  const parentScreen = document.getElementById('parent-screen');
  const navActions = document.getElementById('nav-actions');
  const studentNav = document.getElementById('student-nav-menu');
  const teacherNav = document.getElementById('teacher-nav-menu');

  if (token && userRole) {
    authScreen.classList.add('hidden');
    navActions.classList.remove('hidden');

    document.getElementById('user-badge-display').innerHTML = `
      <i class="fa-regular fa-user"></i> <span>${userRole.toUpperCase()}</span>
    `;

    if (userRole === 'student') {
      studentNav.classList.remove('hidden');
      teacherNav.classList.add('hidden');
      studentScreen.classList.remove('hidden');
      teacherScreen.classList.add('hidden');
      parentScreen.classList.add('hidden');

      loadStudentFeed();
      loadStudentStats();
      loadStudentAssignments();
    } else if (userRole === 'teacher') {
      studentNav.classList.add('hidden');
      teacherNav.classList.remove('hidden');
      studentScreen.classList.add('hidden');
      teacherScreen.classList.remove('hidden');
      parentScreen.classList.add('hidden');

      loadTeacherDashboard();
    } else if (userRole === 'parent') {
      studentNav.classList.add('hidden');
      teacherNav.classList.add('hidden');
      studentScreen.classList.add('hidden');
      teacherScreen.classList.add('hidden');
      parentScreen.classList.remove('hidden');

      loadParentDashboard();
    }
  } else {
    authScreen.classList.remove('hidden');
    studentScreen.classList.add('hidden');
    teacherScreen.classList.add('hidden');
    parentScreen.classList.add('hidden');
    navActions.classList.add('hidden');
    studentNav.classList.add('hidden');
    teacherNav.classList.add('hidden');
  }
}

// Fill Demo Accounts
function loadDemoAccount(role) {
  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');

  if (role === 'student') {
    emailInput.value = 'rahul@apexschool.edu';
    passwordInput.value = 'Student123!';
  } else if (role === 'parent') {
    emailInput.value = 'parent@gmail.com';
    passwordInput.value = 'Parent123!';
  } else if (role === 'teacher') {
    emailInput.value = 'sharma@apexschool.edu';
    passwordInput.value = 'Teacher123!';
  }

  document.getElementById('login-form').dispatchEvent(new Event('submit'));
}

// Toggle Auth Form Tabs
function toggleAuthTabs(tab) {
  const loginForm = document.getElementById('login-form');
  const regForm = document.getElementById('register-form');
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');

  if (tab === 'login') {
    loginForm.classList.remove('hidden');
    regForm.classList.add('hidden');
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
  } else {
    loginForm.classList.add('hidden');
    regForm.classList.remove('hidden');
    tabLogin.classList.remove('active');
    tabRegister.classList.add('active');
  }
}

// Handle Login
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await response.json();
    token = data.access_token;
    userRole = data.role;
    userId = data.user_id;

    localStorage.setItem('edufeedia_token', token);
    localStorage.setItem('edufeedia_role', userRole);
    localStorage.setItem('edufeedia_uid', userId);

    checkAuth();
  } catch (error) {
    alert(error.message);
  }
}

// Handle Register
async function handleRegister(e) {
  e.preventDefault();
  const firstName = document.getElementById('reg-firstname').value;
  const lastName = document.getElementById('reg-lastname').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  const dob = document.getElementById('reg-dob').value;
  const parentEmail = document.getElementById('reg-parent').value;

  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email: email,
        password: password,
        role: 'student',
        date_of_birth: dob,
        parent_email: parentEmail
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Registration failed');
    }

    alert('Registration submitted successfully! You can now log in.');
    toggleAuthTabs('login');
  } catch (error) {
    alert(error.message);
  }
}

// Handle Logout
function handleLogout() {
  token = null;
  userRole = null;
  userId = null;
  localStorage.removeItem('edufeedia_token');
  localStorage.removeItem('edufeedia_role');
  localStorage.removeItem('edufeedia_uid');
  checkAuth();
}

// ==================== STUDENT VIEWS & ACTIONS ====================

function switchStudentSubView(tabName) {
  const views = ['feed', 'flashcards', 'explore', 'leaderboard', 'profile-settings'];
  views.forEach(v => {
    const el = document.getElementById(`student-view-${v}`);
    if (el) {
      if (v === tabName) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  if (tabName === 'feed') {
    loadStudentFeed();
    loadStudentStats();
  } else if (tabName === 'flashcards') {
    loadFlashcardDeck();
  } else if (tabName === 'explore') {
    filterExploreLibrary();
  } else if (tabName === 'leaderboard') {
    loadLeaderboardAndBadges();
  } else if (tabName === 'profile-settings') {
    loadStudentProfileSettings();
  }
}

// Load Student Daily Feed
async function loadStudentFeed() {
  try {
    const response = await fetch(`${API_URL}/students/feed`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load learning feed');
    
    const data = await response.json();
    document.getElementById('student-greeting-name').textContent = data.greeting;
    document.getElementById('student-streak').textContent = data.streak;
    document.getElementById('student-xp').textContent = data.xp;
    
    currentFeed = data.learning_plan;
    renderFeedList(currentFeed);

    const quizCard = document.getElementById('quiz-launch-card');
    if (data.daily_quiz) {
      quizCard.classList.remove('hidden');
      document.getElementById('btn-start-quiz').onclick = () => launchQuiz(data.daily_quiz.quiz_id);
    } else {
      quizCard.classList.add('hidden');
    }
  } catch (error) {
    console.error(error);
  }
}

// Render Feed List with Multi-Stage Recommendation Badges & Feedback Signals
function renderFeedList(items) {
  const container = document.getElementById('feed-container');
  container.innerHTML = '';

  if (!items || items.length === 0) {
    container.innerHTML = `
      <div class="glass feed-card text-center" style="padding: 40px; text-align: center;">
        <i class="fa-solid fa-circle-check" style="font-size: 2.5rem; color: var(--status-green); margin-bottom:12px;"></i>
        <h4>All lessons completed for today!</h4>
        <p>Great job! Come back tomorrow for your next customized learning cycle, or explore extra topics in the Safe Library.</p>
      </div>
    `;
    return;
  }

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'glass feed-card';
    
    // Source formatting
    const sourceLabel = item.explanation ? (
      item.explanation.candidate_source === 'spaced_repetition' ? '<span class="badge badge-accent"><i class="fa-solid fa-clock-rotate-left"></i> Spaced Review</span>' :
      item.explanation.candidate_source === 'collaborative' ? '<span class="badge badge-subtle"><i class="fa-solid fa-users"></i> Peer Choice</span>' :
      '<span class="badge badge-subtle"><i class="fa-solid fa-brain"></i> AI Recommended</span>'
    ) : `<span class="badge badge-accent">${item.type.toUpperCase()}</span>`;

    const matchPct = item.relevance_percentage || (item.explanation ? item.explanation.relevance_percentage : 92);

    card.innerHTML = `
      <div class="feed-card-header">
        <div>
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span class="subject-badge">${item.subject}</span>
            <span class="badge badge-relevance"><i class="fa-solid fa-sparkles"></i> ${matchPct}% Match</span>
          </div>
          <h4 style="margin-top: 6px;">${item.title}</h4>
        </div>
        <div>
          ${sourceLabel}
        </div>
      </div>
      <p>${item.description || ''}</p>
      <div class="feed-card-meta">
        <div class="meta-item"><i class="fa-regular fa-clock"></i> ${item.duration_minutes} mins</div>
        <div class="meta-item"><i class="fa-solid fa-signal"></i> ${item.difficulty.toUpperCase()}</div>
        <div class="meta-item"><i class="fa-solid fa-bookmark"></i> ${item.topic}</div>
      </div>

      <!-- Implicit/Explicit Feedback Interaction Bar -->
      <div class="feed-card-actions">
        <button class="btn-feed-action" onclick="event.stopPropagation(); triggerInteraction('${item.id}', 'like', this)">
          <i class="fa-regular fa-heart"></i> Like
        </button>
        <button class="btn-feed-action" onclick="event.stopPropagation(); triggerInteraction('${item.id}', 'bookmark', this)">
          <i class="fa-regular fa-bookmark"></i> Save
        </button>
        <button class="btn-feed-action" onclick="event.stopPropagation(); triggerInteraction('${item.id}', 'skip', this)">
          <i class="fa-solid fa-forward-step"></i> Skip
        </button>
        <button class="btn-feed-action" style="margin-left:auto;" onclick="event.stopPropagation(); toggleScoreBreakdown('${item.id}')">
          <i class="fa-solid fa-chart-pie"></i> Match Breakdown
        </button>
      </div>

      <!-- Hidden AI Score Breakdown -->
      <div id="score-breakdown-${item.id}" class="score-breakdown-box hidden">
        <div class="breakdown-row">
          <span>Semantic Text Match:</span>
          <strong>${((item.explanation?.content_similarity || 0.8) * 100).toFixed(0)}%</strong>
        </div>
        <div class="breakdown-row">
          <span>Interest Profile Fit:</span>
          <strong>${((item.explanation?.interest_match || 0.9) * 100).toFixed(0)}%</strong>
        </div>
        <div class="breakdown-row">
          <span>Grade & Curriculum Alignment:</span>
          <strong>${((item.explanation?.grade_match || 1.0) * 100).toFixed(0)}%</strong>
        </div>
        <div class="breakdown-row">
          <span>Peer Behavioral Affinity:</span>
          <strong>${((item.explanation?.behavioral_score || 0.75) * 100).toFixed(0)}%</strong>
        </div>
      </div>
    `;
    card.onclick = () => openLearningModal(item);
    container.appendChild(card);
  });
}

function toggleScoreBreakdown(itemId) {
  const el = document.getElementById(`score-breakdown-${itemId}`);
  if (el) el.classList.toggle('hidden');
}

async function triggerInteraction(contentId, type, btnElement) {
  try {
    const response = await fetch(`${API_URL}/recommendations/interaction`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content_item_id: contentId,
        interaction_type: type,
        dwell_time_seconds: 15
      })
    });

    if (btnElement) {
      if (type === 'like') {
        btnElement.classList.toggle('liked');
        btnElement.innerHTML = btnElement.classList.contains('liked') ? '<i class="fa-solid fa-heart"></i> Liked' : '<i class="fa-regular fa-heart"></i> Like';
      } else if (type === 'bookmark') {
        btnElement.classList.toggle('bookmarked');
        btnElement.innerHTML = btnElement.classList.contains('bookmarked') ? '<i class="fa-solid fa-bookmark"></i> Saved' : '<i class="fa-regular fa-bookmark"></i> Save';
      } else if (type === 'skip') {
        btnElement.closest('.feed-card').style.opacity = '0.4';
        setTimeout(() => loadStudentFeed(), 600);
      }
    }
  } catch (error) {
    console.error('Interaction error:', error);
  }
}

// Load Student Subject Mastery & Stats
async function loadStudentStats() {
  try {
    const response = await fetch(`${API_URL}/students/dashboard`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load student stats');
    
    const data = await response.json();
    
    const radialBar = document.getElementById('mastery-radial-bar');
    const lessonsCount = document.getElementById('mastery-lessons-count');
    
    lessonsCount.textContent = data.total_lessons_completed;
    
    const maxTarget = 8;
    const pct = Math.min(1, data.total_lessons_completed / maxTarget);
    const offset = 314 - (pct * 314);
    radialBar.style.strokeDashoffset = offset;

    const container = document.getElementById('mastery-list-container');
    container.innerHTML = '';
    
    if (data.subject_mastery.length === 0) {
      container.innerHTML = `<div style="text-align:center; color:var(--text-muted); font-size:0.8rem;">No subjects completed yet.</div>`;
      return;
    }

    data.subject_mastery.forEach(mastery => {
      const item = document.createElement('div');
      item.className = 'mastery-item';
      item.innerHTML = `
        <span>${mastery.subject}</span>
        <span class="mastery-count">${mastery.completed_lessons} completed</span>
      `;
      container.appendChild(item);
    });
  } catch (error) {
    console.error(error);
  }
}

// Load Student Class Assignments in Sidebar
async function loadStudentAssignments() {
  const container = document.getElementById('sidebar-assignments-list');
  if (!container) return;

  try {
    // Fetch profile to get class_id
    const profRes = await fetch(`${API_URL}/students/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!profRes.ok) return;
    const prof = await profRes.json();

    if (!prof.class_id) {
      container.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted);">No class assignments.</div>`;
      return;
    }

    const assignRes = await fetch(`${API_URL}/teachers/assignments/${prof.class_id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!assignRes.ok) return;
    const assignments = await assignRes.json();

    container.innerHTML = '';
    if (assignments.length === 0) {
      container.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted);">No homework pending! 🎉</div>`;
      return;
    }

    assignments.slice(0, 3).forEach(a => {
      const el = document.createElement('div');
      el.className = 'assignment-item';
      el.innerHTML = `
        <h5>${a.title}</h5>
        <p>${a.instructions || ''}</p>
        <div class="assignment-due"><i class="fa-regular fa-calendar"></i> Due: ${a.due_date || 'This Week'}</div>
      `;
      container.appendChild(el);
    });
  } catch (error) {
    console.error(error);
  }
}

// ==================== LEARNING CONTENT MODAL ====================

function openLearningModal(item) {
  activeLesson = item;
  document.getElementById('modal-content-title').textContent = item.title;
  
  const videoCont = document.getElementById('video-iframe-container');
  const readingCont = document.getElementById('reading-text-container');
  
  if (item.type === 'video') {
    videoCont.classList.remove('hidden');
    readingCont.classList.add('hidden');
    videoCont.innerHTML = item.embed_code || `
      <iframe src="${item.source_url}" frameborder="0" allowfullscreen></iframe>
    `;
  } else {
    videoCont.classList.add('hidden');
    readingCont.classList.remove('hidden');
    readingCont.innerHTML = `
      <div style="font-family: var(--font-primary); color: var(--text-primary);">
        <p style="margin-bottom:15px; font-weight:600; color:var(--accent-cyan);"><i class="fa-solid fa-book-open"></i> Syllabus Reading Summary:</p>
        <p style="font-size:1rem; line-height:1.7;">${item.description}</p>
        <div style="margin-top:20px; padding:16px; background:rgba(255,255,255,0.04); border-radius:8px; border: 1px solid var(--border-glow);">
          <h5 style="color:var(--accent-cyan); margin-bottom:6px;"><i class="fa-solid fa-brain"></i> Active Recall Focus:</h5>
          <p style="font-size:0.88rem; color:var(--text-secondary);">
            Before closing this lesson, reflect on the core concept and its practical implications. Ready yourself for the daily practice quiz!
          </p>
        </div>
      </div>
    `;
  }

  // Reset tutor drawer
  const tutorBody = document.getElementById('tutor-body');
  if (tutorBody) tutorBody.classList.add('hidden');
  const tutorLog = document.getElementById('tutor-chat-log');
  if (tutorLog) {
    tutorLog.innerHTML = `<div style="color:var(--text-muted);">👋 Hello! I am your AI Socratic Tutor. Ask me any question, formula breakdown, or intuition about <strong>${item.topic}</strong>!</div>`;
  }
  const followUps = document.getElementById('tutor-followups');
  if (followUps) followUps.innerHTML = '';

  document.getElementById('learning-modal').classList.add('active');
}

function toggleTutorDrawer() {
  const body = document.getElementById('tutor-body');
  const icon = document.getElementById('tutor-toggle-icon');
  if (body) {
    body.classList.toggle('hidden');
    if (icon) {
      icon.innerHTML = body.classList.contains('hidden') ? '<i class="fa-solid fa-chevron-down"></i>' : '<i class="fa-solid fa-chevron-up"></i>';
    }
  }
}

async function sendTutorQuestion(presetQuestion) {
  if (!activeLesson) return;
  const input = document.getElementById('tutor-user-input');
  const question = presetQuestion || (input ? input.value.trim() : '');
  if (!question) return;

  if (input) input.value = '';
  const log = document.getElementById('tutor-chat-log');
  const followUpsContainer = document.getElementById('tutor-followups');

  if (log) {
    log.innerHTML += `
      <div style="margin-top:8px; margin-bottom:8px; text-align:right;">
        <span style="background:hsla(210,100%,65%,0.2); border:1px solid var(--accent-cyan); padding:6px 10px; border-radius:12px; display:inline-block; max-width:85%;">
          ${question}
        </span>
      </div>
      <div id="tutor-loading" style="color:var(--accent-cyan); font-size:0.8rem;"><i class="fa-solid fa-spinner fa-spin"></i> Thinking...</div>
    `;
    log.scrollTop = log.scrollHeight;
  }

  try {
    const response = await fetch(`${API_URL}/tutor/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content_item_id: activeLesson.id,
        question: question
      })
    });

    const loading = document.getElementById('tutor-loading');
    if (loading) loading.remove();

    if (!response.ok) throw new Error('Tutor unavailable');
    const data = await response.json();

    if (log) {
      log.innerHTML += `
        <div style="margin-top:8px; margin-bottom:8px; text-align:left;">
          <div style="background:hsla(222,40%,12%,0.9); border:1px solid var(--border-glow); padding:10px; border-radius:var(--radius-sm);">
            <div style="font-weight:600; color:var(--accent-cyan); margin-bottom:4px;"><i class="fa-solid fa-robot"></i> AI Tutor:</div>
            <div style="line-height:1.5; white-space:pre-wrap;">${data.answer}</div>
            <div style="margin-top:6px; font-style:italic; color:var(--text-secondary); font-size:0.8rem;">🤔 Socratic Prompt: ${data.socratic_cue}</div>
          </div>
        </div>
      `;
      log.scrollTop = log.scrollHeight;
    }

    if (followUpsContainer && data.follow_up_questions) {
      followUpsContainer.innerHTML = data.follow_up_questions.map(q => `
        <button class="btn-feed-action" style="font-size:0.75rem;" onclick="sendTutorQuestion('${q.replace(/'/g, "\\'")}')">
          💡 ${q}
        </button>
      `).join('');
    }
  } catch (err) {
    const loading = document.getElementById('tutor-loading');
    if (loading) loading.remove();
    if (log) log.innerHTML += `<div style="color:var(--status-red);">${err.message}</div>`;
  }
}

function closeLearningModal() {
  document.getElementById('learning-modal').classList.remove('active');
  document.getElementById('video-iframe-container').innerHTML = '';
  activeLesson = null;
}

async function markLessonCompleted() {
  if (!activeLesson) return;

  try {
    const response = await fetch(`${API_URL}/content/progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content_item_id: activeLesson.id,
        progress_percentage: 100
      })
    });

    if (!response.ok) throw new Error('Failed to save progress');
    const data = await response.json();
    
    closeLearningModal();
    loadStudentFeed();
    loadStudentStats();
    
    if (data.xp_earned > 0) {
      alert(`🎉 Good job! Lesson Completed. You earned +${data.xp_earned} XP!`);
    }
  } catch (error) {
    alert(error.message);
  }
}

// ==================== DAILY PRACTICE QUIZ ====================

async function launchQuiz(quizId) {
  try {
    const response = await fetch(`${API_URL}/quizzes/${quizId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not fetch quiz questions');
    
    activeQuiz = await response.json();
    quizAnswers = {};
    activeQuestionIndex = 0;

    document.getElementById('quiz-question-container').classList.remove('hidden');
    document.getElementById('quiz-report-container').classList.add('hidden');
    document.getElementById('btn-prev-question').classList.remove('hidden');
    document.getElementById('btn-next-question').classList.remove('hidden');
    document.getElementById('btn-submit-quiz').classList.add('hidden');
    document.getElementById('btn-finish-quiz').classList.add('hidden');

    document.getElementById('quiz-title').textContent = activeQuiz.title;
    renderQuestion();
    document.getElementById('quiz-modal').classList.add('active');
  } catch (error) {
    alert(error.message);
  }
}

function renderQuestion() {
  if (!activeQuiz || activeQuiz.questions.length === 0) return;
  const questions = activeQuiz.questions;
  const q = questions[activeQuestionIndex];

  const dots = document.getElementById('quiz-dots');
  dots.innerHTML = '';
  questions.forEach((_, idx) => {
    const dot = document.createElement('div');
    dot.className = `dot ${idx === activeQuestionIndex ? 'active' : ''} ${quizAnswers[questions[idx].id] ? 'completed' : ''}`;
    dots.appendChild(dot);
  });

  document.getElementById('q-difficulty').textContent = `Difficulty: ${q.difficulty.toUpperCase()}`;
  document.getElementById('q-text').textContent = `${activeQuestionIndex + 1}. ${q.question_text}`;
  
  const optionsList = document.getElementById('q-options');
  optionsList.innerHTML = '';
  
  q.options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = `option-btn ${quizAnswers[q.id] === opt ? 'selected' : ''}`;
    btn.textContent = opt;
    btn.onclick = () => selectQuizOption(q.id, opt);
    optionsList.appendChild(btn);
  });

  document.getElementById('btn-prev-question').disabled = (activeQuestionIndex === 0);
  
  if (activeQuestionIndex === questions.length - 1) {
    document.getElementById('btn-next-question').classList.add('hidden');
    document.getElementById('btn-submit-quiz').classList.remove('hidden');
  } else {
    document.getElementById('btn-next-question').classList.remove('hidden');
    document.getElementById('btn-submit-quiz').classList.add('hidden');
  }
}

function selectQuizOption(qId, selection) {
  quizAnswers[qId] = selection;
  renderQuestion();
}

function navigateQuiz(dir) {
  activeQuestionIndex += dir;
  renderQuestion();
}

function closeQuizModal() {
  document.getElementById('quiz-modal').classList.remove('active');
  activeQuiz = null;
  loadStudentFeed();
  loadStudentStats();
}

async function submitQuizAnswers() {
  if (!activeQuiz) return;
  
  const unanswered = activeQuiz.questions.filter(q => !quizAnswers[q.id]);
  if (unanswered.length > 0) {
    alert("Please answer all questions before submitting!");
    return;
  }

  const formattedAnswers = Object.keys(quizAnswers).map(qId => ({
    question_id: qId,
    selected_answer: quizAnswers[qId]
  }));

  try {
    const response = await fetch(`${API_URL}/quizzes/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        quiz_id: activeQuiz.id,
        answers: formattedAnswers
      })
    });

    if (!response.ok) throw new Error('Submission error');

    const result = await response.json();
    displayQuizReport(result);
  } catch (error) {
    alert(error.message);
  }
}

function displayQuizReport(result) {
  document.getElementById('quiz-question-container').classList.add('hidden');
  document.getElementById('quiz-report-container').classList.remove('hidden');
  
  document.getElementById('btn-prev-question').classList.add('hidden');
  document.getElementById('btn-next-question').classList.add('hidden');
  document.getElementById('btn-submit-quiz').classList.add('hidden');
  document.getElementById('btn-finish-quiz').classList.remove('hidden');

  document.getElementById('report-score-fraction').textContent = `${result.score} / ${result.max_score}`;
  document.getElementById('report-score-pct').textContent = `${result.accuracy_percentage.toFixed(0)}% Accuracy`;
  document.getElementById('report-xp-earned').textContent = result.xp_gained;

  const container = document.getElementById('report-solutions-list');
  container.innerHTML = '';

  result.results.forEach((r, idx) => {
    const card = document.createElement('div');
    card.className = `solution-card ${r.is_correct ? 'correct' : 'incorrect'}`;
    const origQuestion = activeQuiz.questions.find(q => q.id === r.question_id);

    card.innerHTML = `
      <div class="sol-status">${r.is_correct ? '<i class="fa-regular fa-circle-check" style="color:var(--status-green);"></i> Correct' : '<i class="fa-regular fa-circle-xmark" style="color:var(--status-red);"></i> Incorrect'}</div>
      <div class="sol-question">${idx + 1}. ${origQuestion ? origQuestion.question_text : 'Question'}</div>
      <div class="sol-ans">Your Answer: <strong style="color:${r.is_correct ? 'var(--status-green)' : 'var(--status-red)'};">${r.selected_answer}</strong></div>
      ${!r.is_correct ? `<div class="sol-ans">Correct Answer: <strong style="color:var(--status-green);">${r.correct_answer}</strong></div>` : ''}
      <div class="sol-explanation"><strong>Explanation:</strong> ${r.explanation || 'Study the subject topics to strengthen understanding.'}</div>
    `;
    container.appendChild(card);
  });
}

// ==================== ACTIVE RECALL FLASHCARDS ====================

async function loadFlashcardDeck() {
  try {
    const response = await fetch(`${API_URL}/flashcards/deck`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load flashcard deck');
    
    flashcardsDeck = await response.json();
    activeFlashcardIndex = 0;
    renderCurrentFlashcard();
  } catch (error) {
    console.error(error);
  }
}

function renderCurrentFlashcard() {
  const wrapper = document.getElementById('flashcard-wrapper');
  wrapper.classList.remove('flipped');
  document.getElementById('fc-hint-box').classList.add('hidden');

  if (!flashcardsDeck || flashcardsDeck.length === 0) {
    document.getElementById('fc-front-text').textContent = 'No flashcards due for review today!';
    document.getElementById('flashcard-counter').textContent = '0 / 0';
    return;
  }

  const card = flashcardsDeck[activeFlashcardIndex];
  document.getElementById('flashcard-counter').textContent = `Card ${activeFlashcardIndex + 1} of ${flashcardsDeck.length}`;
  document.getElementById('fc-subject').textContent = card.subject;
  document.getElementById('fc-subject-back').textContent = card.subject;
  document.getElementById('fc-topic').textContent = card.topic;
  document.getElementById('fc-front-text').textContent = card.front_text;
  document.getElementById('fc-back-text').textContent = card.back_text;
  document.getElementById('fc-hint-text').textContent = card.hint || 'No hint available for this concept.';
}

function toggleFlashcardFlip() {
  const wrapper = document.getElementById('flashcard-wrapper');
  wrapper.classList.toggle('flipped');
}

function toggleFlashcardHint() {
  const hintBox = document.getElementById('fc-hint-box');
  hintBox.classList.toggle('hidden');
}

async function rateFlashcard(rating) {
  if (!flashcardsDeck || flashcardsDeck.length === 0) return;
  const currentCard = flashcardsDeck[activeFlashcardIndex];

  try {
    const response = await fetch(`${API_URL}/flashcards/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        flashcard_id: currentCard.id,
        rating: rating
      })
    });

    if (!response.ok) throw new Error('Failed to record review');
    const result = await response.json();

    // Advance to next card
    if (activeFlashcardIndex < flashcardsDeck.length - 1) {
      activeFlashcardIndex++;
      renderCurrentFlashcard();
    } else {
      alert(`🎉 Flashcard deck completed! Earned +${result.xp_earned} XP.\n${result.message}`);
      loadFlashcardDeck();
    }
  } catch (error) {
    alert(error.message);
  }
}

// ==================== EXPLORE SAFE LIBRARY ====================

async function filterExploreLibrary() {
  const container = document.getElementById('explore-grid-container');
  if (!container) return;

  const searchInput = document.getElementById('explore-search-input');
  const query = searchInput ? searchInput.value.trim() : '';

  const activePill = document.querySelector('#explore-subject-filters .filter-pill.active');
  const subject = activePill ? activePill.dataset.subject : '';

  let url = `${API_URL}/content/explore?`;
  if (query) url += `query=${encodeURIComponent(query)}&`;
  if (subject) url += `subject=${encodeURIComponent(subject)}&`;

  try {
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not fetch explore items');
    const items = await response.json();

    container.innerHTML = '';
    if (items.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding: 40px; color:var(--text-muted);">
          <i class="fa-solid fa-search" style="font-size:2rem; margin-bottom:10px;"></i>
          <p>No educational items matching your search filter.</p>
        </div>
      `;
      return;
    }

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'glass explore-card';
      card.innerHTML = `
        <div class="explore-card-top">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="subject-badge">${item.subject}</span>
            <span class="badge ${item.is_completed ? 'badge-success' : 'badge-accent'}">
              ${item.is_completed ? '<i class="fa-solid fa-check"></i> Completed' : item.type.toUpperCase()}
            </span>
          </div>
          <h4>${item.title}</h4>
          <p>${item.description}</p>
        </div>
        <div class="explore-card-bottom">
          <span class="safety-tag"><i class="fa-solid fa-shield-halved"></i> 100% Kid-Safe</span>
          <span style="font-size:0.78rem; color:var(--text-muted);"><i class="fa-regular fa-clock"></i> ${item.duration_minutes} mins</span>
        </div>
      `;
      card.onclick = () => openLearningModal(item);
      container.appendChild(card);
    });
  } catch (error) {
    console.error(error);
  }
}

// ==================== LEADERBOARD & BADGES ====================

async function loadLeaderboardAndBadges() {
  try {
    // Load Leaderboard
    const lbRes = await fetch(`${API_URL}/students/leaderboard`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (lbRes.ok) {
      const lbData = await lbRes.json();
      renderLeaderboard(lbData);
    }

    // Load Badges
    const badgeRes = await fetch(`${API_URL}/students/badges`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (badgeRes.ok) {
      const badgeData = await badgeRes.json();
      renderBadges(badgeData);
    }
  } catch (error) {
    console.error(error);
  }
}

function renderLeaderboard(data) {
  const container = document.getElementById('leaderboard-table-container');
  container.innerHTML = '';

  data.forEach(entry => {
    const row = document.createElement('div');
    row.className = `leaderboard-row ${entry.is_current_user ? 'current-user' : ''}`;
    
    let rankClass = '';
    if (entry.rank === 1) rankClass = 'rank-1';
    else if (entry.rank === 2) rankClass = 'rank-2';
    else if (entry.rank === 3) rankClass = 'rank-3';

    row.innerHTML = `
      <div class="lb-rank-col">
        <div class="rank-badge ${rankClass}">#${entry.rank}</div>
        <div>
          <span class="lb-name">${entry.name} ${entry.is_current_user ? '(You)' : ''}</span>
          <div style="font-size:0.72rem; color:var(--text-muted);">Level ${entry.level} Scholar</div>
        </div>
      </div>
      <div class="lb-stats">
        <span class="lb-streak"><i class="fa-solid fa-fire"></i> ${entry.streak}d</span>
        <span class="lb-xp">${entry.xp} XP</span>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderBadges(data) {
  document.getElementById('lb-current-level').textContent = `Level ${data.level}`;
  document.getElementById('lb-level-title').textContent = data.level_title;
  document.getElementById('student-level-badge').textContent = `Lvl ${data.level}`;
  document.getElementById('student-level-title').textContent = data.level_title;
  document.getElementById('lb-xp-fraction').textContent = `${data.current_xp} / ${data.next_level_xp} XP`;
  document.getElementById('badges-unlocked-count').textContent = `${data.unlocked_count}/${data.total_badges}`;

  const pct = Math.min(100, Math.round((data.current_xp / data.next_level_xp) * 100));
  document.getElementById('lb-xp-progress-bar').style.width = `${pct}%`;

  const container = document.getElementById('badges-grid-container');
  container.innerHTML = '';

  data.badges.forEach(b => {
    const item = document.createElement('div');
    item.className = `badge-item ${b.unlocked ? 'unlocked' : 'locked'}`;
    item.innerHTML = `
      <div class="badge-icon-box">
        <i class="fa-solid ${b.icon}"></i>
      </div>
      <span class="badge-name">${b.name}</span>
      <span class="badge-desc">${b.description}</span>
      <span class="badge ${b.unlocked ? 'badge-success' : ''}" style="font-size:0.68rem; margin-top:4px;">
        ${b.unlocked ? '<i class="fa-solid fa-check"></i> Unlocked' : '<i class="fa-solid fa-lock"></i> Locked'}
      </span>
    `;
    container.appendChild(item);
  });
}

// ==================== PROFILE SETTINGS ====================

async function loadStudentProfileSettings() {
  try {
    const response = await fetch(`${API_URL}/students/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) return;
    const profile = await response.json();

    // Select Board
    const boardInputs = document.querySelectorAll('input[name="student-board"]');
    boardInputs.forEach(input => {
      input.checked = (input.value === profile.board);
    });

    // Interests
    const interestChips = document.querySelectorAll('.interests-selector-group input[type="checkbox"]:not([name="learning-pref"])');
    interestChips.forEach(chip => {
      chip.checked = (profile.interests && profile.interests.includes(chip.value));
    });

    // Learning prefs
    const prefChips = document.querySelectorAll('input[name="learning-pref"]');
    prefChips.forEach(chip => {
      chip.checked = (profile.learning_preference && profile.learning_preference.includes(chip.value));
    });
  } catch (error) {
    console.error(error);
  }
}

async function handleSaveStudentProfile(e) {
  e.preventDefault();

  const selectedBoard = document.querySelector('input[name="student-board"]:checked')?.value || 'CBSE';
  
  const selectedInterests = [];
  document.querySelectorAll('.interests-selector-group input[type="checkbox"]:not([name="learning-pref"]):checked').forEach(c => {
    selectedInterests.push(c.value);
  });

  const selectedPrefs = [];
  document.querySelectorAll('input[name="learning-pref"]:checked').forEach(c => {
    selectedPrefs.push(c.value);
  });

  try {
    const response = await fetch(`${API_URL}/students/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        board: selectedBoard,
        interests: selectedInterests,
        learning_preference: selectedPrefs
      })
    });

    if (!response.ok) throw new Error('Could not update profile preferences');
    alert('Curriculum preferences saved! Your personalized learning feed has been updated.');
    
    // Switch to feed
    document.querySelector('#student-nav-menu button[data-tab="feed"]').click();
  } catch (error) {
    alert(error.message);
  }
}

// ==================== TEACHER PORTAL ====================

async function loadTeacherDashboard() {
  try {
    const response = await fetch(`${API_URL}/teachers/classes`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load teacher classes');
    
    teacherClasses = await response.json();
    const select = document.getElementById('teacher-class-select');
    select.innerHTML = '';

    if (teacherClasses.length === 0) {
      select.innerHTML = `<option value="">No assigned classes</option>`;
      return;
    }

    teacherClasses.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.class_id;
      opt.textContent = `Grade ${c.grade_level}-${c.section_name} (${c.subject})`;
      select.appendChild(opt);
    });

    selectedTeacherClassId = teacherClasses[0].class_id;
    loadClassAnalytics(selectedTeacherClassId);
    initSafetyInspector();
  } catch (error) {
    console.error(error);
  }
}

async function loadClassAnalytics(classId) {
  try {
    const response = await fetch(`${API_URL}/teachers/classes/${classId}/analytics`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not fetch class analytics');
    
    const data = await response.json();

    document.getElementById('teacher-total-students').textContent = data.total_students;
    document.getElementById('teacher-avg-accuracy').textContent = `${data.class_average_accuracy}%`;
    document.getElementById('teacher-lessons-count').textContent = data.total_lessons_completed;
    document.getElementById('teacher-at-risk-count').textContent = data.at_risk_students_count;

    // Render roster table
    const tbody = document.getElementById('teacher-roster-tbody');
    tbody.innerHTML = '';

    data.students.forEach(s => {
      const row = document.createElement('tr');
      
      let statusHtml = '';
      if (s.average_accuracy >= 85) {
        statusHtml = `<span class="status-pill status-mastering">Mastering</span>`;
      } else if (s.average_accuracy >= 70) {
        statusHtml = `<span class="status-pill status-ontrack">On Track</span>`;
      } else {
        statusHtml = `<span class="status-pill status-atrisk">Needs Attention</span>`;
      }

      row.innerHTML = `
        <td><strong>${s.name}</strong></td>
        <td>${s.email}</td>
        <td><strong style="color:var(--accent-cyan);">${s.xp} XP</strong></td>
        <td><i class="fa-solid fa-fire text-orange"></i> ${s.streak}d</td>
        <td><strong>${s.average_accuracy}%</strong></td>
        <td>${s.lessons_completed} lessons</td>
        <td>${statusHtml}</td>
      `;
      tbody.appendChild(row);
    });

    // Load assignments for this class
    loadTeacherClassAssignments(classId);
  } catch (error) {
    console.error(error);
  }
}

async function loadTeacherClassAssignments(classId) {
  const container = document.getElementById('teacher-assignments-container');
  container.innerHTML = '';

  try {
    const response = await fetch(`${API_URL}/teachers/assignments/${classId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) return;
    const assignments = await response.json();

    if (assignments.length === 0) {
      container.innerHTML = `<div style="font-size:0.85rem; color:var(--text-muted);">No assignments dispatched yet.</div>`;
      return;
    }

    assignments.forEach(a => {
      const card = document.createElement('div');
      card.className = 'assignment-item';
      card.innerHTML = `
        <h5>${a.title}</h5>
        <p>${a.instructions || ''}</p>
        <div class="assignment-due"><i class="fa-regular fa-calendar"></i> Due: ${a.due_date || 'No deadline'}</div>
      `;
      container.appendChild(card);
    });
  } catch (error) {
    console.error(error);
  }
}

function openTeacherQuizModal() {
  document.getElementById('teacher-quiz-modal').classList.add('active');
}

function closeTeacherQuizModal() {
  document.getElementById('teacher-quiz-modal').classList.remove('active');
}

async function handleTeacherCreateQuiz(e) {
  e.preventDefault();
  const title = document.getElementById('tq-title').value;
  const qtext = document.getElementById('tq-qtext').value;
  const opt1 = document.getElementById('tq-opt1').value;
  const opt2 = document.getElementById('tq-opt2').value;
  const opt3 = document.getElementById('tq-opt3').value;
  const opt4 = document.getElementById('tq-opt4').value;
  const correct = document.getElementById('tq-correct').value;
  const exp = document.getElementById('tq-explanation').value;

  try {
    const response = await fetch(`${API_URL}/teachers/quizzes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title: title,
        questions: [
          {
            question_text: qtext,
            options: [opt1, opt2, opt3, opt4],
            correct_answer: correct,
            explanation: exp,
            difficulty: "medium"
          }
        ]
      })
    });

    if (!response.ok) throw new Error('Could not create quiz');
    alert('Quiz created successfully and added to curriculum bank!');
    closeTeacherQuizModal();
    document.getElementById('teacher-quiz-form').reset();
  } catch (error) {
    alert(error.message);
  }
}

function openTeacherAssignModal() {
  document.getElementById('teacher-assign-modal').classList.add('active');
}

function closeTeacherAssignModal() {
  document.getElementById('teacher-assign-modal').classList.remove('active');
}

async function handleTeacherCreateAssignment(e) {
  e.preventDefault();
  if (!selectedTeacherClassId) {
    alert('Please select a class first');
    return;
  }

  const title = document.getElementById('ta-title').value;
  const instructions = document.getElementById('ta-instructions').value;
  const dueDate = document.getElementById('ta-duedate').value;

  try {
    const response = await fetch(`${API_URL}/teachers/assignments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        class_id: selectedTeacherClassId,
        title: title,
        instructions: instructions,
        due_date: dueDate || null
      })
    });

    if (!response.ok) throw new Error('Could not dispatch assignment');
    alert('Assignment dispatched to class!');
    closeTeacherAssignModal();
    document.getElementById('teacher-assign-form').reset();
    loadTeacherClassAssignments(selectedTeacherClassId);
  } catch (error) {
    alert(error.message);
  }
}

// ==================== PARENT PORTAL ====================

async function loadParentDashboard() {
  try {
    const response = await fetch(`${API_URL}/parents/students`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load parent configurations');
    
    parentStudents = await response.json();
    const selector = document.getElementById('student-select');
    selector.innerHTML = '';

    if (parentStudents.length === 0) {
      selector.innerHTML = `<option value="">No children registered</option>`;
      document.getElementById('parent-dashboard-content').style.opacity = '0.5';
      return;
    }

    parentStudents.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.student_id;
      opt.textContent = `${s.name} (Grade ${s.board})`;
      selector.appendChild(opt);
    });

    selectedParentStudentId = parentStudents[0].student_id;
    loadStudentProgressForParent(selectedParentStudentId);
  } catch (error) {
    console.error(error);
  }
}

async function loadStudentProgressForParent(studentId) {
  try {
    const response = await fetch(`${API_URL}/parents/student/${studentId}/progress`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load student progress details');
    
    const data = await response.json();

    document.getElementById('parent-accuracy').textContent = `${data.average_quiz_accuracy.toFixed(0)}%`;
    document.getElementById('parent-lessons-count').textContent = data.total_lessons_completed;
    document.getElementById('parent-streak-count').textContent = `${data.streak} Days`;

    // Dynamic horizontal mastery bars
    const barContainer = document.getElementById('parent-subject-bars');
    barContainer.innerHTML = '';

    if (data.subject_progress.length === 0) {
      barContainer.innerHTML = `<div style="color:var(--text-muted); font-size:0.85rem; text-align:center;">No lesson completions recorded.</div>`;
    } else {
      data.subject_progress.forEach(progress => {
        const row = document.createElement('div');
        row.className = 'bar-row';
        const capacity = 4;
        const pct = Math.min(100, (progress.lessons_completed / capacity) * 100);
        
        row.innerHTML = `
          <div class="bar-row-lbls">
            <span>${progress.subject}</span>
            <span>${progress.lessons_completed} completed</span>
          </div>
          <div class="bar-outer">
            <div class="bar-inner" style="width: ${pct}%"></div>
          </div>
        `;
        barContainer.appendChild(row);
      });
    }

    // AI insights printing
    const strengthsText = document.getElementById('parent-strengths-text');
    const focusText = document.getElementById('parent-focus-text');
    
    if (data.academic_insights.strengths && data.academic_insights.strengths.length > 0) {
      strengthsText.textContent = data.academic_insights.strengths.map(s => `${s.subject} (${s.accuracy.toFixed(0)}% accuracy)`).join(', ');
    } else {
      strengthsText.textContent = 'Awaiting further quiz results to calculate strengths.';
    }

    if (data.academic_insights.weaknesses && data.academic_insights.weaknesses.length > 0) {
      focusText.textContent = data.academic_insights.weaknesses.map(w => `${w.subject} (${w.accuracy.toFixed(0)}% accuracy)`).join(', ');
    } else {
      focusText.textContent = 'None identified. Performance meets school board standards.';
    }
  } catch (error) {
    console.error(error);
  }
}

// ==================== AI SAFETY INSPECTOR ====================

function initSafetyInspector() {
  const form = document.getElementById('safety-inspector-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('inspector-input');
    const resultBox = document.getElementById('safety-audit-results');
    const query = input.value.trim();
    if (!query) return;

    resultBox.classList.remove('hidden');
    resultBox.innerHTML = `<div style="text-align:center; padding:12px; color:var(--accent-cyan);"><i class="fa-solid fa-spinner fa-spin"></i> Running multi-stage safety audit...</div>`;

    try {
      const response = await fetch(`${API_URL}/recommendations/inspect-safety`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: query,
          description: '',
          target_age_group: 16
        })
      });

      if (!response.ok) throw new Error('Safety check failed');
      const audit = await response.json();

      const verdictClass = audit.verdict === 'ALLOW' ? 'status-allow' : (audit.verdict === 'REVIEW' ? 'status-review' : 'status-block');
      const verdictIcon = audit.verdict === 'ALLOW' ? 'fa-circle-check' : (audit.verdict === 'REVIEW' ? 'fa-triangle-exclamation' : 'fa-ban');

      let catHtml = '';
      if (audit.categories && audit.categories.length > 0) {
        catHtml = `
          <div class="audit-category-grid">
            ${audit.categories.map(c => `
              <div class="audit-cat-item">
                <div class="audit-cat-title">${c.category.replace(/_/g, ' ')}</div>
                <div class="audit-cat-val ${c.score > 0.5 ? 'text-orange' : 'text-green'}">
                  ${(c.score * 100).toFixed(0)}% <small style="font-size:0.7rem; font-weight:normal;">(${c.severity})</small>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      }

      resultBox.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid var(--border-glow);">
          <div>
            <span style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Audit Verdict</span>
            <h4 class="${verdictClass}" style="margin-top:2px;">
              <i class="fa-solid ${verdictIcon}"></i> ${audit.verdict} (Safety Score: ${audit.safety_score}/100)
            </h4>
          </div>
          <span class="badge ${audit.is_safe ? 'badge-accent' : 'badge-subtle'}">
            ${audit.is_safe ? 'Safe for Student Feed' : 'Blocked / Excluded'}
          </span>
        </div>
        <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:8px;">${audit.explanation}</p>
        ${audit.matched_rules && audit.matched_rules.length > 0 ? `
          <div style="color:var(--status-red); font-size:0.8rem; margin-bottom:8px;">
            <i class="fa-solid fa-triangle-exclamation"></i> <strong>Triggered Safety Rules:</strong> ${audit.matched_rules.join(', ')}
          </div>
        ` : ''}
        ${catHtml}
      `;
    } catch (err) {
      resultBox.innerHTML = `<div style="color:var(--status-red);">${err.message}</div>`;
    }
  });
}

// Initialize inspector when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  initSafetyInspector();
});
