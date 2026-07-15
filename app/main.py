import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, APIRouter
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
from app.modules.growth_tracking import growth_router
from app.modules.health_records import health_records_router
from app.modules.medication import medication_router
from app.modules.nutrition import nutrition_router
from app.modules.cry import cry_router

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

setup_logging()
logger = logging.getLogger(__name__)

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
api_router.include_router(growth_router)
api_router.include_router(health_records_router)
api_router.include_router(medication_router)
api_router.include_router(nutrition_router)
api_router.include_router(cry_router)

app.include_router(api_router, prefix="/api")

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
