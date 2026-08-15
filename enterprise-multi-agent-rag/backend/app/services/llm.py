from abc import ABC, abstractmethod
import httpx
from app.core.config import settings

class LLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str | None = None) -> str: ...

class OllamaLLM(LLMService):
    async def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {"model": settings.llm_model, "prompt": prompt, "system": system or "", "stream": False}
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(f"{settings.ollama_base_url.rstrip('/')}/api/generate", json=payload)
            res.raise_for_status()
            return res.json().get("response", "").strip()

class OpenAICompatibleLLM(LLMService):
    async def generate(self, prompt: str, system: str | None = None) -> str:
        if not settings.openai_compatible_base_url or not settings.openai_compatible_api_key:
            raise RuntimeError("OpenAI-compatible provider is not configured")
        headers = {"Authorization": f"Bearer {settings.openai_compatible_api_key}"}
        body = {"model": settings.llm_model, "messages": [
            {"role": "system", "content": system or "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ], "temperature": 0.1}
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(f"{settings.openai_compatible_base_url.rstrip('/')}/chat/completions", headers=headers, json=body)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()

def get_llm_service() -> LLMService:
    return OpenAICompatibleLLM() if settings.llm_provider.lower() in {"openai", "openai-compatible"} else OllamaLLM()
