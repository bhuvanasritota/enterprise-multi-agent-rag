from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "EnterpriseRAG"
    environment: str = "development"
    api_v1_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://enterpriserag:enterpriserag@localhost:5432/enterpriserag"
    redis_url: str = "redis://localhost:6379/0"
    elasticsearch_url: str = "http://localhost:9200"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    ollama_base_url: str = "http://localhost:11434"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2:3b"
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 8
    retrieval_candidates: int = 24
    max_upload_size: int = 20 * 1024 * 1024
    upload_dir: str = "./uploads"
    cors_origins: list[str] | str = ["http://localhost:5173"]
    frontend_url: str = "http://localhost:5173"
    celery_task_always_eager: bool = False
    admin_email: str = "admin@example.com"
    admin_password: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [x.strip() for x in value.split(",") if x.strip()]
        return value

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
