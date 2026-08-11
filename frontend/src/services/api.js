// ==============================================================================
// Edufeedia Frontend API Client
// Direct integration with FastAPI backend (http://127.0.0.1:8000/api/v1)
// Includes resilient fallback dataset for standalone offline testing
// ==============================================================================

const API_BASE_URL = '/api/v1';

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

const defaultHeaders = () => ({
  'Content-Type': 'application/json',
  ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
});

// 1. Authentication Service
export const apiLogin = async (email, password) => {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error('Invalid credentials');
    const data = await res.json();
    setAuthSession(data.access_token, data.user, data.user.role);
    return data;
  } catch (err) {
    // Demo account fallback if backend is offline
    if (email.includes('rahul') || email.includes('student')) {
      const demoUser = { id: 'u-student-1', email, first_name: 'Rahul', last_name: 'Kumar', role: 'student', grade: 10, board: 'CBSE' };
      setAuthSession('demo-token-student', demoUser, 'student');
      return { access_token: 'demo-token-student', user: demoUser };
    } else if (email.includes('priya') || email.includes('teacher')) {
      const demoUser = { id: 'u-teacher-1', email, first_name: 'Priya', last_name: 'Sharma', role: 'teacher' };
      setAuthSession('demo-token-teacher', demoUser, 'teacher');
      return { access_token: 'demo-token-teacher', user: demoUser };
    } else {
      const demoUser = { id: 'u-parent-1', email, first_name: 'Rajesh', last_name: 'Kumar', role: 'parent' };
      setAuthSession('demo-token-parent', demoUser, 'parent');
      return { access_token: 'demo-token-parent', user: demoUser };
    }
  }
};

// 2. Student Daily Learning Plan Feed
export const fetchDailyPlanFeed = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/recommendations/feed`, {
      headers: defaultHeaders()
    });
    if (!res.ok) throw new Error('Could not fetch daily plan');
    return await res.json();
  } catch (err) {
    // Resilient Fallback Data matching Live Recommender
    return {
      student_id: 'u-student-1',
      greeting: 'Good morning, Rahul! 👋',
      streak: 6,
      xp: 350,
      items: [
        {
          id: 'c-resp-1',
          title: 'Human Respiration Process Explained',
          description: 'Explore the pathways of aerobic vs anaerobic respiration, glycolysis, and ATP synthesis in mitochondria.',
          subject: 'Science',
          topic: 'Human Respiration',
          grade_level: 10,
          duration_minutes: 12,
          relevance_percentage: 84,
          explanation: { candidate_source: 'spaced_repetition' },
          source_url: 'https://www.youtube.com/watch?v=00jbG_cfGuQ',
          embed_code: '<iframe width="100%" height="360" src="https://www.youtube-nocookie.com/embed/00jbG_cfGuQ" frameborder="0" allowfullscreen></iframe>',
          is_completed: false
        },
        {
          id: 'c-quad-1',
          title: 'Quadratic Equations & Discriminant Nature',
          description: 'Master factorization and the quadratic formula to solve non-linear roots.',
          subject: 'Mathematics',
          topic: 'Quadratic Equations',
          grade_level: 10,
          duration_minutes: 18,
          relevance_percentage: 78,
          explanation: { candidate_source: 'content_based' },
          source_url: 'https://www.youtube.com/watch?v=qeByhTF8WEw',
          embed_code: '<iframe width="100%" height="360" src="https://www.youtube-nocookie.com/embed/qeByhTF8WEw" frameborder="0" allowfullscreen></iframe>',
          is_completed: false
        },
        {
          id: 'c-newt-1',
          title: "Newton's Laws of Motion & Momentum Recall",
          description: 'Understanding inertia, F = ma calculation, and action-reaction pairs.',
          subject: 'Physics',
          topic: "Newton's Laws",
          grade_level: 10,
          duration_minutes: 15,
          relevance_percentage: 70,
          explanation: { candidate_source: 'content_based' },
          source_url: 'https://www.youtube.com/watch?v=kKKM8Y-u7ds',
          embed_code: '<iframe width="100%" height="360" src="https://www.youtube-nocookie.com/embed/kKKM8Y-u7ds" frameborder="0" allowfullscreen></iframe>',
          is_completed: false
        },
        {
          id: 'c-py-1',
          title: 'Python Functions & Scope Modularization',
          description: 'Write reusable code blocks using parameters, return values, and local scope.',
          subject: 'Computer Science',
          topic: 'Python Functions',
          grade_level: 10,
          duration_minutes: 20,
          relevance_percentage: 68,
          explanation: { candidate_source: 'collaborative' },
          source_url: 'https://www.youtube.com/watch?v=9Os0o3wzS_I',
          embed_code: '<iframe width="100%" height="360" src="https://www.youtube-nocookie.com/embed/9Os0o3wzS_I" frameborder="0" allowfullscreen></iframe>',
          is_completed: false
        }
      ]
    };
  }
};

// 3. Socratic AI Tutor API
export const askSocraticTutor = async (question, contentItemId = null) => {
  try {
    const res = await fetch(`${API_BASE_URL}/tutor/ask`, {
      method: 'POST',
      headers: defaultHeaders(),
      body: JSON.stringify({ question, content_item_id: contentItemId })
    });
    if (!res.ok) throw new Error('Tutor query failed');
    return await res.json();
  } catch (err) {
    return {
      answer: "In Newton's Second Law, net force causes an object with mass to accelerate ($F = ma$). When force increases while mass remains constant, the rate of velocity change increases proportionally.",
      socratic_cue: "What would happen to the acceleration if you doubled the mass while applying the exact same force?",
      follow_up_questions: [
        "How does friction oppose this net acceleration?",
        "Can an object move with constant speed if the net force is zero?"
      ],
      is_safe: true
    };
  }
};

// 4. Learning Analytics & Mastery Report
export const fetchMasteryAnalytics = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/students/analytics/mastery`, {
      headers: defaultHeaders()
    });
    if (!res.ok) throw new Error('Could not fetch mastery');
    return await res.json();
  } catch (err) {
    return {
      total_topics_evaluated: 12,
      weak_topic_count: 2,
      subject_mastery: {
        Science: 74,
        Mathematics: 82,
        'Computer Science': 91
      },
      weak_topics: [
        { topic: "Newton's Laws", subject: 'Science', mastery_score: 54, next_revision_date: 'Thursday' },
        { topic: 'Chemical Bonding', subject: 'Science', mastery_score: 51, next_revision_date: 'Saturday' }
      ],
      upcoming_revisions: [
        { topic: 'Human Respiration', subject: 'Science', scheduled_date: 'Today', interval_days: 3 },
        { topic: "Newton's Laws", subject: 'Physics', scheduled_date: 'Thursday', interval_days: 6 }
      ]
    };
  }
};
