// Role Configuration
const ROLES = {
  manager: {
    email: "verify_mgr@acme.com",
    password: "strong_password_123"
  },
  representative: {
    email: "verify_rep@acme.com",
    password: "strong_password_123"
  }
};

let jwtToken = localStorage.getItem("jwt_token") || "";
let activeWorkflows = JSON.parse(localStorage.getItem("active_workflows")) || [];
let currentEmail = localStorage.getItem("user_email") || "";
let authMode = "login";

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  // Initialize Auth views
  updateAuthView();
  
  // Resume polling for existing active workflows if logged in
  if (jwtToken) {
    activeWorkflows.forEach(runId => {
      startWorkflowPolling(runId);
    });
  }
});

// Update display based on auth state
function updateAuthView() {
  const authContainer = document.getElementById("auth-container");
  const appWorkspace = document.getElementById("app-workspace");
  const activeEmailBadge = document.getElementById("active-user-email");
  
  if (jwtToken) {
    if (authContainer) authContainer.style.display = "none";
    if (appWorkspace) appWorkspace.style.display = "block";
    if (activeEmailBadge) activeEmailBadge.innerText = currentEmail || "Logged In";
    refreshDashboard();
  } else {
    if (authContainer) authContainer.style.display = "flex";
    if (appWorkspace) appWorkspace.style.display = "none";
  }
}

// Toggle Auth Mode
function toggleAuthTab(mode) {
  authMode = mode;
  const loginTab = document.getElementById("tab-login");
  const registerTab = document.getElementById("tab-register");
  const roleGroup = document.getElementById("register-role-group");
  const submitBtn = document.getElementById("auth-submit-btn");
  
  if (mode === "login") {
    loginTab.classList.add("active");
    registerTab.classList.remove("active");
    if (roleGroup) roleGroup.style.display = "none";
    if (submitBtn) submitBtn.innerText = "Sign In";
  } else {
    loginTab.classList.remove("active");
    registerTab.classList.add("active");
    if (roleGroup) roleGroup.style.display = "block";
    if (submitBtn) submitBtn.innerText = "Register Account";
  }
}

// Auth Submit Form Handler
async function handleAuthSubmit(event) {
  if (event) event.preventDefault();
  
  const emailInput = document.getElementById("auth-email");
  const passwordInput = document.getElementById("auth-password");
  const roleSelect = document.getElementById("auth-role");
  const submitBtn = document.getElementById("auth-submit-btn");
  
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  const role = roleSelect ? roleSelect.value : "representative";
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner"></span> Processing...`;
  
  try {
    if (authMode === "register") {
      // Register first
      const registerResp = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role })
      });
      
      if (!registerResp.ok) {
        const err = await registerResp.json();
        throw new Error(err.detail || "Registration failed");
      }
      
      showNotification("Registration successful! Logging in...", "success");
    }
    
    // Perform Login to get token
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);
    
    const loginResp = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params
    });
    
    if (!loginResp.ok) {
      const err = await loginResp.json();
      throw new Error(err.detail || "Incorrect email or password");
    }
    
    const data = await loginResp.json();
    jwtToken = data.access_token;
    currentEmail = email;
    
    localStorage.setItem("jwt_token", jwtToken);
    localStorage.setItem("user_email", currentEmail);
    
    showNotification("Logged in successfully!", "success");
    updateAuthView();
    
    // Clear inputs
    emailInput.value = "";
    passwordInput.value = "";
  } catch (error) {
    console.error("Auth flow failed:", error);
    showNotification(error.message || "Authentication failed.", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = authMode === "login" ? "Sign In" : "Register Account";
  }
}

// Quick Login Demo buttons
const MOCK_CREDENTIALS = {
  manager: { email: "verify_mgr@acme.com", password: "strong_password_123" },
  representative: { email: "verify_rep@acme.com", password: "strong_password_123" }
};

async function quickLogin(roleType) {
  const creds = MOCK_CREDENTIALS[roleType];
  
  // Fill the inputs visually
  document.getElementById("auth-email").value = creds.email;
  document.getElementById("auth-password").value = creds.password;
  
  // Set tab to login
  toggleAuthTab("login");
  
  // Execute login
  await handleAuthSubmit(null);
}

// Logout Action
function logout() {
  jwtToken = "";
  currentEmail = "";
  localStorage.removeItem("jwt_token");
  localStorage.removeItem("user_email");
  
  showNotification("Logged out successfully.", "info");
  updateAuthView();
}

// Wrapper for API calls with token authentication
async function apiFetch(endpoint, options = {}) {
  options.headers = {
    ...options.headers,
    "Authorization": `Bearer ${jwtToken}`
  };
  
  const response = await fetch(endpoint, options);
  
  if (response.status === 401 || response.status === 403) {
    const err = await response.json();
    showNotification(`Access Denied: ${err.detail || "You do not have permission."}`, "error");
    throw new Error("RBAC restriction");
  }
  
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Request failed");
  }
  
  return response.json();
}

// Reload Statistics and Lead Grid
async function refreshDashboard() {
  await loadLeads();
}

async function loadLeads() {
  const leadsGrid = document.getElementById("leads-grid");
  const totalLeadsBadge = document.getElementById("total-leads-badge");
  
  if (!leadsGrid) return;
  
  try {
    // We list leads using custom endpoint or database fetch
    // Since there's no dedicated list api (except lead/id), let's call our new list endpoint
    const leads = await apiFetch("/api/whatsapp/webhook", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entry: [{
          changes: [{
            value: {
              messages: [{
                from: "admin_tester",
                type: "text",
                text: { body: "list" }
              }]
            }
          }]
        }]
      })
    });
    
    // Instead of parsing list message text, let's fetch leads using a cleaner fallback.
    // In our plan we wrote that we can load leads from the DB or a query.
    // Let's implement an endpoint inside python or fetch leads manually using ID increments
    // But since we want to be robust, we will create a helper route `/api/frontend/leads` in python
    // that returns leads directly as JSON. Let's make an AJAX call to `/api/frontend/leads`
    const leadsData = await fetchLeadsList();
    
    if (totalLeadsBadge) {
      totalLeadsBadge.innerText = leadsData.length;
    }
    
    if (leadsData.length === 0) {
      leadsGrid.innerHTML = `<div class="empty-state">No leads discovered yet. Enter target criteria on the left panel to discover new leads!</div>`;
      return;
    }
    
    leadsGrid.innerHTML = leadsData.map(lead => `
      <div class="lead-card" onclick="openLeadModal(${lead.id})">
        <div class="lead-header">
          <div>
            <div class="lead-title">${escapeHtml(lead.company_name)}</div>
            <div class="lead-domain">${escapeHtml(lead.domain || "no domain")}</div>
          </div>
          <span class="badge badge-${lead.status.toLowerCase()}">${lead.status}</span>
        </div>
        <div class="lead-footer">
          <div>Industry: <span style="color:#e5e7eb">${escapeHtml(lead.industry || "Unknown")}</span></div>
          <div class="lead-score">${lead.score !== null ? lead.score + '%' : 'N/A'}</div>
        </div>
      </div>
    `).join("");
    
  } catch (error) {
    console.error("Failed to load leads:", error);
  }
}

async function fetchLeadsList() {
  // Call our custom frontend endpoint
  const response = await fetch("/api/frontend/leads", {
    headers: { "Authorization": `Bearer ${jwtToken}` }
  });
  if (!response.ok) return [];
  return response.json();
}

// Trigger Lead Discovery & Research
async function triggerLeadSearch(event) {
  event.preventDefault();
  const industryInput = document.getElementById("industry-input");
  const submitBtn = document.getElementById("search-submit-btn");
  
  const industry = industryInput.value.trim();
  if (!industry) return;
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner"></span> Starting...`;
  
  try {
    const result = await apiFetch("/api/lead-search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_criteria: { industry } })
    });
    
    const runId = result.workflow_run_id;
    showNotification(`Workflow triggered! Run ID: ${runId.substring(0,8)}...`, "success");
    
    // Add to active workflows
    activeWorkflows.push(runId);
    localStorage.setItem("active_workflows", JSON.stringify(activeWorkflows));
    
    // Render workflow item
    addWorkflowToSidebar(runId, industry);
    
    // Start polling
    startWorkflowPolling(runId);
    
    industryInput.value = "";
  } catch (error) {
    console.error("Failed to start workflow:", error);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "Start Discovery Workflow";
  }
}

function addWorkflowToSidebar(runId, industry) {
  const container = document.getElementById("workflow-list-container");
  if (!container) return;
  
  const emptyState = container.querySelector(".empty-state");
  if (emptyState) emptyState.remove();
  
  const item = document.createElement("div");
  item.className = "workflow-item";
  item.id = `wf-${runId}`;
  item.innerHTML = `
    <div class="workflow-item-header">
      <strong>${escapeHtml(industry)}</strong>
      <span class="badge badge-discovered" id="badge-wf-${runId}">RUNNING</span>
    </div>
    <div class="workflow-id">Run ID: ${runId.substring(0, 8)}...</div>
  `;
  container.prepend(item);
}

function startWorkflowPolling(runId) {
  const interval = setInterval(async () => {
    try {
      const run = await apiFetch(`/api/workflow/${runId}`);
      
      const badge = document.getElementById(`badge-wf-${runId}`);
      if (badge) {
        badge.innerText = run.status;
        badge.className = `badge badge-${run.status.toLowerCase().replace('_', '-')}`;
      }
      
      if (run.status === "COMPLETED" || run.status === "FAILED" || run.status === "AWAITING_REVIEW") {
        clearInterval(interval);
        
        // Remove from active workflows list
        activeWorkflows = activeWorkflows.filter(id => id !== runId);
        localStorage.setItem("active_workflows", JSON.stringify(activeWorkflows));
        
        if (run.status === "COMPLETED") {
          showNotification("Workflow run completed successfully!", "success");
        } else if (run.status === "AWAITING_REVIEW") {
          showNotification("Outreach drafts generated! Awaiting manager approval.", "warning");
        } else {
          showNotification("Workflow run execution failed.", "error");
        }
        
        // Refresh Leads List
        await refreshDashboard();
      }
    } catch (error) {
      console.error(`Error polling workflow ${runId}:`, error);
      clearInterval(interval);
    }
  }, 2000);
}

// Modal Details View
let activeLeadDetails = null;

async function openLeadModal(leadId) {
  const modal = document.getElementById("details-modal");
  if (!modal) return;
  
  modal.classList.add("active");
  
  try {
    const lead = await apiFetch(`/api/lead/${leadId}`);
    activeLeadDetails = lead;
    
    // Populate firmographics
    document.getElementById("modal-lead-title").innerText = lead.company_name;
    document.getElementById("modal-lead-status").innerText = lead.status;
    document.getElementById("modal-lead-status").className = `badge badge-${lead.status.toLowerCase()}`;
    
    document.getElementById("detail-id").innerText = lead.id;
    document.getElementById("detail-company").innerText = lead.company_name;
    document.getElementById("detail-domain").innerText = lead.domain || "N/A";
    document.getElementById("detail-industry").innerText = lead.industry || "N/A";
    document.getElementById("detail-score").innerText = lead.score !== null ? `${lead.score}%` : "Not Scored";
    
    // Load report & message
    await fetchReportsAndMessages(leadId);
    
    // Set active tab to overview
    switchTab("overview");
  } catch (error) {
    console.error("Failed to load lead details:", error);
    closeLeadModal();
  }
}

async function fetchReportsAndMessages(leadId) {
  const reportContent = document.getElementById("report-content");
  const outreachContent = document.getElementById("outreach-content");
  
  reportContent.innerHTML = `<span class="spinner"></span> Loading report...`;
  outreachContent.innerHTML = `<span class="spinner"></span> Loading outreach...`;
  
  try {
    const details = await apiFetch(`/api/frontend/lead/${leadId}/details`);
    
    // Render Report
    if (details.report) {
      reportContent.innerHTML = `
        <div class="info-box" style="margin-bottom: 1.5rem">
          <div class="info-label">Company Profile</div>
          <div class="info-value" style="white-space: pre-wrap; line-height: 1.5;">${escapeHtml(details.report.profile)}</div>
        </div>
        
        <div class="grid-cols-2" style="margin-bottom: 1.5rem;">
          <div class="info-box">
            <div class="info-label">📈 Growth Signals</div>
            <div class="info-value" style="margin-top: 0.5rem;">${formatDict(details.report.growth_signals)}</div>
          </div>
          <div class="info-box">
            <div class="info-label">👥 Hiring & Talent Signals</div>
            <div class="info-value" style="margin-top: 0.5rem;">${formatDict(details.report.hiring_signals)}</div>
          </div>
        </div>

        <div class="grid-cols-2">
          <div class="info-box">
            <div class="info-label">🛠️ Technology Stack</div>
            <div class="info-value" style="margin-top: 0.5rem;">${formatListAsPills(details.report.tech_adoption)}</div>
          </div>
          <div class="info-box">
            <div class="info-label">⚠️ Business Risks & Concerns</div>
            <div class="info-value" style="margin-top: 0.5rem;">${formatRisks(details.report.risks)}</div>
          </div>
        </div>
      `;
    } else {
      reportContent.innerHTML = `<div class="empty-state">No research report compiled for this lead yet.</div>`;
    }
    
    // Render Outreach Message
    if (details.message) {
      outreachContent.innerHTML = `
        <div class="info-box" style="margin-bottom: 1rem">
          <div class="info-label">Sales Angle & Strategy</div>
          <div class="info-value" style="font-weight: 600; color: var(--color-accent)">${escapeHtml(details.message.sales_angle)}</div>
        </div>
        <div class="info-box" style="margin-bottom: 1rem">
          <div class="info-label">Email Subject</div>
          <div class="info-value" style="font-weight: 700">${escapeHtml(details.message.email_subject)}</div>
        </div>
        <div class="info-box" style="margin-bottom: 1rem">
          <div class="info-label">Email Body</div>
          <div class="code-snippet" style="font-family: var(--font-body)">${escapeHtml(details.message.email_body)}</div>
        </div>
        <div class="info-box">
          <div class="info-label">LinkedIn Connection Message</div>
          <div class="code-snippet" style="font-family: var(--font-body)">${escapeHtml(details.message.linkedin_message)}</div>
        </div>
      `;
    } else {
      outreachContent.innerHTML = `<div class="empty-state">No outreach campaign generated for this lead yet. Only high-scoring qualified leads trigger automatic outreach drafts.</div>`;
    }
    
  } catch (error) {
    reportContent.innerHTML = `<div class="empty-state">Error loading details.</div>`;
    outreachContent.innerHTML = `<div class="empty-state">Error loading details.</div>`;
  }
}

function closeLeadModal() {
  const modal = document.getElementById("details-modal");
  if (modal) modal.classList.remove("active");
  activeLeadDetails = null;
}

// Tab Selector inside Modal
function switchTab(tabName) {
  // Update buttons
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("onclick").includes(tabName));
  });
  
  // Update panes
  document.querySelectorAll(".tab-pane").forEach(pane => {
    pane.classList.toggle("active", pane.id === `${tabName}-tab`);
  });
}

// Notifications Helper
function showNotification(message, type = "success") {
  const container = document.getElementById("notification-container") || createNotificationContainer();
  
  const toast = document.createElement("div");
  toast.style.background = type === "success" ? "rgba(16, 185, 129, 0.95)" : type === "warning" ? "rgba(245, 158, 11, 0.95)" : "rgba(239, 68, 68, 0.95)";
  toast.style.color = "white";
  toast.style.padding = "0.75rem 1.25rem";
  toast.style.borderRadius = "8px";
  toast.style.fontSize = "0.85rem";
  toast.style.fontWeight = "600";
  toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
  toast.style.display = "flex";
  toast.style.alignItems = "center";
  toast.style.gap = "0.5rem";
  toast.style.transition = "all 0.3s ease";
  toast.style.opacity = "0";
  toast.style.transform = "translateY(20px)";
  
  toast.innerHTML = message;
  container.appendChild(toast);
  
  // Slide In
  setTimeout(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";
  }, 10);
  
  // Slide Out
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-20px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function createNotificationContainer() {
  const container = document.createElement("div");
  container.id = "notification-container";
  container.style.position = "fixed";
  container.style.bottom = "2rem";
  container.style.right = "2rem";
  container.style.display = "flex";
  container.style.flexDirection = "column";
  container.style.gap = "0.75rem";
  container.style.zIndex = "2000";
  document.body.appendChild(container);
  return container;
}

// Escape HTML Helper to prevent XSS
function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


// RAG Data Formatting Helpers
function formatDict(obj) {
  if (!obj || typeof obj !== "object") return "None";
  if (Array.isArray(obj)) {
    return `<ul style="list-style: none; padding-left: 0;">${
      obj.map(item => `<li style="margin-bottom: 0.4rem; display: flex; align-items: flex-start; gap: 0.4rem; font-size: 0.85rem;"><span style="color: var(--color-success)">✓</span> <span>${escapeHtml(item)}</span></li>`).join("")
    }</ul>`;
  }
  const entries = Object.entries(obj);
  if (entries.length === 0) return "None";
  return `<div style="display: flex; flex-direction: column; gap: 0.75rem;">${
    entries.map(([key, val]) => {
      const cleanKey = key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
      let valStr = "";
      if (Array.isArray(val)) {
        valStr = val.join(", ");
      } else if (typeof val === "object" && val !== null) {
        valStr = JSON.stringify(val);
      } else {
        valStr = String(val);
      }
      return `<div><span style="font-size: 0.7rem; font-weight: 700; color: var(--color-accent); text-transform: uppercase; letter-spacing: 0.05em; display: block;">${escapeHtml(cleanKey)}</span><span style="font-size: 0.85rem; font-weight: 500;">${escapeHtml(valStr)}</span></div>`;
    }).join("")
  }</div>`;
}

function formatListAsPills(arr) {
  if (!arr || !Array.isArray(arr) || arr.length === 0) return "None";
  return `<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">${
    arr.map(item => `<span class="badge" style="background: rgba(59, 130, 246, 0.08); color: var(--color-primary); border: 1px solid rgba(59, 130, 246, 0.2); text-transform: none; font-size: 0.75rem; border-radius: 6px; padding: 0.3rem 0.6rem;">${escapeHtml(item)}</span>`).join("")
  }</div>`;
}

function formatRisks(arr) {
  if (!arr || !Array.isArray(arr) || arr.length === 0) return "None";
  return `<ul style="list-style: none; padding-left: 0;">${
    arr.map(item => `<li style="margin-bottom: 0.5rem; display: flex; align-items: flex-start; gap: 0.5rem; font-size: 0.85rem;"><span style="color: var(--color-danger)">⚠</span> <span>${escapeHtml(item)}</span></li>`).join("")
  }</ul>`;
}


