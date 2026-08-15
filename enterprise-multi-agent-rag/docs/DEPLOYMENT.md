# Production deployment guide

EnterpriseRAG is intentionally split into stateless web services and managed stateful services.

## Recommended shape
- Frontend: static hosting/CDN (Vercel, Netlify, Cloudflare Pages, or equivalent).
- FastAPI backend + Celery worker: container platform (Render, Railway, Fly.io, Azure Container Apps, AWS ECS, Google Cloud Run for API; worker needs a continuously available process model).
- PostgreSQL: managed PostgreSQL with pgvector enabled.
- Redis: managed Redis-compatible service.
- Elasticsearch: managed Elastic Cloud or another compatible Elasticsearch deployment. A real production Elasticsearch tier is often not permanently free.
- LLM: an OpenAI-compatible API configured with `LLM_PROVIDER=openai-compatible`, or a separately hosted Ollama endpoint with adequate CPU/GPU resources.

Do not place secrets in frontend environment variables. `VITE_API_URL` is public by design; provider API keys are backend-only.

## Deployment sequence
1. Push the repository to GitHub.
2. Provision PostgreSQL and enable `CREATE EXTENSION vector`.
3. Provision Redis and Elasticsearch.
4. Deploy backend using `backend/Dockerfile` and set all backend environment variables.
5. Run `alembic upgrade head` as a release command.
6. Deploy a second service using `backend/Dockerfile.worker` for Celery.
7. Verify `GET /api/health`.
8. Deploy frontend with build arg/environment `VITE_API_URL=https://YOUR-BACKEND/api`.
9. Set backend `CORS_ORIGINS=https://YOUR-FRONTEND` and redeploy.
10. Register, upload a sample PDF, wait for COMPLETED, ask a question, verify citations and history.
11. Replace README Live Demo placeholders only after real URLs exist.

## Production hardening
Use long random JWT secrets, HTTPS only, private networking where supported, object storage for uploaded documents, malware scanning, rate limiting, centralized logs, backups, secret rotation, and an external identity provider for higher-assurance enterprise deployments.
