import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add current directory to sys.path to resolve app imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables from .env
load_dotenv()

from app.infrastructure.database.connection import get_firestore_db
from app.core.config import settings

def test_firebase_connection():
    print("=== Testing Firebase Firestore Connection ===")
    
    # 1. Print current settings/env
    print(f"App Name: {settings.APP_NAME}")
    print(f"App Env: {settings.APP_ENV}")
    print(f"Firebase Key Path: {settings.FIREBASE_CREDENTIALS_PATH}")
    
    if not settings.FIREBASE_CREDENTIALS_PATH and not settings.FIREBASE_CREDENTIALS_JSON:
        print("Error: No Firebase credentials configured in .env!")
        return

    # 2. Get Firestore Client
    try:
        print("Initializing database client...")
        db = get_firestore_db()
        print("Database client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        return

    # 3. Try to write a test document
    try:
        print("Writing test document to collection 'test_connections'...")
        doc_ref = db.collection("test_connections").document("status")
        doc_ref.set({
            "message": "Hello from local connection test!",
            "status": "connected",
            "tested_at": datetime.now(timezone.utc).isoformat()
        })
        print("Test document written successfully.")
    except Exception as e:
        print(f"Error writing to Firestore: {e}")
        return

    # 4. Try to read the document back
    try:
        print("Reading test document back...")
        doc = doc_ref.get()
        if doc.exists:
            print("Document successfully retrieved:")
            print(f"  Data: {doc.to_dict()}")
        else:
            print("Error: Document was written but not found on retrieval.")
    except Exception as e:
        print(f"Error reading from Firestore: {e}")
        return

    # 5. Clean up (delete) the test document
    try:
        print("Cleaning up test document...")
        doc_ref.delete()
        print("Cleanup completed successfully.")
    except Exception as e:
        print(f"Warning: Failed to delete test document during cleanup: {e}")

    print("\n=== Connection Test SUCCESSFUL! ===")

if __name__ == "__main__":
    test_firebase_connection()
