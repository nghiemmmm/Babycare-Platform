from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.infrastructure.database.connection import initialize_firebase

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up BabyCare AI application...")
    try:
        initialize_firebase()
        logger.info("Firebase initialization verified on startup.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase on startup: {e}")
        raise e

    yield

    # Shutdown
    logger.info("Shutting down BabyCare AI application...")
    
    # Dừng các Background Tasks đang chạy ngầm
    import asyncio
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pending:
        logger.info(f"Cancelling {len(pending)} pending background tasks...")
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        logger.info("All background tasks stopped successfully.")

