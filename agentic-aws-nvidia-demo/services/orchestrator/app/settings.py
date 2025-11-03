from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_URL: str = 'http://llm-nim.agentic.svc.cluster.local:8000'
    EMBED_URL: str = 'http://embed-nim.agentic.svc.cluster.local:8001'
    TOP_K: int = 5
    MAX_TOKENS: int = 512

settings = Settings()
