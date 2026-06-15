import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType
from app.core.config import settings
from app.core.exceptions import MilvusError

logger = logging.getLogger("platform.milvus")

class MilvusService:
    def __init__(self):
        self.connected = False
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        if "openai" in settings.EMBEDDING_MODEL_NAME or settings.LLM_PROVIDER == "openai":
            self.embedding_dim = 1536

    def connect(self, retries: int = 5, delay: float = 2.0) -> bool:
        """Connect to Milvus service with retry logic."""
        if self.connected:
            return True

        for i in range(retries):
            try:
                logger.info(f"Connecting to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT} (attempt {i+1}/{retries})...")
                connections.connect(
                    alias="default",
                    host=settings.MILVUS_HOST,
                    port=str(settings.MILVUS_PORT),
                    timeout=10.0
                )
                self.connected = True
                logger.info("Successfully connected to Milvus.")
                self.initialize_collections()
                return True
            except Exception as e:
                logger.warning(f"Failed to connect to Milvus: {e}")
                if i < retries - 1:
                    time.sleep(delay * (2 ** i))  # Exponential backoff
        
        logger.error("Could not establish connection to Milvus.")
        return False

    def initialize_collections(self):
        """Create collections if they do not exist."""
        try:
            collections_to_create = ["company_knowledge", "sales_playbooks", "research_reports"]
            for col_name in collections_to_create:
                if not utility.has_collection(col_name):
                    self.create_collection(col_name)
                    logger.info(f"Created Milvus collection: {col_name}")
                else:
                    logger.debug(f"Milvus collection already exists: {col_name}")
        except Exception as e:
            logger.error(f"Error initializing Milvus collections: {e}")
            raise MilvusError(f"Milvus initialization failed: {e}")

    def create_collection(self, collection_name: str):
        """Create a standard Milvus collection schema."""
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="company_name", dtype=DataType.VARCHAR, max_length=255, default_value=""),
            FieldSchema(name="industry", dtype=DataType.VARCHAR, max_length=255, default_value=""),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=255, default_value=""),
            FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50, default_value="")
        ]
        schema = CollectionSchema(fields=fields, description=f"{collection_name} collection")
        col = Collection(name=collection_name, schema=schema)
        
        # Create an IVF_FLAT or FLAT index for fast search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "FLAT",
            "params": {}
        }
        col.create_index(field_name="vector", index_params=index_params)
        logger.info(f"Created index on collection: {collection_name}")

    def insert(self, collection_name: str, entities: List[Dict[str, Any]]):
        """Insert records into a collection."""
        if not self.connect():
            raise MilvusError("Milvus is offline. Cannot insert.")
        
        try:
            col = Collection(collection_name)
            # Structure data for insert
            # PyMilvus expects arrays of columns
            data = [
                [entity["vector"] for entity in entities],
                [entity["text"] for entity in entities],
                [entity.get("company_name", "") for entity in entities],
                [entity.get("industry", "") for entity in entities],
                [entity.get("source", "") for entity in entities],
                [entity.get("created_at", "") for entity in entities]
            ]
            col.insert(data)
            col.flush()
            logger.info(f"Inserted {len(entities)} vectors into {collection_name}")
        except Exception as e:
            logger.error(f"Error inserting into Milvus collection {collection_name}: {e}")
            raise MilvusError(f"Milvus insert failed: {e}")

    def search(self, collection_name: str, query_vector: List[float], limit: int = 5, expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search similar entities in collection."""
        if not self.connect():
            # In testing/local fallback, return empty list or fallback gracefully
            logger.warning("Milvus is offline. Returning empty search results.")
            return []
        
        try:
            col = Collection(collection_name)
            col.load()  # Must load collection into memory before search
            
            search_params = {
                "metric_type": "COSINE",
                "params": {}
            }
            
            results = col.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["text", "company_name", "industry", "source", "created_at"]
            )
            
            hits = []
            for hit in results[0]:
                hits.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "text": hit.entity.get("text"),
                    "company_name": hit.entity.get("company_name"),
                    "industry": hit.entity.get("industry"),
                    "source": hit.entity.get("source"),
                    "created_at": hit.entity.get("created_at")
                })
            return hits
        except Exception as e:
            logger.error(f"Error searching Milvus collection {collection_name}: {e}")
            raise MilvusError(f"Milvus search failed: {e}")

milvus_service = MilvusService()
