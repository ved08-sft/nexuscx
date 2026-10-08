from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "NexusCX"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    JWT_SECRET_KEY: str = "change_me_in_production_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector DB
    CHROMA_PATH: str = "./data/chroma"

    # LLM Providers
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_ENABLE_GEMINI: bool = False
    GROQ_TIMEOUT_SEC: float = 1.2

    # WEKA
    WEKA_MODEL_PATH: str = "backend/ml/models/rf_escalation.model"
    RISK_WEIGHT_WEKA: float = 0.6
    RISK_WEIGHT_SENTIMENT: float = 0.4


settings = Settings()
