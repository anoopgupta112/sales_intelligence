import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from app.services.milvus_service import milvus_service
from app.core.config import settings

logger = logging.getLogger("platform.rag.indexing")

_embedding_model: Optional[SentenceTransformer] = None

def get_embedding_model() -> SentenceTransformer:
    """Lazily load the SentenceTransformer embedding model."""
    global _embedding_model
    if _embedding_model is None:
        model_name = settings.EMBEDDING_MODEL_NAME or "all-MiniLM-L6-v2"
        logger.info(f"Loading SentenceTransformer embedding model: {model_name}")
        # Default local model is light and downloads quickly
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model

def get_embedding(text: str) -> List[float]:
    """Generate embedding vector for a single text chunk."""
    model = get_embedding_model()
    vector = model.encode(text, convert_to_numpy=True).tolist()
    return vector

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embedding vectors for multiple text chunks."""
    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True).tolist()
    return vectors

async def index_document(
    collection_name: str,
    text: str,
    company_name: str = "",
    industry: str = "",
    source: str = "",
) -> None:
    """Index a single text chunk into the specified Milvus collection."""
    vector = get_embedding(text)
    entity = {
        "vector": vector,
        "text": text,
        "company_name": company_name,
        "industry": industry,
        "source": source,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    # milvus_service.insert is synchronous inside, run in executor if needed or direct
    milvus_service.insert(collection_name, [entity])

async def index_documents(
    collection_name: str,
    chunks: List[Dict[str, Any]],
) -> None:
    """
    Index multiple text chunks. 
    Each chunk in list should have a 'text' key, and optional metadata.
    """
    if not chunks:
        return
    
    texts = [chunk["text"] for chunk in chunks]
    vectors = get_embeddings(texts)
    
    entities = []
    created_at = datetime.now(timezone.utc).isoformat()
    
    for i, chunk in enumerate(chunks):
        entities.append({
            "vector": vectors[i],
            "text": chunk["text"],
            "company_name": chunk.get("company_name", ""),
            "industry": chunk.get("industry", ""),
            "source": chunk.get("source", ""),
            "created_at": chunk.get("created_at", created_at)
        })
        
    milvus_service.insert(collection_name, entities)
