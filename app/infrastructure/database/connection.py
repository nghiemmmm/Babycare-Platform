import json
import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global variables for firebase app and firestore client
_firebase_app = None
_db_client: Optional[Client] = None

def initialize_firebase() -> firebase_admin.App:
    """
    Initializes the Firebase Admin SDK and Firestore client.
    """
    global _firebase_app, _db_client

    if _firebase_app is not None:
        return _firebase_app

    # Check if default app is already initialized
    try:
        _firebase_app = firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized.")
    except ValueError:
        # App is not initialized, let's initialize it
        cred = None

        if settings.FIREBASE_CREDENTIALS_JSON:
            try:
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
                logger.info("Initializing Firebase using credentials JSON from environment.")
            except Exception as e:
                logger.error(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")
                raise e
        elif settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            try:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                logger.info(f"Initializing Firebase using credentials file from path: {settings.FIREBASE_CREDENTIALS_PATH}")
            except Exception as e:
                logger.error(f"Failed to load Firebase credentials from path {settings.FIREBASE_CREDENTIALS_PATH}: {e}")
                if os.getenv("APP_ENV") == "production":
                    raise e
        else:
            logger.warning("Firebase credentials not configured or file not found. Attempting to use Application Default Credentials.")
            try:
                cred = credentials.ApplicationDefault()
            except Exception as e:
                logger.warning(f"Application Default Credentials notice: {e}")
                if os.getenv("APP_ENV") == "production":
                    raise ValueError("Firebase credentials not configured for production.")
                cred = None

        if cred is not None:
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK successfully initialized.")
        else:
            logger.warning("Running in mock/local mode without active Firebase credentials.")

    # Initialize Firestore Client
    _db_client = firestore.client()
    return _firebase_app

def get_firestore_db() -> Client:
    """
    Dependency or helper function to get the Firestore client.
    Ensures Firebase is initialized before returning the client.
    """
    global _db_client
    if _db_client is None:
        initialize_firebase()
    if _db_client is None:
        raise RuntimeError("Firestore client could not be initialized.")
    return _db_client
