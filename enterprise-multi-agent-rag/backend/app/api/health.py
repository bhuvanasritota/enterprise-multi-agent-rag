from fastapi import APIRouter
from elasticsearch import Elasticsearch
from redis import Redis
from app.core.config import settings
from app.core.database import ping_db
router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    db_ok = ping_db()
    try: redis_ok = bool(Redis.from_url(settings.redis_url, socket_timeout=2).ping())
    except Exception: redis_ok = False
    try: es_ok = bool(Elasticsearch(settings.elasticsearch_url, request_timeout=2).ping())
    except Exception: es_ok = False
    overall = "ok" if db_ok and redis_ok and es_ok else "degraded"
    return {"status": overall, "database": db_ok, "redis": redis_ok, "elasticsearch": es_ok}
