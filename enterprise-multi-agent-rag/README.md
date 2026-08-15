# Enterprise Multi-Agent RAG Platform

**EnterpriseRAG** is a full-stack, multi-user document intelligence platform built with FastAPI, React, PostgreSQL/pgvector, Elasticsearch, Redis/Celery, Sentence Transformers, LangChain-compatible components, and LangGraph orchestration.

> Live Demo: `[DEPLOYED FRONTEND URL]`  
> Backend API: `[DEPLOYED BACKEND URL]`  
> API Docs: `[DEPLOYED BACKEND URL]/docs`  
> GitHub: `[REPOSITORY URL]`

Do not replace these placeholders until real URLs exist.

## Problem statement
Enterprise teams need grounded answers across private documents without leaking data between users. EnterpriseRAG combines semantic retrieval, BM25 keyword retrieval, reciprocal-rank fusion, reranking, source-aware answering, and a verification pass while enforcing ownership at the database and search layers.

## Features
- Registration/login with Argon2 password hashing and JWT access tokens
- USER and ADMIN roles with owner-scoped authorization
- PDF, DOCX, TXT, CSV ingestion and validation
- Asynchronous Celery processing with Redis
- Page-preserving PDF extraction using PyMuPDF
- Configurable chunking and Sentence Transformer embeddings
- PostgreSQL + pgvector semantic search
- Elasticsearch BM25 keyword search and metadata filters
- Hybrid reciprocal-rank fusion + cross-encoder reranking
- LangGraph router, retrieval, answer, comparison, and verification workflow with retry limit
- Conversation history and real source citations
- Admin statistics endpoint/dashboard
- Docker Compose, Alembic migrations, tests, GitHub Actions
- Local Ollama plus production OpenAI-compatible LLM abstraction

## Demo questions
- What is the annual leave policy?
- How many sick leave days are available?
- What is the travel reimbursement limit?
- Compare the 2025 and 2026 employee policies.
- What is the approval process?
- Which document contains the reimbursement policy?

## Project structure
```text
enterprise-multi-agent-rag/
├── backend/                 FastAPI, SQLAlchemy, LangGraph, Celery, tests
├── frontend/                React + TypeScript + Tailwind
├── sample_documents/        Safe synthetic demo documents, including PDF
├── docs/                    Architecture and deployment notes
├── scripts/                 Admin bootstrap helper
├── .github/workflows/       CI
├── docker-compose.yml
├── .env.example
└── README.md
```

## Windows 11 local setup (recommended: Docker for infrastructure, local Ollama)
### 1. Install prerequisites
Install Git, Docker Desktop, Python 3.12+, Node.js 22+, and Ollama. Verify in PowerShell:
```powershell
python --version
node --version
git --version
docker --version
ollama --version
```

### 2. Extract and enter the project
```powershell
cd enterprise-multi-agent-rag
Copy-Item .env.example .env
```
Change `JWT_SECRET` in `.env` to a long random value.

### 3. Pull the local LLM
```powershell
ollama pull llama3.2:3b
ollama list
```
Ollama normally listens on `http://localhost:11434`. Docker services use `host.docker.internal` from the provided `.env.example`.

### 4. Start the complete stack
```powershell
docker compose up --build
```
Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000`  
Swagger: `http://localhost:8000/docs`  
Health: `http://localhost:8000/api/health`

The first embedding/reranker run downloads public model weights. This can be large and can take time depending on your connection.

## Alternative developer mode
Start only infrastructure:
```powershell
docker compose up -d postgres redis elasticsearch
```
Create backend environment:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg://enterpriserag:enterpriserag@localhost:5432/enterpriserag"
$env:REDIS_URL="redis://localhost:6379/0"
$env:ELASTICSEARCH_URL="http://localhost:9200"
$env:OLLAMA_BASE_URL="http://localhost:11434"
alembic upgrade head
uvicorn app.main:app --reload
```
In another PowerShell:
```powershell
cd enterprise-multi-agent-rag\backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="postgresql+psycopg://enterpriserag:enterpriserag@localhost:5432/enterpriserag"
$env:REDIS_URL="redis://localhost:6379/0"
$env:ELASTICSEARCH_URL="http://localhost:9200"
celery -A app.workers.celery_app:celery worker --loglevel=INFO --pool=solo
```
Frontend:
```powershell
cd enterprise-multi-agent-rag\frontend
npm install
$env:VITE_API_URL="http://localhost:8000/api"
npm run dev
```

## Testing
Backend:
```powershell
cd backend
pytest -q
ruff check app tests
```
Frontend build validation:
```powershell
cd frontend
npm install
npm run build
```
End-to-end manual verification:
- [ ] Website opens
- [ ] Register works
- [ ] Login works
- [ ] Dashboard works
- [ ] Upload works
- [ ] Document changes from UPLOADED/PROCESSING to COMPLETED
- [ ] Chat returns a grounded answer
- [ ] Citation cards show actual filename/page/chunk IDs
- [ ] Conversation history works
- [ ] Logout works
- [ ] A normal user cannot access another user's documents/conversations
- [ ] Admin endpoint works only for ADMIN
- [ ] `/api/health` responds
- [ ] No real secrets are committed

## Create an admin user
After migrations, set environment variables and run:
```powershell
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="replace-with-a-strong-password"
python scripts\create_admin.py
```

## Environment variables
| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Celery broker/result backend |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `JWT_SECRET` | JWT signing secret |
| `JWT_ALGORITHM` | JWT algorithm, default HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token TTL |
| `OLLAMA_BASE_URL` | Local Ollama endpoint |
| `LLM_PROVIDER` | `ollama` or `openai-compatible` |
| `LLM_MODEL` | Model identifier |
| `OPENAI_COMPATIBLE_BASE_URL` | Production-compatible chat API base URL |
| `OPENAI_COMPATIBLE_API_KEY` | Backend-only provider key |
| `EMBEDDING_MODEL` | Sentence Transformer model |
| `EMBEDDING_DIMENSION` | Must match pgvector column dimension |
| `RERANKER_MODEL` | Cross-encoder model |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Chunking controls |
| `TOP_K` | Context chunks after reranking |
| `RETRIEVAL_CANDIDATES` | Candidates before reranking |
| `MAX_UPLOAD_SIZE` | Bytes accepted per upload |
| `UPLOAD_DIR` | Local/container upload directory |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `FRONTEND_URL` | Public frontend URL |
| `VITE_API_URL` | Public frontend API base URL |

## API
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/search?q=...`
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`
- `GET /api/documents/{id}/status`
- `POST /api/chat`
- `GET /api/conversations`
- `GET /api/conversations/{id}`
- `DELETE /api/conversations/{id}`
- `GET /api/admin/stats`
- `GET /api/admin/users`
- `GET /api/admin/documents`
- `DELETE /api/admin/documents/{id}`
- `GET /api/health`

## Push to GitHub
Create an empty GitHub repository first, then in PowerShell:
```powershell
cd enterprise-multi-agent-rag
git init
git add .
git commit -m "Initial commit: Enterprise Multi-Agent RAG Platform"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```
Replace only `YOUR_GITHUB_REPOSITORY_URL` with the URL of the repository you created.

## Production deployment
See `docs/DEPLOYMENT.md`. GitHub Pages alone cannot run this FastAPI/PostgreSQL/Redis/Elasticsearch/Celery stack. The frontend may be static-hosted; the backend and stateful dependencies require suitable services.

## Security notes
This repository contains no real secrets. For production add rate limiting, malware scanning, object storage, centralized audit logs, secret rotation, backups, TLS-only connectivity, and ideally an enterprise identity provider. The included JWT flow is suitable for demonstrating authorization architecture, not a substitute for a full corporate IAM deployment.

## Common errors
| Problem | Likely cause | Solution |
|---|---|---|
| Document stuck UPLOADED | Worker not running / Redis unreachable | Check `docker compose logs worker redis` |
| FAILED with model error | Model download unavailable or insufficient RAM | Verify internet/model cache; use smaller models |
| No keyword hits | Elasticsearch unavailable/index missing | Check `http://localhost:9200` and worker logs |
| Ollama connection error | Ollama not running or wrong URL | Run `ollama list`; verify `OLLAMA_BASE_URL` |
| pgvector error | Extension/migration not applied | Run `alembic upgrade head` |
| 401 | Missing/expired token | Login again |
| 403 admin | User role is USER | Bootstrap admin using `scripts/create_admin.py` |
| Browser CORS error | Frontend URL absent from `CORS_ORIGINS` | Add exact frontend origin and restart backend |

## Limitations
- Local filesystem storage is used for demo simplicity; production should use object storage.
- Cross-encoder and embedding models require memory and initial downloads.
- The verification agent is model-based, not a formal proof of factual correctness.
- Production Elasticsearch and hosted LLM services may have usage charges.

## Resume description
**Enterprise Multi-Agent RAG Platform** - Built a secure multi-user document intelligence platform with FastAPI, React, LangGraph, pgvector, Elasticsearch BM25, hybrid retrieval, cross-encoder reranking, Celery background ingestion, JWT/RBAC, and source-grounded conversational answers.

Resume bullets:
- Designed a multi-agent RAG workflow using LangGraph with routing, retrieval, comparison, answer generation, verification, and bounded retry logic.
- Implemented hybrid retrieval by combining pgvector semantic search and Elasticsearch BM25 with reciprocal-rank fusion and cross-encoder reranking.
- Built asynchronous PDF/DOCX/TXT/CSV ingestion using FastAPI, Celery, Redis, Sentence Transformers, PostgreSQL, and page-aware source citations.
- Developed a React/TypeScript SaaS interface, containerized services with Docker Compose, database migrations with Alembic, automated tests, and GitHub Actions CI.

Technology stack: Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, pgvector, Elasticsearch, Redis, Celery, LangChain, LangGraph, Sentence Transformers, Ollama/OpenAI-compatible LLMs, React 19, TypeScript, Vite, Tailwind, Docker, GitHub Actions.

GitHub: `[REPOSITORY URL]`  
Live Demo: `[DEPLOYED FRONTEND URL]`

## Interview preparation
1. **RAG** - What? Retrieval-augmented generation grounds LLM answers in external evidence. Why here? To answer private document questions with citations. Where? `app/rag/pipeline.py` and the agent graph. Interview: *How do you reduce hallucinations?* Short answer: owner-filtered retrieval, hybrid ranking, evidence-only prompting, citations, and verification.
2. **pgvector** - What? PostgreSQL vector extension. Why? Keeps embeddings close to relational ownership metadata. Where? `DocumentChunk.embedding`. Interview: *How is tenant isolation enforced?* Short answer: semantic SQL always includes `owner_id == authenticated user.id`.
3. **Elasticsearch/BM25** - What? Lexical relevance search. Why? Handles exact names, codes, and wording that embeddings can miss. Where? `HybridSearchService.keyword`. Interview: *Why hybrid search?* Short answer: semantic and lexical methods have complementary failure modes.
4. **Reranking** - What? A cross-encoder scores query-document pairs jointly. Why? Improves precision before context reaches the LLM. Where? `services/reranker.py`. Interview: *Why not rerank every chunk?* Short answer: retrieve candidates cheaply first, then apply expensive reranking to a small set.
5. **LangGraph** - What? Stateful agent/workflow orchestration. Why? Explicit conditional routing and bounded verification retry. Where? `agents/graph.py`. Interview: *How do you prevent loops?* Short answer: state tracks retries and terminates after the configured bounded retry path.
6. **Celery/Redis** - What? Distributed task processing and broker. Why? Upload requests should return quickly while parsing/embedding/indexing runs asynchronously. Where? `workers/tasks.py`. Interview: *How are failures represented?* Short answer: exceptions set document status to FAILED and store a user-facing error.
7. **JWT/RBAC** - What? Signed access token + role checks. Why? Protect APIs and distinguish USER/ADMIN. Where? `core/security.py`, `api/deps.py`. Interview: *Is role in the token enough?* Short answer: no; the server reloads the user from the DB and authorization also scopes data by user ID.
8. **FastAPI** - What? Typed ASGI API framework. Why? Validation, OpenAPI, async endpoints. Where? `app/main.py` and `api/*`. Interview: *Where is async useful?* Short answer: network-bound LLM requests and uploads; CPU-heavy model work belongs in workers.
9. **SQLAlchemy/Alembic** - What? ORM and migrations. Why? Manage relationships, constraints, schema evolution. Where? models and `alembic/`. Interview: *Why migrations instead of create_all?* Short answer: migrations make schema changes reviewable and repeatable across environments.
10. **React/TypeScript** - What? Typed SPA UI. Why? Professional recruiter-facing workflow for upload, processing, chat, citations, and history. Where? `frontend/src/App.tsx`. Interview: *How is auth persisted?* Short answer: demo uses localStorage bearer tokens; production should prefer hardened token/cookie patterns depending on threat model.

## Future improvements
Object storage and antivirus scanning, SSO/OIDC, streaming chat, websocket job progress, per-tenant encryption keys, document ACL sharing, OpenTelemetry, richer RAG evaluation datasets, OCR for scanned PDFs, query expansion, learned fusion, and Kubernetes/Terraform deployment modules.
