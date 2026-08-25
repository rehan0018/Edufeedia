// ==============================================================================
// Edufeedia Frontend API Client (Production-Grade)
// Direct integration with FastAPI backend (http://127.0.0.1:8000/api/v1)
// ==============================================================================

const API_BASE_URL = '/api/v1';
const IS_DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

let authToken = localStorage.getItem('edufeedia_token') || '';
let currentRole = localStorage.getItem('edufeedia_role') || 'student';
let currentUserData = JSON.parse(localStorage.getItem('edufeedia_user') || 'null');

export const setAuthSession = (token, user, role = 'student') => {
  authToken = token;
  currentUserData = user;
  currentRole = role;
  localStorage.setItem('edufeedia_token', token);
  localStorage.setItem('edufeedia_user', JSON.stringify(user));
  localStorage.setItem('edufeedia_role', role);
};

export const clearAuthSession = () => {
  authToken = '';
  currentUserData = null;
  currentRole = 'student';
  localStorage.removeItem('edufeedia_token');
  localStorage.removeItem('edufeedia_user');
  localStorage.removeItem('edufeedia_role');
};

export const getSession = () => ({
  token: authToken,
  user: currentUserData,
  role: currentRole
});

export const defaultHeaders = () => ({
  'Content-Type': 'application/json',
  ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
});

export const apiFetch = async (endpoint, options = {}) => {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const headers = {
    ...defaultHeaders(),
    ...(options.headers || {})
  };
  
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    clearAuthSession();
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('auth_session_expired'));
    }
    const err = await res.json().catch(() => ({ detail: 'Session expired. Please log in again.' }));
    throw new Error(err.detail || 'Session expired.');
  }
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: `Request failed with status ${res.status}` }));
    throw new Error(errData.detail || errData.message || `Request failed (${res.status})`);
  }
  return await res.json();
};

// 1. Real Authentication Service
export const apiLogin = async (email, password) => {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (!res.ok) {
    if (IS_DEMO_MODE) {
      if (email.includes('rahul') || email.includes('student')) {
        const demoUser = { id: 'u-student-1', email, first_name: 'Rahul', last_name: 'Kumar', role: 'student', grade: 10, board: 'CBSE' };
        setAuthSession('demo-token-student', demoUser, 'student');
        return { access_token: 'demo-token-student', user: demoUser };
      } else if (email.includes('sharma') || email.includes('priya') || email.includes('teacher')) {
        const demoUser = { id: 'u-teacher-1', email, first_name: 'Sunita', last_name: 'Sharma', role: 'teacher' };
        setAuthSession('demo-token-teacher', demoUser, 'teacher');
        return { access_token: 'demo-token-teacher', user: demoUser };
      } else {
        const demoUser = { id: 'u-parent-1', email, first_name: 'Rajesh', last_name: 'Kumar', role: 'parent' };
        setAuthSession('demo-token-parent', demoUser, 'parent');
        return { access_token: 'demo-token-parent', user: demoUser };
      }
    }
    const errData = await res.json().catch(() => ({ detail: 'Authentication failed' }));
    throw new Error(errData.detail || 'Invalid email or password');
  }

  const data = await res.json();
  const userRole = data.role || data.user?.role || 'student';
  const userData = data.user || {
    id: data.user_id,
    email: email,
    role: userRole,
    first_name: userRole === 'teacher' ? 'Sunita' : (userRole === 'parent' ? 'Rajesh' : 'Rahul'),
    last_name: userRole === 'teacher' ? 'Sharma' : (userRole === 'parent' ? 'Kumar' : 'Kumar')
  };
  setAuthSession(data.access_token, userData, userRole);
  return { ...data, user: userData };
};

export const apiRegister = async (registerData) => {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(registerData)
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(errData.detail || 'Registration failed');
  }

  // Automatically authenticate upon successful registration
  return await apiLogin(registerData.email, registerData.password);
};

// 2. Student Daily Learning Plan Feed
export const fetchDailyPlanFeed = async () => {
  const res = await fetch(`${API_BASE_URL}/recommendations/feed`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('Unable to retrieve recommendations from learning server');
  }
  return await res.json();
};

// 3. Complete Lesson & Update Learning Progress
export const recordLessonProgress = async (contentItemId, progressPercentage = 100) => {
  const res = await fetch(`${API_BASE_URL}/content/progress`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: JSON.stringify({
      content_item_id: contentItemId,
      progress_percentage: progressPercentage
    })
  });
  if (!res.ok) {
    throw new Error('Failed to record lesson progress on server');
  }
  return await res.json();
};

// 4. Fetch Real Quiz for Content
export const fetchQuizForContent = async (contentItemId) => {
  const res = await fetch(`${API_BASE_URL}/quizzes/content/${contentItemId}`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('No assessment quiz available for this topic');
  }
  return await res.json();
};

// 5. Submit Real Quiz Attempt to Backend
export const submitQuizAttempt = async (quizId, answers) => {
  const res = await fetch(`${API_BASE_URL}/quizzes/submit`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: JSON.stringify({
      quiz_id: quizId,
      answers: answers.map(a => ({
        question_id: a.question_id,
        selected_answer: a.selected_answer
      }))
    })
  });
  if (!res.ok) {
    throw new Error('Failed to submit quiz attempt to grading server');
  }
  return await res.json();
};

// 6. Socratic AI Tutor API
export const askSocraticTutor = async (question, contentItemId = null) => {
  const res = await fetch(`${API_BASE_URL}/tutor/ask`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: JSON.stringify({ question, content_item_id: contentItemId })
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Tutor service unavailable' }));
    throw new Error(errData.detail || 'The AI Tutor is temporarily unavailable. Please try again.');
  }
  return await res.json();
};

// 7. Learning Analytics & Mastery Report
export const fetchMasteryAnalytics = async () => {
  const res = await fetch(`${API_BASE_URL}/students/analytics/mastery`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('Could not fetch student mastery analytics');
  }
  return await res.json();
};

// 8. Teacher Pending Moderation Queue
export const fetchTeacherPendingQueue = async () => {
  const res = await fetch(`${API_BASE_URL}/content/ingestion/pending`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('Failed to load pending moderation queue');
  }
  return await res.json();
};

// 9. Teacher Moderation Action (Approve / Reject)
export const reviewStagedContent = async (contentId, action, notes = '') => {
  const res = await fetch(`${API_BASE_URL}/content/ingestion/${contentId}/review`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: JSON.stringify({ action, moderator_notes: notes })
  });
  if (!res.ok) {
    throw new Error('Failed to submit moderation review');
  }
  return await res.json();
};

// 10. Teacher Class Analytics
export const fetchTeacherClasses = async () => {
  const res = await fetch(`${API_BASE_URL}/teachers/classes`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('Failed to load teacher class roster');
  }
  return await res.json();
};

export const fetchClassAnalytics = async (classId) => {
  const res = await fetch(`${API_BASE_URL}/teachers/classes/${classId}/analytics`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('Failed to load class analytics');
  }
  return await res.json();
};

// 11. Parent Linked Student Progress
export const fetchParentStudentSummary = async () => {
  const res = await fetch(`${API_BASE_URL}/parents/students`, {
    headers: defaultHeaders()
  });
  if (!res.ok) {
    throw new Error('Could not fetch linked student records');
  }
  const students = await res.json();
  if (!students || students.length === 0) return null;

  const firstStudent = students[0];
  const progressRes = await fetch(`${API_BASE_URL}/parents/student/${firstStudent.student_id}/progress`, {
    headers: defaultHeaders()
  });
  if (!progressRes.ok) {
    return { student: firstStudent, summary: null };
  }
  const summary = await progressRes.json();
  return { student: firstStudent, summary };
};

// 12. Explore Catalog Search & Filter
export const fetchExploreCatalog = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.query) queryParams.append('query', params.query);
  if (params.subject && params.subject !== 'All') queryParams.append('subject', params.subject);
  if (params.grade_level) queryParams.append('grade_level', params.grade_level);
  if (params.content_type) queryParams.append('content_type', params.content_type);

  const url = `${API_BASE_URL}/content/explore${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const res = await fetch(url, { headers: defaultHeaders() });
  if (!res.ok) {
    throw new Error('Failed to load explore catalog');
  }
  return await res.json();
};

// 13. Inter-Class Academic Challenges & Safe Leaderboard
export const fetchWeeklyChallenge = async () => {
  const res = await fetch(`${API_BASE_URL}/challenges/weekly`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('Failed to fetch weekly challenge');
  return await res.json();
};

export const fetchClassLeaderboard = async () => {
  const res = await fetch(`${API_BASE_URL}/challenges/class-leaderboard`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('Failed to fetch class leaderboard');
  return await res.json();
};

export const fetchMyPersonalGrowth = async () => {
  const res = await fetch(`${API_BASE_URL}/challenges/my-growth`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('Failed to fetch personal growth stats');
  return await res.json();
};

// 14. Faculty Assessment Creation (Manual Builder & AI Draft Review)
export const apiGenerateQuizDraft = async (subject, topic, gradeLevel = 10, numQuestions = 3) => {
  const res = await fetch(`${API_BASE_URL}/quizzes/generate-draft`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: JSON.stringify({
      subject,
      topic,
      grade_level: gradeLevel,
      num_questions: numQuestions
    })
  });
  if (!res.ok) {
    throw new Error('Failed to generate AI quiz draft');
  }
  return await res.json();
};

export const apiCreateCustomQuiz = async (quizData) => {
  const res = await fetch(`${API_BASE_URL}/quizzes/custom`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: JSON.stringify(quizData)
  });
  if (!res.ok) {
    throw new Error('Failed to publish assessment');
  }
  return await res.json();
};

// 15. Content Reporting
export const reportContent = async (contentItemId, reason, details = '') => {
  return await apiFetch('/content/report', {
    method: 'POST',
    body: JSON.stringify({ content_item_id: contentItemId, reason, details })
  });
};

// 16. Learning Health Score
export const fetchLearningHealth = async () => {
  return await apiFetch('/students/analytics/learning-health');
};

// 17. Parent Weekly Summary
export const fetchParentWeeklySummary = async (studentId) => {
  return await apiFetch(`/parents/student/${studentId}/weekly-summary`);
};

// 18. Teacher Interventions
export const fetchTeacherInterventions = async () => {
  return await apiFetch('/teachers/interventions');
};

// 19. Content Moderation Queue
export const fetchModerationQueue = async () => {
  return await apiFetch('/teachers/moderation-queue');
};

export const moderateContentReport = async (reportId, status, actionTaken = '') => {
  return await apiFetch('/teachers/moderate-report', {
    method: 'POST',
    body: JSON.stringify({ report_id: reportId, status, action_taken: actionTaken })
  });
};
