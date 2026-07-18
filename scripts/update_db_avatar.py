import sys
import os

# Include project root in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.infrastructure.database import get_firestore_db

def update_avatars():
    print("=" * 60)
    print("BABYCARE AI: UPDATING BABY AVATAR URLS IN FIRESTORE")
    print("=" * 60)
    
    db = get_firestore_db()
    babies_ref = db.collection("babies")
    docs = list(babies_ref.stream())
    
    if not docs:
        print("[-] No babies found in Firestore database.")
        return
        
    print(f"[+] Found {len(docs)} baby profile documents.")
    for doc in docs:
        d = doc.to_dict()
        name = d.get("name", "Unknown")
        old_avatar = d.get("avatar_url", "")
        
        # Decide new avatar URL
        new_avatar = "/static/img/leo.png"
        if name.lower() == "bo":
            new_avatar = "/static/img/bo.png"
            
        print(f"    * Baby '{name}':")
        print(f"      - Old URL: {old_avatar}")
        print(f"      - New URL: {new_avatar}")
        
        doc.reference.update({
            "avatar_url": new_avatar
        })
        print(f"      [+] Updated document successfully!")

if __name__ == "__main__":
    update_avatars()
