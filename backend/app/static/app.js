// API Base URL config
const API_URL = window.location.origin + '/api/v1';

// App State
let token = localStorage.getItem('edufeedia_token') || null;
let userRole = localStorage.getItem('edufeedia_role') || null;
let userId = localStorage.getItem('edufeedia_uid') || null;
let currentFeed = [];
let activeQuiz = null;
let quizAnswers = {}; // question_id -> selected_answer
let activeQuestionIndex = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkAuth();
});

// Event listeners binding
function setupEventListeners() {
  // Auth Tab Toggles
  document.getElementById('tab-login').addEventListener('click', () => toggleAuthTabs('login'));
  document.getElementById('tab-register').addEventListener('click', () => toggleAuthTabs('register'));

  // Auth Forms Submit
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('register-form').addEventListener('submit', handleRegister);

  // Logout button
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Learning Modal Action
  document.getElementById('btn-close-learning').addEventListener('click', closeLearningModal);
  document.getElementById('btn-complete-lesson').addEventListener('click', markLessonCompleted);

  // Quiz Modal Actions
  document.getElementById('btn-close-quiz').addEventListener('click', closeQuizModal);
  document.getElementById('btn-prev-question').addEventListener('click', () => navigateQuiz(-1));
  document.getElementById('btn-next-question').addEventListener('click', () => navigateQuiz(1));
  document.getElementById('btn-submit-quiz').addEventListener('click', submitQuizAnswers);
  document.getElementById('btn-finish-quiz').addEventListener('click', closeQuizModal);

  // Parent Student Selection Change
  document.getElementById('student-select').addEventListener('change', (e) => {
    if (e.target.value) {
      loadStudentProgressForParent(e.target.value);
    }
  });
}

// Authentication Check
function checkAuth() {
  if (token && userRole) {
    document.getElementById('nav-actions').classList.remove('hidden');
    document.getElementById('auth-screen').classList.add('hidden');
    
    document.getElementById('user-badge-display').innerHTML = `
      <i class="fa-regular fa-user"></i> <span>${userRole.toUpperCase()}</span>
    `;

    if (userRole === 'student') {
      document.getElementById('student-screen').classList.remove('hidden');
      document.getElementById('parent-screen').classList.add('hidden');
      loadStudentFeed();
      loadStudentStats();
    } else if (userRole === 'parent') {
      document.getElementById('student-screen').classList.add('hidden');
      document.getElementById('parent-screen').classList.remove('hidden');
      loadParentDashboard();
    }
  } else {
    document.getElementById('nav-actions').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
    document.getElementById('student-screen').classList.add('hidden');
    document.getElementById('parent-screen').classList.add('hidden');
  }
}

// Helper to fill demo account details
function loadDemoAccount(role) {
  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');
  
  if (role === 'student') {
    emailInput.value = 'rahul@apexschool.edu';
    passwordInput.value = 'Student123!';
  } else if (role === 'parent') {
    emailInput.value = 'parent@gmail.com';
    passwordInput.value = 'Parent123!';
  }
  
  // Trigger form submit
  document.getElementById('login-form').dispatchEvent(new Event('submit'));
}

// Toggle between Login & Register tabs
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

    alert('Registration submitted! If parent validation is required, have parent log in first.');
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

// Load Student Feed
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

// Render student daily learning items
function renderFeedList(items) {
  const container = document.getElementById('feed-container');
  container.innerHTML = '';

  if (items.length === 0) {
    container.innerHTML = `
      <div class="glass feed-card text-center" style="padding: 40px;">
        <i class="fa-solid fa-circle-check" style="font-size: 2.5rem; color: var(--status-green); margin-bottom:12px;"></i>
        <h4>All lessons completed for today!</h4>
        <p>Great job! Come back tomorrow for your next customized learning cycle.</p>
      </div>
    `;
    return;
  }

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'glass feed-card';
    card.innerHTML = `
      <div class="feed-card-header">
        <div>
          <span class="subject-badge">${item.subject}</span>
          <h4 style="margin-top: 8px;">${item.title}</h4>
        </div>
        <span class="badge badge-accent">${item.type}</span>
      </div>
      <p>${item.description}</p>
      <div class="feed-card-meta">
        <div class="meta-item"><i class="fa-regular fa-clock"></i> ${item.duration_minutes} mins</div>
        <div class="meta-item"><i class="fa-solid fa-signal"></i> ${item.difficulty.toUpperCase()}</div>
        <div class="meta-item"><i class="fa-solid fa-bookmark"></i> ${item.topic}</div>
      </div>
    `;
    card.onclick = () => openLearningModal(item);
    container.appendChild(card);
  });
}

// Load Student Subject Mastery & Stats
async function loadStudentStats() {
  try {
    const response = await fetch(`${API_URL}/students/dashboard`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load student stats');
    
    const data = await response.json();
    
    // Set circle progress (SVG path matching completions)
    const radialBar = document.getElementById('mastery-radial-bar');
    const lessonsCount = document.getElementById('mastery-lessons-count');
    
    lessonsCount.textContent = data.total_lessons_completed;
    
    // Animate radial bar: dasharray=314, calculate percentage
    const maxTarget = 10; // Let's set 10 completed lessons as master target
    const pct = Math.min(1, data.total_lessons_completed / maxTarget);
    const offset = 314 - (pct * 314);
    radialBar.style.strokeDashoffset = offset;

    // Render mastery subject list
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
        <span class="mastery-count">${mastery.completed_lessons} Mastery points</span>
      `;
      container.appendChild(item);
    });
  } catch (error) {
    console.error(error);
  }
}

// Active lesson details inside modal
let activeLesson = null;
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
        <p style="margin-bottom:15px; font-weight:600; color:var(--accent-cyan);"><i class="fa-solid fa-book-open"></i> Read the syllabus document summary below:</p>
        <p style="font-size:1rem; line-height:1.7;">${item.description}</p>
        <div style="margin-top:20px; padding:15px; background:rgba(255,255,255,0.03); border-radius:6px; border: 1px solid var(--border-glow);">
          <h5>💡 Active Recall Trigger:</h5>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:8px;">
            Think about these core topics before starting the daily quiz. Active recall helps establish long-term neural connections.
          </p>
        </div>
      </div>
    `;
  }

  document.getElementById('learning-modal').classList.add('active');
}

function closeLearningModal() {
  document.getElementById('learning-modal').classList.remove('active');
  document.getElementById('video-iframe-container').innerHTML = ''; // Clear iframe to stop video playing in bg
  activeLesson = null;
}

// Trigger POST to record progress completion
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

// Quiz Handlers
async function launchQuiz(quizId) {
  try {
    const response = await fetch(`${API_URL}/quizzes/${quizId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not fetch quiz questions');
    
    activeQuiz = await response.json();
    quizAnswers = {};
    activeQuestionIndex = 0;

    // Reset modals visibility state
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

  // Dots indicator
  const dots = document.getElementById('quiz-dots');
  dots.innerHTML = '';
  questions.forEach((_, idx) => {
    const dot = document.createElement('div');
    dot.className = `dot ${idx === activeQuestionIndex ? 'active' : ''} ${quizAnswers[questions[idx].id] ? 'completed' : ''}`;
    dots.appendChild(dot);
  });

  // Question metadata
  document.getElementById('q-difficulty').textContent = `Difficulty: ${q.difficulty}`;
  document.getElementById('q-text').textContent = `${activeQuestionIndex + 1}. ${q.question_text}`;
  
  // Options
  const optionsList = document.getElementById('q-options');
  optionsList.innerHTML = '';
  
  q.options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = `option-btn ${quizAnswers[q.id] === opt ? 'selected' : ''}`;
    btn.textContent = opt;
    btn.onclick = () => selectQuizOption(q.id, opt);
    optionsList.appendChild(btn);
  });

  // Buttons navigation toggling
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
  
  // Validate all questions answered
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

// Display Quiz Results grading details
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

  // Render solutions layout
  const container = document.getElementById('report-solutions-list');
  container.innerHTML = '';

  result.results.forEach((r, idx) => {
    const card = document.createElement('div');
    card.className = `solution-card ${r.is_correct ? 'correct' : 'incorrect'}`;
    
    // Find question text
    const origQuestion = activeQuiz.questions.find(q => q.id === r.question_id);

    card.innerHTML = `
      <div class="sol-status">${r.is_correct ? '<i class="fa-regular fa-circle-check"></i> Correct' : '<i class="fa-regular fa-circle-xmark"></i> Incorrect'}</div>
      <div class="sol-question">${idx + 1}. ${origQuestion ? origQuestion.question_text : 'Question'}</div>
      <div class="sol-ans">Your Answer: <strong style="color:${r.is_correct ? 'var(--status-green)' : 'var(--status-red)'};">${r.selected_answer}</strong></div>
      ${!r.is_correct ? `<div class="sol-ans">Correct Answer: <strong style="color:var(--status-green);">${r.correct_answer}</strong></div>` : ''}
      <div class="sol-explanation"><strong>Explanation:</strong> ${r.explanation || 'Study the subject topics to strengthen understanding.'}</div>
    `;
    container.appendChild(card);
  });
}

// ==================== PARENT PORTAL LOGIC ====================
async function loadParentDashboard() {
  try {
    const response = await fetch(`${API_URL}/parents/students`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Could not load parent configurations');
    
    const students = await response.json();
    const selector = document.getElementById('student-select');
    selector.innerHTML = '';

    if (students.length === 0) {
      selector.innerHTML = `<option value="">No children registered</option>`;
      document.getElementById('parent-dashboard-content').style.opacity = '0.5';
      return;
    }

    students.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.student_id;
      opt.textContent = `${s.name} (Grade ${s.board})`;
      selector.appendChild(opt);
    });

    // Auto-load first student progress details
    loadStudentProgressForParent(students[0].student_id);
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

    // KPIs
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
        
        // Calculate dynamic fill ratio (say mastery capacity is 5 completions)
        const capacity = 5;
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
