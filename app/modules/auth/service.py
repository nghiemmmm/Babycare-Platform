import logging
from datetime import datetime, timezone
from google.cloud.firestore import Client
from app.infrastructure.database import get_firestore_db
from app.modules.auth.schemas import UserRecord

logger = logging.getLogger(__name__)

def get_or_create_user_profile(user: UserRecord, db: Client = None) -> dict:
    """
    Check if user exists in the Firestore 'users' collection.
    If not, create a new profile document.
    Returns the user document data.
    """
    if db is None:
        db = get_firestore_db()
        
    user_ref = db.collection("users").document(user.uid)
    try:
        doc = user_ref.get()
        if doc.exists:
            # User exists, let's update last login time or just return the data
            user_data = doc.to_dict()
            user_ref.update({
                "last_login_at": datetime.now(timezone.utc).isoformat()
            })
            user_data["last_login_at"] = datetime.now(timezone.utc).isoformat()
            return user_data
        else:
            # User does not exist, let's create a new record (Just-in-Time provisioning)
            logger.info(f"Creating new user profile document for UID: {user.uid}")
            username = user.email.split("@")[0] if user.email else f"user_{user.uid[:8]}"
            user_profile = {
                "username": username,
                "email": user.email,
                "role": "USER",
                "active": True,
                "first_login": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_login_at": datetime.now(timezone.utc).isoformat()
            }
            user_ref.set(user_profile)
            return user_profile
    except Exception as e:
        logger.error(f"Error getting or creating user profile in Firestore: {e}")
        raise e

def update_user_profile(uid: str, update_data: dict, db: Client = None) -> dict:
    """
    Cập nhật các trường thông tin trong hồ sơ người dùng trên Firestore.
    """
    if db is None:
        db = get_firestore_db()
        
    user_ref = db.collection("users").document(uid)
    try:
        # Lọc bỏ các giá trị None và cập nhật thời gian chỉnh sửa
        filtered_data = {k: v for k, v in update_data.items() if v is not None}
        filtered_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        user_ref.update(filtered_data)
        
        # Trả về dữ liệu mới nhất
        doc = user_ref.get()
        return doc.to_dict()
    except Exception as e:
        logger.error(f"Error updating user profile in Firestore: {e}")
        raise e

