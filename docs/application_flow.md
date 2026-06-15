# Application Flow & Data Pipelines

This document maps the three core operational flows within the platform: the multi-agent execution pipeline, the web interface loop, and the WhatsApp bot command parsing sequence.

---

## 1. Multi-Agent Lead Processing Pipeline (LangGraph & CrewAI)

When a lead discovery run is initiated (via the API, Web UI, or WhatsApp), the background workflow executes the following sequence:

```
[Start]
   │
   ▼
1. discover_companies_node
   ├── Reads industry focus (e.g. "Robotics")
   ├── Simulates prospect discovery
   └── Inserts new Lead records into PostgreSQL (status = "discovered")
   │
   ▼
2. research_companies_node
   ├── Triggers CrewAI Company Intelligence Analyst Agent
   ├── Queries Google / News tools for company profile & growth signals
   ├── Queries Milvus Vector Database for matching playbooks (RAG)
   └── Saves ResearchReport record in PostgreSQL (status = "researched")
   │
   ▼
3. qualify_companies_node
   ├── Triggers CrewAI Qualification Agent
   ├── Compares research details against user-defined target criteria
   └── Computes ICP match score & updates PostgreSQL (status = "qualified"/"disqualified")
   │
   ▼
4. generate_outreach_node
   ├── Filters leads with ICP score >= 70
   ├── Triggers CrewAI Copywriter Agent to draft custom emails & InMail copies
   ├── Saves OutreachMessage draft in PostgreSQL
   └── Workflow pauses & transitions to AWAITING_REVIEW status
   │
   ▼
5. human_review_node (Manager Approval)
   ├── User approves/edits message via Dashboard or API
   ├── Updates status to "outreach_generated" & marks message as "sent"
   └── Workflow run completes (status = "COMPLETED")
```

---

## 2. Jinja2 Web Dashboard Interaction Loop

The web interface behaves dynamically as a Single Page Application (SPA):

1. **Authentication Check**:
   * On load, `app.js` checks if a JWT token exists in `localStorage`.
   * If missing, it hides the dashboard and shows the secure login/registration panel.
   * Users can enter credentials or click **Quick Demo Profile** buttons (which automatically call `/api/auth/login`, store the token, and reveal the dashboard).
2. **Dashboard Rendering**:
   * `app.js` makes authenticated AJAX fetches to `/api/frontend/leads` to render the grid cards.
3. **Workflow Triggering & Polling**:
   * When a user submits an industry, the dashboard calls `POST /api/lead-search` and receives a `workflow_run_id`.
   * The sidebar immediately appends a progress card and starts polling `GET /api/workflow/{run_id}` every 2 seconds.
   * When status updates to `AWAITING_REVIEW` or `COMPLETED`, the polling clears, and the leads grid reloads.
4. **Modal inspection**:
   * Clicking a card calls `/api/frontend/lead/{id}/details` to load combined database details (firmographics, research report, and copywriting drafts) and reveals the details modal.

---

## 3. WhatsApp Webhook & Command Processor Flow

The WhatsApp integration acts as an asynchronous chat assistant:

```
[User Text Message]
       │
       ▼
1. Meta WhatsApp Cloud API
       │ (Sends HTTP POST Webhook payload)
       ▼
2. FastAPI Endpoint: POST /api/whatsapp/webhook
       │
       ▼
3. Command Parser (whatsapp.py)
       ├── "help"   ──► Returns bot command list
       ├── "list"   ──► Queries PostgreSQL for top 5 recent leads
       ├── "search" ──► Triggers background LangGraph workflow
       ├── "status" ──► Queries status of a specific workflow run ID
       ├── "lead"   ──► Retrieves firmographics of a lead ID
       └── Wildcard ──► Runs a wildcard database check on company name
       │
       ▼
4. Meta Messages API
       │ (Sends HTTP POST to https://graph.facebook.com/v25.0)
       ▼
[User receives WhatsApp Reply]
```
