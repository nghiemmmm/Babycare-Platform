import logging
from dotenv import load_dotenv

# Nạp tất cả biến môi trường từ .env bao gồm LangSmith Tracing
load_dotenv(override=True)

from datetime import datetime, timezone
from fastapi import FastAPI, Depends, APIRouter
from fastapi.staticfiles import StaticFiles
import os

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from google.cloud.firestore import Client

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core import exception_handler
from app.core.middleware import RequestLoggingMiddleware
from app.infrastructure.database import get_firestore_db

from app.modules.auth import auth_router
from app.modules.baby import baby_router
from app.modules.guardian import guardian_router
from app.modules.notification import notification_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.growth_tracking import growth_router
from app.modules.growth_tracking.router import measurements_router
from app.modules.health_records import health_records_router
from app.modules.medication import medication_router
from app.modules.medication.router import health_medication_router
from app.modules.nutrition import nutrition_router
from app.modules.nutrition.router import feeds_router
from app.modules.cry import cry_router
from app.modules.ai_agent.router import ai_agent_router
from app.modules.jobs.router import jobs_router


# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

setup_logging()
logger = logging.getLogger(__name__)

if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    logger.info(f"[LangSmith] 🚀 Tracing Enabled | Project: '{os.getenv('LANGCHAIN_PROJECT')}' | Endpoint: '{os.getenv('LANGCHAIN_ENDPOINT')}'")
else:
    logger.warning("[LangSmith] ⚠️ Tracing is currently DISABLED.")

app = FastAPI(
    title=settings.APP_NAME,
    description="BabyCare AI Backend Services",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Serve static files (baby photos, assets)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Register Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key="babycare-ai-secret-session-key",
)
app.add_middleware(RequestLoggingMiddleware)

# Group module routers into a single api_router
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(baby_router)
api_router.include_router(guardian_router)
api_router.include_router(notification_router)
api_router.include_router(dashboard_router)
api_router.include_router(growth_router)
api_router.include_router(measurements_router)
api_router.include_router(health_records_router)
api_router.include_router(medication_router)
api_router.include_router(health_medication_router)
api_router.include_router(nutrition_router)
api_router.include_router(feeds_router)
api_router.include_router(cry_router)
api_router.include_router(ai_agent_router)
api_router.include_router(jobs_router)

app.include_router(api_router, prefix="/api/v1")

# Initialize custom exception handlers
exception_handler.init_app(app)

@app.get("/")
async def root():
    return {
        "app_name": settings.APP_NAME,
        "status": "healthy",
        "env": settings.APP_ENV
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/test-db")
async def test_db_connection(db: Client = Depends(get_firestore_db)):
    """
    Temporary endpoint to test reading and writing to Firebase Firestore.
    """
    try:
        # Write to a test collection
        doc_ref = db.collection("test_connections").document("status")
        doc_ref.set({
            "message": "Connection successful!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Read back from the collection
        doc = doc_ref.get()
        if doc.exists:
            return {
                "status": "success",
                "data_written": doc.to_dict()
            }
        else:
            return {
                "status": "failed",
                "message": "Document was written but could not be retrieved."
            }
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
