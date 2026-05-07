from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    OPENAI_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    API_KEY: str = "dev-key"
    COLLECTION_NAME: str = "rag_collection"

    MODEL_PROVIDER: str = "openai"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"


settings = Settings()
