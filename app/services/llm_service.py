import logging
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger("platform.services.llm")

def get_llm(temperature: float = 0.2) -> Any:
    """
    Get the configured LLM client instance (Gemini or OpenAI).
    Uses settings to determine the provider and api keys.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set. Falling back to mock model or dry run.")
        logger.info("Initializing OpenAI Chat Model (gpt-4o-mini)")
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0,
            max_retries=3
        )
    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Falling back to mock/openai.")
        logger.info("Initializing Google Gemini Chat Model (gemini-1.5-flash)")
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=temperature,
            google_api_key=settings.GEMINI_API_KEY,
            timeout=30.0,
            max_retries=3
        )
    elif provider == "agentrouter" or provider == "agent_router":
        if not settings.AGENT_ROUTER_API_KEY:
            logger.warning("AGENT_ROUTER_API_KEY is not set. Falling back to mock model or dry run.")
        logger.info(f"Initializing AgentRouter Chat Model ({settings.AGENT_ROUTER_MODEL})")
        return ChatOpenAI(
            model=settings.AGENT_ROUTER_MODEL,
            temperature=temperature,
            api_key=settings.AGENT_ROUTER_API_KEY,
            base_url=settings.AGENT_ROUTER_BASE_URL,
            timeout=30.0,
            max_retries=3
        )
    else:
        # Fallback to OpenAI gpt-4o-mini if provider is unknown
        logger.warning(f"Unknown LLM Provider '{provider}'. Defaulting to OpenAI.")
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
