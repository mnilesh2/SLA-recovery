from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./sla_recovery.db"
    secret_key: str = "dev-secret-key-change-in-production"
    openai_api_key: str = ""
    upload_dir: str = "./uploads"
    api_host: str = "localhost"
    api_port: int = 8000
    api_url: str = "http://localhost:8000"
    frontend_port: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
