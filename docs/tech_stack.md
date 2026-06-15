# Technical Stack Configuration

This document lists the databases, libraries, frameworks, and tools powering the **Enterprise Sales Intelligence Platform**.

---

## 💻 Backend Core & API Layer
* **FastAPI**: Asynchronous web framework for building highly performant REST APIs.
* **Uvicorn**: Lightning-fast ASGI web server implementation used to run the API container.
* **Pydantic v2**: Data validation and settings management using python type annotations.

---

## 🤖 Multi-Agent Orchestration & LLM Services
* **LangGraph**: State machine graph orchestration framework used to compile workflow nodes, define state transitions, and handle state persistence.
* **CrewAI**: Role-based agentic framework. We define three specialized agents (Intelligence Analyst, Qualification Analyst, Copywriter) that cooperate to research and write sales outreach scripts.
* **Google Gemini Pro / OpenAI**: Advanced Large Language Models (LLMs) used to drive reasoning and tool usage for CrewAI agents.
* **AgentRouter**: Proxy provider which wraps third-party API models (like `deepseek-r1`) as OpenAI-compatible completions.

---

## 💾 Relational Database & ORM
* **PostgreSQL (v15)**: Primary transactional database storing user credentials, leads metadata, research reports, outreach copies, and run states.
* **SQLAlchemy 2.0**: Object Relational Mapper (ORM) using modern async syntax (e.g. `select`, `scalars()`) and `asyncpg` drivers.
* **Alembic**: Database migrations management tool to version-control schema upgrades.

---

## 🔍 Vector Database & Embeddings (RAG)
* **Milvus Standalone (v2.4.0)**: Vector database storing sales playbooks and objection-handling templates.
* **Sentence-Transformers (`all-MiniLM-L6-v2`)**: Embedding model used locally inside the API container to map search queries and text chunks into 384-dimensional dense vectors.
* **MinIO & Etcd**: Docker dependencies of Milvus standalone, used for object storage and configuration consensus metadata.

---

## 🖥️ Web Frontend Layer
* **Jinja2**: HTML templating engine used to compile and serve the dashboard index file from FastAPI.
* **Vanilla CSS**: Premium dark-mode variables, layouts, scrollbars, and transition animations without bloated utility framework dependencies.
* **Vanilla JS**: Asynchronous AJAX fetching (`fetch`), local storage auth token caching, polling loops, and modal controllers.

---

## 📊 Observability & Deployment
* **LangSmith**: Real-time tracing and debugging platform. It tracks LangGraph executions, agent reasoning trees, LLM prompts, tool inputs/outputs, and costs.
* **Docker & Docker Compose**: Complete containerization structure, enabling one-click deployment of the api service alongside its databases, vector stores, and caching layers.
