# Project Overview: Enterprise Sales Intelligence Platform

This document describes the structure, components, and files implemented in the **Enterprise Multi-Agent Sales Intelligence Platform** repository.

---

## 📂 Directory Structure & Key Files

The codebase is split into the docker orchestrator configuration at the root and the Python FastAPI code inside the `backend/` directory:

```
sales_intelligence/
├── docker-compose.yml           # Multi-service container definitions
├── backend/
│   ├── docker/
│   │   └── Dockerfile           # Backend container build script
│   ├── requirements.txt         # Python dependencies
│   ├── alembic.ini              # DB migrations configuration
│   ├── alembic/                 # Alembic version schemas
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint
│   │   ├── core/
│   │   │   ├── config.py        # Environment settings & Pydantic validation
│   │   │   ├── security.py      # BCrypt password hashing & JWT generation
│   │   │   └── exceptions.py    # Global exception definitions
│   │   ├── db/
│   │   │   ├── session.py       # Asynchronous DB connection session makers
│   │   │   └── models.py        # SQLAlchemy 2.0 PostgreSQL tables
│   │   ├── repositories/        # SQL DB query wrappers
│   │   │   ├── leads.py
│   │   │   ├── user.py
│   │   │   └── workflows.py
│   │   ├── services/
│   │   │   ├── llm_service.py   # LLM Factory (Gemini, OpenAI, AgentRouter)
│   │   │   ├── milvus_service.py# Vector database interfaces
│   │   │   └── workflow_service.py # Background workflow executor
│   │   ├── agents/              # CrewAI role configurations
│   │   │   ├── research.py      # Company Analyst (uses Milvus RAG)
│   │   │   ├── qualify.py       # Qualification Analyst
│   │   │   └── outreach.py      # Outreach copywriter
│   │   ├── graph/
│   │   │   ├── state.py         # LangGraph workflow state schema
│   │   │   └── workflow.py      # LangGraph state machine node execution
│   │   ├── api/                 # Endpoint controllers
│   │   │   ├── auth.py          # RBAC dependency guards
│   │   │   ├── routes.py        # Sales REST APIs
│   │   │   ├── whatsapp.py      # Meta WhatsApp webhook router
│   │   │   └── frontend.py      # Web UI template router
│   │   ├── templates/
│   │   │   └── index.html       # HTML Jinja2 dashboard page
│   │   └── static/
│   │       ├── styles.css       # Premium CSS variables & styling rules
│   │       └── app.js           # Client AJAX & UI logic
│   └── scripts/
│       ├── seed_playbooks.py    # Milvus vector database seeder
│       ├── verify_live_api.py   # Live API HTTP verification script
│       └── verify_whatsapp_webhook.py # Simulated WhatsApp integration test
```

---

## 🛠️ Components Built

### 1. Multi-Agent LangGraph State Machine
We compiled a state transition graph managing the sales pipeline. It runs the following steps sequentially in the background:
* **Discover**: Finds target prospects based on search criteria.
* **Research**: Analyzes companies using web search and Milvus RAG retrievals.
* **Qualify**: Scores leads against ICP criteria.
* **Outreach**: Generates personalized copy for high-scoring leads.
* **Human Review**: Awaits manager approval before completing the flow.

### 2. Relational Database Layer
* Implemented **SQLAlchemy 2.0** tables for users, leads, research reports, outreach drafts, workflow logs, and workflow run histories.
* Configured **Alembic** migrations to automatically apply database schema updates.

### 3. Vector Database Layer (RAG)
* Configured **Milvus Standalone** to store and search sales playbook materials (value pitches, objection-handling templates) using the `all-MiniLM-L6-v2` embedding model.

### 4. Interactive Web Dashboard
* Designed a responsive dark-mode interface built on Jinja2 templates, vanilla CSS, and vanilla JS, providing lead discovery buttons, active workflow lists, and expandable lead detailed modals.

### 5. Meta WhatsApp Bot Integration
* Implemented a WhatsApp Cloud API webhook endpoint that verifies subscription tokens and parses text commands (`help`, `list`, `search <industry>`, `status <id>`, `lead <id>`) to trigger background tasks and reply to the user's phone.
