import sys
from unittest.mock import patch, MagicMock
import pytest

from app.infrastructure.database.connection import initialize_firebase, get_firestore_db
from app.core.config import settings

def test_initialize_firebase_with_path():
    # Reset globals in connection module to simulate clean run
    import app.infrastructure.database.connection as conn
    conn._firebase_app = None
    conn._db_client = None

    # Configure mock settings
    settings.FIREBASE_CREDENTIALS_PATH = "dummy_path.json"
    settings.FIREBASE_CREDENTIALS_JSON = None

    with patch("firebase_admin.get_app", side_effect=ValueError("No app initialized")), \
         patch("firebase_admin.credentials.Certificate") as mock_cert, \
         patch("firebase_admin.initialize_app") as mock_init_app, \
         patch("firebase_admin.firestore.client") as mock_firestore_client:
        
        initialize_firebase()
        
        mock_cert.assert_called_once_with("dummy_path.json")
        mock_init_app.assert_called_once()
        mock_firestore_client.assert_called_once()

def test_initialize_firebase_with_json():
    # Reset globals in connection module
    import app.infrastructure.database.connection as conn
    conn._firebase_app = None
    conn._db_client = None

    # Configure mock settings
    settings.FIREBASE_CREDENTIALS_PATH = None
    settings.FIREBASE_CREDENTIALS_JSON = '{"type": "service_account"}'

    with patch("firebase_admin.get_app", side_effect=ValueError("No app initialized")), \
         patch("firebase_admin.credentials.Certificate") as mock_cert, \
         patch("firebase_admin.initialize_app") as mock_init_app, \
         patch("firebase_admin.firestore.client") as mock_firestore_client:
        
        initialize_firebase()
        
        mock_cert.assert_called_once_with({"type": "service_account"})
        mock_init_app.assert_called_once()
        mock_firestore_client.assert_called_once()
