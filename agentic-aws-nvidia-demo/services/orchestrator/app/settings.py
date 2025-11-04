import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API URLs
    LLM_URL: str = 'http://llm-nim.agentic.svc.cluster.local:8000'
    EMBED_URL: str = 'http://embed-nim.agentic.svc.cluster.local:8001'
    
    # RAG Settings
    TOP_K: int = 5
    MAX_TOKENS: int = 512
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80
    
    # Database
    DATABASE_URL: str = 'sqlite:///./storyweave.db'
    
    # File Storage
    UPLOAD_DIR: str = './uploads'
    INDEX_DIR: str = './indices'
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    # Note: Pydantic doesn't support set directly, so we'll use a list
    ALLOWED_EXTENSIONS: list = ['.md', '.txt', '.pdf']
    
    # API Settings
    API_TIMEOUT: int = 120
    MAX_UPLOAD_FILES: int = 10
    
    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FILE: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = 'development'
    USE_MOCK: bool = os.getenv("USE_MOCK", "0") == "1"
    
    # NVIDIA NIM API Settings
    NIM_API_KEY: Optional[str] = os.getenv("NIM_API_KEY")
    NVCF_BASE: str = os.getenv("NVCF_BASE", "https://integrate.api.nvidia.com/v1")
    NIM_TEXT_FUNC_ID: Optional[str] = os.getenv("NIM_TEXT_FUNC_ID", "meta/llama-3.1-nemotron-70b-instruct")
    
    # Sentry Configuration
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_RELEASE: Optional[str] = os.getenv("SENTRY_RELEASE", "1.0.0")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.INDEX_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
