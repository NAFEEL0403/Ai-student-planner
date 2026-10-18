import { useState, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  // Auth state
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  
  // Auth Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Planner Form fields
  const [studentName, setStudentName] = useState('');
  const [selectedSubjects, setSelectedSubjects] = useState([]);
  const [topicsInput, setTopicsInput] = useState('');
  const [examDate, setExamDate] = useState('');
  const [dailyHours, setDailyHours] = useState(4);
  const [knowledgeLevel, setKnowledgeLevel] = useState('Beginner');
  const [preferredSession, setPreferredSession] = useState('Flexible');
  const [durationDays, setDurationDays] = useState(7);
  
  // Document upload state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadSubject, setUploadSubject] = useState('General');
  const [uploadLoading, setUploadLoading] = useState(false);
  
  // App UI states
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null); // { type: 'success'|'error', message: '' }
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const [completedDays, setCompletedDays] = useState([]);

  // Available subject options for multi-select
  const availableSubjects = ['DBMS', 'Python', 'Django', 'DSA'];

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
      // Pre-fill student name from user profile
      setStudentName(user.name || '');
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleLogout = () => {
    setToken('');
    setUser(null);
    setGeneratedPlan(null);
    setCompletedDays([]);
    showAlert('success', 'Logged out successfully.');
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      showAlert('error', 'Passwords do not match.');
      return;
    }
    
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/auth/signup/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          email,
          password,
          confirm_password: confirmPassword,
        }),
      });
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(Object.values(data).flat().join(' '));
      }
      
      showAlert('success', 'Signup successful! Please log in.');
      setAuthMode('login');
      // Clear password fields
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      showAlert('error', err.message || 'Signup failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Login failed. Please check your credentials.');
      }
      
      setToken(data.access);
      setUser(data.user);
      showAlert('success', `Welcome back, ${data.user.name}!`);
    } catch (err) {
      showAlert('error', err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSubject = (subj) => {
    if (selectedSubjects.includes(subj)) {
      setSelectedSubjects(selectedSubjects.filter(s => s !== subj));
    } else {
      setSelectedSubjects([...selectedSubjects, subj]);
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      showAlert('error', 'Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('subject', uploadSubject);

    try {
      setUploadLoading(true);
      const res = await fetch(`${API_BASE}/api/study-plan/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to upload document.');
      }

      showAlert('success', data.message || 'Document uploaded and indexed successfully!');
      setUploadFile(null);
      
      // Reset input element
      const fileInput = document.getElementById('doc-file-input');
      if (fileInput) fileInput.value = '';
    } catch (err) {
      showAlert('error', err.message || 'Upload failed.');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleGeneratePlan = async (e) => {
    e.preventDefault();
    if (selectedSubjects.length === 0) {
      showAlert('error', 'Please select at least one subject.');
      return;
    }
    if (!topicsInput.trim()) {
      showAlert('error', 'Please enter some topics to study.');
      return;
    }
    if (!examDate) {
      showAlert('error', 'Please select your target exam date.');
      return;
    }

    const topicsArray = topicsInput.split(',').map(t => t.trim()).filter(t => t.length > 0);

    try {
      setLoading(true);
      setGeneratedPlan(null);
      setCompletedDays([]);
      
      const res = await fetch(`${API_BASE}/api/study-plan/generate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: studentName,
          subjects: selectedSubjects,
          topics: topicsArray,
          exam_date: examDate,
          daily_hours: parseInt(dailyHours),
          knowledge_level: knowledgeLevel,
          preferred_session: preferredSession,
          duration_days: parseInt(durationDays)
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to generate study plan.');
      }

      setGeneratedPlan(data.generated_plan);
      showAlert('success', 'Study plan generated successfully!');
    } catch (err) {
      showAlert('error', err.message || 'Plan generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const toggleDayCompletion = (dayIndex) => {
    if (completedDays.includes(dayIndex)) {
      setCompletedDays(completedDays.filter(d => d !== dayIndex));
    } else {
      setCompletedDays([...completedDays, dayIndex]);
    }
  };

  const calculateProgress = () => {
    if (!durationDays) return 0;
    return Math.round((completedDays.length / durationDays) * 100);
  };

  return (
    <div className="container">
      {/* Title Header */}
      <div className="header">
        <h1>Student Study Planner</h1>
        {user && (
          <div>
            <span style={{ marginRight: '1rem', fontSize: '0.95rem' }}>
              Logged in as: <strong>{user.name}</strong>
            </span>
            <button className="btn btn-secondary" onClick={handleLogout}>Logout</button>
          </div>
        )}
      </div>

      {/* Alert Notifications */}
      {alert && (
        <div className={`alert alert-${alert.type}`}>
          {alert.message}
        </div>
      )}

      {/* Authentication Screen */}
      {!token ? (
        <div className="card" style={{ maxWidth: '450px', margin: '2rem auto' }}>
          <div className="auth-tabs">
            <div 
              className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
              onClick={() => setAuthMode('login')}
            >
              Login
            </div>
            <div 
              className={`auth-tab ${authMode === 'signup' ? 'active' : ''}`}
              onClick={() => setAuthMode('signup')}
            >
              Sign Up
            </div>
          </div>

          {authMode === 'login' ? (
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label>Email Address</label>
                <input 
                  type="email" 
                  className="form-control" 
                  required 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input 
                  type="password" 
                  className="form-control" 
                  required 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••"
                />
              </div>
              <button type="submit" className="btn" style={{ width: '100%' }} disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignup}>
              <div className="form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  className="form-control" 
                  required 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                />
              </div>
              <div className="form-group">
                <label>Email Address</label>
                <input 
                  type="email" 
                  className="form-control" 
                  required 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="john@example.com"
                />
              </div>
              <div className="form-group">
                <label>Password (Min. 6 chars)</label>
                <input 
                  type="password" 
                  className="form-control" 
                  required 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••"
                />
              </div>
              <div className="form-group">
                <label>Confirm Password</label>
                <input 
                  type="password" 
                  className="form-control" 
                  required 
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••"
                />
              </div>
              <button type="submit" className="btn" style={{ width: '100%' }} disabled={loading}>
                {loading ? 'Creating Account...' : 'Sign Up'}
              </button>
            </form>
          )}
        </div>
      ) : (
        /* Planner Dashboard Screen */
        <div className="form-row" style={{ gridTemplateColumns: '1fr' }}>
          
          {/* Document Upload Form */}
          <div className="card">
            <h2>Upload Reference Document (Syllabus/Notes)</h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Upload plain text files (.txt, .md) or PDF files (.pdf) to automatically split, vector-index, and feed them into the RAG system as custom knowledge.
            </p>
            <form onSubmit={handleUploadDocument}>
              <div className="form-row">
                <div className="form-group">
                  <label>Document Subject / Category</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    required 
                    value={uploadSubject}
                    onChange={(e) => setUploadSubject(e.target.value)}
                    placeholder="e.g. DBMS, Python, Biology"
                  />
                </div>
                <div className="form-group">
                  <label>Choose File (.txt, .md, .csv, .json, .pdf)</label>
                  <input 
                    id="doc-file-input"
                    type="file" 
                    accept=".txt,.md,.csv,.json,.pdf"
                    className="form-control" 
                    required 
                    onChange={(e) => setUploadFile(e.target.files[0])}
                  />
                </div>
              </div>
              <button type="submit" className="btn" style={{ width: '100%' }} disabled={uploadLoading}>
                {uploadLoading ? (
                  <>
                    <span className="spinner"></span>
                    Uploading & Indexing Chunks...
                  </>
                ) : 'Upload & Add to Knowledge Base'}
              </button>
            </form>
          </div>

          {/* Plan Generator Form */}
          <div className="card">
            <h2>Create New Study Plan</h2>
            <form onSubmit={handleGeneratePlan}>
              <div className="form-row">
                <div className="form-group">
                  <label>Student Name</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    required 
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    placeholder="Student Name"
                  />
                </div>
                <div className="form-group">
                  <label>Target Exam Date</label>
                  <input 
                    type="date" 
                    className="form-control" 
                    required 
                    value={examDate}
                    onChange={(e) => setExamDate(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Subjects (Select all that apply)</label>
                <div className="tags-container">
                  {availableSubjects.map(subj => (
                    <button
                      key={subj}
                      type="button"
                      className={`tag-select ${selectedSubjects.includes(subj) ? 'selected' : ''}`}
                      onClick={() => toggleSubject(subj)}
                    >
                      {subj}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Topics to Learn (comma-separated, e.g. SQL Joins, Class Inheritance, Two Pointer)</label>
                <input 
                  type="text" 
                  className="form-control" 
                  required 
                  value={topicsInput}
                  onChange={(e) => setTopicsInput(e.target.value)}
                  placeholder="e.g. SQL Joins, Lists & Dictionaries, Django REST, Sliding Window"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Daily Hours to Study ({dailyHours} hrs)</label>
                  <input 
                    type="range" 
                    min="1" 
                    max="12" 
                    className="form-control" 
                    value={dailyHours}
                    onChange={(e) => setDailyHours(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Study Duration (Days)</label>
                  <input 
                    type="number" 
                    min="1" 
                    max="30" 
                    className="form-control" 
                    value={durationDays}
                    onChange={(e) => setDurationDays(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Knowledge Level</label>
                  <select 
                    className="form-control" 
                    value={knowledgeLevel}
                    onChange={(e) => setKnowledgeLevel(e.target.value)}
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Preferred Study Session</label>
                  <select 
                    className="form-control" 
                    value={preferredSession}
                    onChange={(e) => setPreferredSession(e.target.value)}
                  >
                    <option value="Morning">Morning</option>
                    <option value="Afternoon">Afternoon</option>
                    <option value="Evening">Evening</option>
                    <option value="Flexible">Flexible</option>
                  </select>
                </div>
              </div>

              <button type="submit" className="btn" style={{ width: '100%', marginTop: '0.5rem' }} disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Retrieving RAG Data & Generating Plan...
                  </>
                ) : 'Generate Personalized Study Plan'}
              </button>
            </form>
          </div>

          {/* Generated Plan Output & Interactive Checklist */}
          {generatedPlan && (
            <div className="card">
              <h2>Your Study Schedule & Progress</h2>
              
              {/* Progress Tracker */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', fontWeight: 500 }}>
                  <span>Plan Completion Status</span>
                  <span>{calculateProgress()}% Completed ({completedDays.length} of {durationDays} days)</span>
                </div>
                <div className="progress-container">
                  <div className="progress-bar" style={{ width: `${calculateProgress()}%` }}></div>
                </div>
              </div>

              {/* Checklist Grid */}
              <div style={{ marginBottom: '2rem' }}>
                <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Check off completed days:</h4>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {Array.from({ length: durationDays }, (_, i) => i + 1).map(dayNum => (
                    <label 
                      key={dayNum} 
                      className={`tag-select ${completedDays.includes(dayNum) ? 'selected' : ''}`}
                      style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer' }}
                    >
                      <input 
                        type="checkbox" 
                        checked={completedDays.includes(dayNum)}
                        onChange={() => toggleDayCompletion(dayNum)}
                        style={{ cursor: 'pointer' }}
                      />
                      Day {dayNum}
                    </label>
                  ))}
                </div>
              </div>

              {/* Renders generated plan content */}
              <div>
                <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                  Generated Study Plan Details:
                </h3>
                <div 
                  style={{ 
                    whiteSpace: 'pre-wrap', 
                    fontSize: '0.95rem', 
                    backgroundColor: 'rgba(0,0,0,0.02)', 
                    padding: '1rem', 
                    borderRadius: '6px', 
                    border: '1px solid var(--border-color)',
                    maxHeight: '600px',
                    overflowY: 'auto'
                  }}
                >
                  {generatedPlan}
                </div>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}

export default App;
