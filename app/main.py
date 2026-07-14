import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from google.cloud.firestore import Client
from app.core.config import settings
from app.core.lifespan import lifespan
from app.infrastructure.database import get_firestore_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="BabyCare AI Backend Services",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

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
