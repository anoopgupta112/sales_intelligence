import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.whatsapp import router as whatsapp_router
from app.api.frontend import router as frontend_router
from app.services.milvus_service import milvus_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("platform.main")

app = FastAPI(
    title="Enterprise Sales Intelligence Platform",
    description="Asynchronous multi-agent sales platform driven by LangGraph, CrewAI, and Milvus.",
    version="1.0.0",
    docs_url="/api/docs"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing services on startup...")
    # Attempt to connect to Milvus in the background so API startup is not blocked if Milvus is booting
    import threading
    threading.Thread(target=milvus_service.connect, kwargs={"retries": 3, "delay": 2.0}, daemon=True).start()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Include routing
app.include_router(router)
app.include_router(whatsapp_router, prefix="/api")
app.include_router(frontend_router)
