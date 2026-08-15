# Architecture

```text
React -> FastAPI -> JWT/RBAC
                 -> LangGraph Router
                    -> Hybrid Retrieval
                       -> pgvector semantic search
                       -> Elasticsearch BM25
                       -> reciprocal-rank fusion
                       -> cross-encoder reranker
                    -> Answer Agent
                    -> Verification Agent
                 -> PostgreSQL conversation history

Upload -> FastAPI validation -> durable metadata -> Celery/Redis -> Parser -> Chunker
       -> SentenceTransformer embeddings -> PostgreSQL/pgvector + Elasticsearch -> COMPLETED
```

Security boundary: every non-admin document query, chunk lookup, conversation read, and delete operation is scoped to the authenticated `user.id`.
