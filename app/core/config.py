from typing import Optional, Any
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Explicitly load environment variables from .env file into os.environ
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    DATABASE_URL: Optional[str] = None
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    JWT_SECRET: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # or "openai", "agentrouter"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AGENT_ROUTER_API_KEY: Optional[str] = None
    AGENT_ROUTER_BASE_URL: str = "https://agentrouter.org/v1"
    AGENT_ROUTER_MODEL: str = "deepseek-r1-0528"

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # WhatsApp Settings
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None

    # LangChain/LangSmith Settings
    LANGCHAIN_TRACING_V2: Optional[str] = None
    LANGCHAIN_ENDPOINT: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if isinstance(v, str) and v.strip() == "":
                    cleaned[k] = None
                else:
                    cleaned[k] = v
            return cleaned
        return data

settings = Settings()

