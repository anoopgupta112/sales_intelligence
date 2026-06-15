import time
import logging
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# Configure structured logging
logger = logging.getLogger("platform.observability")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
    ))
    logger.addHandler(ch)

class MetricsTracker:
    def __init__(self):
        # In-memory accumulator or stats manager
        self.stats: Dict[str, Any] = {
            "execution_time": 0.0,
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "cost": 0.0,
            "tool_calls": 0,
            "failures": 0,
            "retrieval_latency": 0.0
        }

    def add_tokens(self, prompt_tokens: int, completion_tokens: int, provider: str = "gemini"):
        self.stats["token_usage"]["prompt_tokens"] += prompt_tokens
        self.stats["token_usage"]["completion_tokens"] += completion_tokens
        self.stats["token_usage"]["total_tokens"] += (prompt_tokens + completion_tokens)
        
        # Estimate cost (rough estimates)
        # Gemini 1.5 Flash: $0.075 / 1M input tokens, $0.30 / 1M output tokens
        # OpenAI GPT-4o-mini: $0.150 / 1M input tokens, $0.60 / 1M output tokens
        if provider == "gemini":
            cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)
        else:
            cost = (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
        self.stats["cost"] += cost

    def increment_tool_calls(self):
        self.stats["tool_calls"] += 1

    def increment_failures(self):
        self.stats["failures"] += 1

    def add_retrieval_latency(self, latency: float):
        self.stats["retrieval_latency"] += latency

# Global tracker context var or local instance
_current_tracker: Optional[MetricsTracker] = None

@asynccontextmanager
async def track_execution(operation_name: str, request_id: Optional[str] = None):
    """Async context manager to track operation execution, latency, and failures."""
    start_time = time.perf_counter()
    status = "SUCCESS"
    error_msg = None
    
    try:
        yield
    except Exception as e:
        status = "FAILURE"
        error_msg = str(e)
        raise e
    finally:
        latency = time.perf_counter() - start_time
        log_payload = {
            "operation": operation_name,
            "status": status,
            "latency_seconds": round(latency, 4),
            "request_id": request_id
        }
        if error_msg:
            log_payload["error"] = error_msg
            
        logger.info(f"{log_payload}")
