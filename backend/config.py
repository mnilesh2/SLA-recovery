from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./sla_recovery.db"
    secret_key: str = "dev-secret-key-change-in-production"
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://openrouter.ai/api"
    anthropic_auth_token: str = ""
    upload_dir: str = "./uploads"
    api_host: str = "localhost"
    api_port: int = 8000
    api_url: str = "http://localhost:8000"
    frontend_port: int = 8501

    # Pipeline configuration — all "magic" values made configurable
    sql_table_name: str = "data"  # DuckDB table name for CSV data
    llm_model: str = "anthropic/claude-haiku-4.5"  # LLM model to use
    llm_max_tokens: int = 4096  # Max tokens for LLM response
    llm_temperature: float = 0.0  # LLM temperature (deterministic if 0)
    default_currency: str = "USD"  # Default currency for monetary cost types

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
