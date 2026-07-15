import os
import sys
import time
import logging

# Add root directory to sys.path to resolve imports when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.infrastructure.database.connection import get_firestore_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend_pre_start")

max_tries = 10
sleep_time_seconds = 5

def main() -> None:
    logger.info("Initializing babycare-ai backend pre-start checks...")
    
    db_ok = False
    for attempt in range(1, max_tries + 1):
        try:
            logger.info(f"Attempting to connect to Firebase Firestore (Attempt {attempt}/{max_tries})...")
            db = get_firestore_db()
            
            # Verify connection by performing a lightweight get request
            doc_ref = db.collection("test_connections").document("ping")
            doc_ref.get()
            
            logger.info("Firebase Firestore connectivity successfully verified!")
            db_ok = True
            break
        except Exception as e:
            logger.warning(f"Connection attempt {attempt} failed: {e}")
            if attempt < max_tries:
                logger.info(f"Retrying in {sleep_time_seconds} seconds...")
                time.sleep(sleep_time_seconds)
            else:
                logger.error("Max connection retries exceeded.")
                
    if not db_ok:
        logger.error("Backend pre-start checks FAILED. Exiting with error.")
        sys.exit(1)
        
    logger.info("Backend pre-start checks COMPLETED successfully.")

if __name__ == "__main__":
    main()
