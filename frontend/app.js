// frontend/app.js
document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = "http://localhost:8000";

  let sessionId = null;
  let currentQuestion = "";
  let authToken = localStorage.getItem("token") || null;

  // Elements
  const uploadBtn = document.getElementById("uploadBtn");
  const nextQuestionBtn = document.getElementById("nextQuestionBtn");
  const submitAnswerBtn = document.getElementById("submitAnswerBtn");
  const refreshSummaryBtn = document.getElementById("refreshSummaryBtn");

  const uploadStatus = document.getElementById("uploadStatus");
  const skillsList = document.getElementById("skillsList");
  const questionBoxContainer = document.getElementById("questionBoxContainer");
  const questionText = document.getElementById("questionText");
  const questionStatusIndicator = document.getElementById("questionStatusIndicator");
  const answerSection = document.getElementById("answerSection");
  const answerText = document.getElementById("answerText");
  const feedbackBox = document.getElementById("feedbackBox");
  const summaryBox = document.getElementById("summaryBox");

  // Sections/Cards
  const cardInterview = document.getElementById("cardInterview");
  const cardSummary = document.getElementById("cardSummary");
  const authOverlay = document.getElementById("authOverlay");
  const mainApp = document.getElementById("mainApp");
  const userNameDisplay = document.getElementById("userNameDisplay");
  const logoutBtn = document.getElementById("logoutBtn");

  // Auth elements
  const tabLogin = document.getElementById("tabLogin");
  const tabRegister = document.getElementById("tabRegister");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const authStatus = document.getElementById("authStatus");

  // ------------------------------------------------------------------
  // Auth Logic
  // ------------------------------------------------------------------

  const checkAuth = async () => {
    if (!authToken) {
      showAuth(true);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (!res.ok) throw new Error("Session expired");
      const user = await res.json();
      userNameDisplay.textContent = user.username;
      showAuth(false);
    } catch (err) {
      logout();
    }
  };

  const showAuth = (show) => {
    authOverlay.style.display = show ? "flex" : "none";
    mainApp.style.display = show ? "none" : "block";
  };

  const logout = () => {
    localStorage.removeItem("token");
    authToken = null;
    showAuth(true);
  };

  logoutBtn.onclick = logout;

  // Tab switching
  tabLogin.onclick = () => {
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    loginForm.style.display = "block";
    registerForm.style.display = "none";
  };

  tabRegister.onclick = () => {
    tabRegister.classList.add("active");
    tabLogin.classList.remove("active");
    registerForm.style.display = "block";
    loginForm.style.display = "none";
  };

  // Login handler
  document.getElementById("loginBtn").onclick = async () => {
    const user = document.getElementById("loginUsername").value;
    const pass = document.getElementById("loginPassword").value;
    authStatus.textContent = "Signing in...";
    
    try {
      const formData = new URLSearchParams();
      formData.append("username", user);
      formData.append("password", pass);

      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");

      authToken = data.access_token;
      localStorage.setItem("token", authToken);
      await checkAuth();
    } catch (err) {
      console.error("Login error:", err);
      authStatus.innerHTML = `<span style="color: var(--error);">Error: ${err.message}</span>`;
    }
  };

  // Register handler
  document.getElementById("registerBtn").onclick = async () => {
    const user = document.getElementById("regUsername").value;
    const email = document.getElementById("regEmail").value;
    const pass = document.getElementById("regPassword").value;
    
    if (!user || !email || !pass) {
        authStatus.innerHTML = `<span style="color: var(--error);">All fields are required</span>`;
        return;
    }

    authStatus.textContent = "Creating account...";

    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, email, password: pass })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");

      authStatus.innerHTML = `<span style="color: var(--success);">Account created! Logging in...</span>`;
      
      // Auto-login
      document.getElementById("loginUsername").value = user;
      document.getElementById("loginPassword").value = pass;
      document.getElementById("loginBtn").click();
    } catch (err) {
      console.error("Registration error:", err);
      authStatus.innerHTML = `<span style="color: var(--error);">${err.message}</span>`;
    }
  };

  // Helper for authenticated requests
  const fetchWithAuth = async (url, options = {}) => {
    if (!options.headers) options.headers = {};
    options.headers["Authorization"] = `Bearer ${authToken}`;
    
    const res = await fetch(url, options);
    if (res.status === 401) {
      logout();
      throw new Error("Authentication required");
    }
    return res;
  };

  checkAuth();

  // Helper functions
  const setLoading = (btn, isLoading, text) => {
    const btnText = btn.querySelector('.btn-text');
    if (isLoading) {
      btn.disabled = true;
      btn.dataset.originalText = btnText.textContent;
      const spinner = `<svg class="spinner" viewBox="0 0 50 50"><circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle></svg>`;
      btnText.innerHTML = `${spinner} ${text}`;
    } else {
      btn.disabled = false;
      btnText.textContent = btn.dataset.originalText || text;
    }
  };

  const typeWriterEffect = async (text, element) => {
    element.innerHTML = "";
    const speed = 20; // ms per char
    
    // Smooth fade in
    element.style.opacity = 0;
    setTimeout(() => {
        element.style.opacity = 1;
        element.style.transition = 'opacity 0.5s ease';
    }, 50);

    for (let i = 0; i < text.length; i++) {
      element.innerHTML += text.charAt(i);
      await new Promise(r => setTimeout(r, speed));
    }
  };

  // ------------------------------------------------------------------
  // Upload Resume
  // ------------------------------------------------------------------
  uploadBtn.onclick = async () => {
    try {
      const fileInput = document.getElementById("resumeFile");
      if (!fileInput.files || !fileInput.files[0]) {
        throw new Error("Please select a resume file.");
      }

      setLoading(uploadBtn, true, "Analyzing Document...");
      uploadStatus.textContent = "";
      feedbackBox.innerHTML = "";
      skillsList.innerHTML = "";
      
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      const res = await fetchWithAuth(`${API_BASE}/upload_resume`, {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!res.ok || !data.session_id) {
        throw new Error(data.error || "Resume upload failed.");
      }

      sessionId = data.session_id;

      uploadStatus.innerHTML = `
        <span style="color: var(--success);">✓ Context initialized</span><br>
        <span style="font-size: 0.85em; color: var(--text-secondary);">Analyzing: ${data.filename}</span>
      `;
      
      // Render skill pills
      if (data.skills && data.skills.length > 0) {
        data.skills.forEach(skill => {
            const pill = document.createElement("div");
            pill.className = "skill-pill";
            pill.textContent = skill;
            skillsList.appendChild(pill);
        });
      }

      // Unlock next stage
      cardInterview.classList.remove("disabled");
      cardSummary.classList.remove("disabled");

    } catch (err) {
      uploadStatus.innerHTML = `<span style="color: var(--error);">✗ ${err.message}</span>`;
      console.error(err);
    } finally {
      setLoading(uploadBtn, false, "Extract & Initialize Context");
    }
  };

  // ------------------------------------------------------------------
  // Get Next Question
  // ------------------------------------------------------------------
  nextQuestionBtn.onclick = async () => {
    try {
      if (!sessionId) {
        alert("Please initialize context first.");
        return;
      }

      setLoading(nextQuestionBtn, true, "Generating AI Question...");
      questionBoxContainer.style.display = "block";
      answerSection.style.display = "none";
      feedbackBox.innerHTML = "";
      questionText.innerHTML = `<span class="loading">Generating optimized question...</span>`;
      questionStatusIndicator.innerHTML = `<span style="font-size: 0.8em; padding: 2px 8px; border-radius: 12px; background: rgba(0,212,255,0.2); color: var(--accent-cyan);">THINKING...</span>`;

      const res = await fetchWithAuth(`${API_BASE}/next_question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });

      const data = await res.json();

      if (!res.ok || !data.question) {
        throw new Error(data.error || "Failed to generate question.");
      }

      currentQuestion = data.question;
      questionStatusIndicator.innerHTML = "";
      await typeWriterEffect(currentQuestion, questionText);
      
      answerText.value = "";
      answerSection.style.display = "block";
      
    } catch (err) {
      questionText.innerHTML = `<span style="color: var(--error);">Error generating question: ${err.message}</span>`;
      console.error(err);
    } finally {
      setLoading(nextQuestionBtn, false, "Generate Next Question");
    }
  };

  // ------------------------------------------------------------------
  // Submit Answer
  // ------------------------------------------------------------------
  submitAnswerBtn.onclick = async () => {
    try {
      if (!sessionId || !currentQuestion) {
        alert("Please generate a question first.");
        return;
      }

      const answer = answerText.value.trim();
      if (!answer) {
        alert("Please provide a comprehensive answer.");
        return;
      }

      setLoading(submitAnswerBtn, true, "Evaluating with AI...");
      feedbackBox.innerHTML = `
        <div class="alert alert-info loading" style="text-align: center;">
          <em>Running multidimensional analysis on your response...</em>
        </div>
      `;

      const res = await fetchWithAuth(`${API_BASE}/submit_answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          question: currentQuestion,
          answer: answer
        })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Answer submission failed.");
      }

      // Nice color handling for score
      const scoreColor = data.score >= 8 ? 'var(--success)' : 
                         data.score >= 5 ? 'var(--accent-cyan)' : 
                         'var(--error)';

      let cleanFeedback = data.feedback || "No feedback provided.";
      cleanFeedback = cleanFeedback.replace(/```json/g, '').replace(/```/g, '').replace(/\\n/g, '<br>');

      feedbackBox.innerHTML = `
        <div class="alert alert-info" style="animation: slideIn 0.3s ease;">
          <div class="score-display" style="color: ${scoreColor};">${data.score}<span style="font-size: 1rem; color: var(--text-secondary);">/10</span></div>
          <p style="margin-bottom: 0;"><strong>Feedback Insight:</strong><br><span style="line-height: 1.6;">${cleanFeedback}</span></p>
        </div>
      `;
      
      // Auto-refresh summary
      refreshSummaryBtn.click();
      
    } catch (err) {
      feedbackBox.innerHTML =
        `<div class="alert alert-danger">Error: ${err.message}</div>`;
      console.error(err);
    } finally {
      setLoading(submitAnswerBtn, false, "Submit Answer");
    }
  };

  // ------------------------------------------------------------------
  // Refresh Session Summary
  // ------------------------------------------------------------------
  refreshSummaryBtn.onclick = async () => {
    try {
      if (!sessionId) return;

      setLoading(refreshSummaryBtn, true, "Fetching...");

      const res = await fetchWithAuth(
        `${API_BASE}/session_summary?session_id=${sessionId}`
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Failed to load summary.");
      }

      if (!data.answers || data.answers.length === 0) {
         summaryBox.innerHTML = `<div style="background: rgba(0, 0, 0, 0.2); padding: 1.5rem; border-radius: 12px; color: var(--text-secondary); text-align: center;">No questions answered yet.</div>`;
         return;
      }

      let averageScoreColor = data.average_score >= 8 ? 'var(--success)' : 
                              data.average_score >= 5 ? 'var(--accent-cyan)' : 'var(--error)';

      let htmlContent = `<div style="margin-bottom: 2rem; text-align: center;">
          <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">Average Score</h3>
          <div style="font-size: 3rem; font-weight: 700; color: ${averageScoreColor}; line-height: 1;">
              ${data.average_score ? data.average_score.toFixed(1) : '0.0'}<span style="font-size: 1.5rem; color: var(--text-secondary);">/10</span>
          </div>
      </div>`;

      htmlContent += `<div style="display: flex; flex-direction: column; gap: 1.5rem;">`;

      data.answers.forEach((ans, index) => {
         const scoreColor = ans.score >= 8 ? 'var(--success)' : ans.score >= 5 ? 'var(--accent-cyan)' : 'var(--error)';
         
         // Clean potential raw json/markdown leftovers
         let cleanFeedback = ans.feedback || "No feedback provided.";
         cleanFeedback = cleanFeedback.replace(/```json/g, '').replace(/```/g, '').replace(/\\n/g, '<br>');

         htmlContent += `
           <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; border-left: 4px solid ${scoreColor};">
             <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; gap: 1rem;">
               <div style="font-weight: 600; color: var(--text-primary); font-size: 1.1rem;">
                 Q${index + 1}: ${ans.question}
               </div>
               <div style="background: rgba(0,0,0,0.3); padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 700; color: ${scoreColor}; white-space: nowrap;">
                 Score: ${ans.score}/10
               </div>
             </div>
             
             <div style="margin-bottom: 1rem;">
               <span style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); display: block; margin-bottom: 0.3rem;">Your Answer:</span>
               <div style="color: var(--text-primary); font-style: italic; background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 8px;">
                 "${ans.answer}"
               </div>
             </div>

             <div>
               <span style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); display: block; margin-bottom: 0.3rem;">AI Feedback:</span>
               <div style="color: var(--text-primary); line-height: 1.5;">
                 ${cleanFeedback}
               </div>
             </div>
           </div>
         `;
      });

      htmlContent += `</div>`;
      summaryBox.innerHTML = htmlContent;

    } catch (err) {
      summaryBox.innerHTML = `<span style="color: var(--error);">Error formatting summary: ${err.message}</span>`;
      console.error(err);
    } finally {
        setLoading(refreshSummaryBtn, false, "Fetch Latest Results");
    }
  };
});