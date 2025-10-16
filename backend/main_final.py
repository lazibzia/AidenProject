from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
import uvicorn
import logging
from datetime import datetime, timedelta

from app_final.core.scheduler import scheduler
from app_final.core.config import RAG_INDEX_DIR, PERMITS_DB_PATH
from app_final.database import engine
from app_final.rag_engine.rag_engine_functional2 import RAGIndex

# Import all route modules
from app_final.api.dashboard import router as dashboard_router
from app_final.api.permits import router as permits_router
from app_final.api.scraping import router as scraping_router
from app_final.api.automation import router as automation_router
from app_final.api.clients import router as clients_router
from app_final.api.email import router as email_router
from app_final.api.rag import router as rag_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-City Permits Dashboard",
    description="Unified dashboard for permits across multiple cities",
    version="2.1.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG index
rag_index = RAGIndex(PERMITS_DB_PATH, index_dir=RAG_INDEX_DIR)

# Include all routers
app.include_router(dashboard_router, tags=["Dashboard"])
app.include_router(permits_router, prefix="/api", tags=["Permits"])
app.include_router(scraping_router, prefix="/api", tags=["Scraping"])
app.include_router(automation_router, prefix="/api", tags=["Automation"])
app.include_router(clients_router, tags=["Clients"])
app.include_router(email_router, prefix="/api", tags=["Email"])
app.include_router(rag_router, prefix="/api", tags=["RAG"])


@app.on_event("startup")
def startup_event():
    """Initialize database and RAG index"""
    # Create database tables
    SQLModel.metadata.create_all(engine)

    # Load RAG index
    try:
        rag_index.load()
        logger.info(f"RAG index startup status: {rag_index.status()}")
    except Exception as e:
        logger.warning(f"RAG index not loaded yet: {e}")

    # Start scheduler
    scheduler.start()

    print("🚀 Multi-City Permits Dashboard started!")
    print("🤖 4-hour automation cycle will start in 5 minutes")


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000, reload=True)