from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./sla_recovery.db"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # LLM Provider (openrouter or anthropic)
    llm_provider: str = "openrouter"

    # OpenRouter API
    openrouter_api_key: str = ""

    # Anthropic Claude API (for backward compatibility)
    anthropic_api_key: str = ""

    # Model configuration
    llm_model: str = "openai/gpt-4-turbo"
    llm_max_tokens: int = 4096
    llm_thinking_enabled: bool = False
    llm_thinking_budget: int = 5000

    # File handling
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # API configuration
    api_host: str = "localhost"
    api_port: int = 8000
    api_url: str = "http://localhost:8000"
    frontend_port: int = 8501

    # Document processing
    default_document_type: str = "custom"

    # LLM behavior
    use_mock_llm: bool = False
    mock_responses_dir: str = "./mock_responses"

    # Performance
    cache_llm_responses: bool = True
    cache_dir: str = "./cache"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_supported_document_types(self) -> List[str]:
        """Get list of supported document types"""
        return ["sla", "contract", "insurance", "service_agreement", "custom"]


settings = Settings()
