import os
import sys
from dotenv import load_dotenv

# Set base dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.infrastructure.database.connection import get_firestore_db

def main():
    db = get_firestore_db()
    print("=== INSPECTING USERS ===")
    users = {}
    for doc in db.collection("users").stream():
        data = doc.to_dict()
        users[doc.id] = data
        print(f"UID: {doc.id} | Email: {data.get('email')} | Name: {data.get('name')}")

    print("\n=== INSPECTING BABIES ===")
    babies_to_delete = []
    for doc in db.collection("babies").stream():
        data = doc.to_dict()
        guardians = data.get("guardians", [])
        print(f"Baby ID: {doc.id} | Name: {data.get('name')} | Guardians: {guardians}")
        
        # Check if this baby belongs to Hoai or is an auto-generated Leo for non-demo users
        for g_uid in guardians:
            user_data = users.get(g_uid, {})
            u_email = str(user_data.get("email", "")).lower()
            u_name = str(user_data.get("name", "")).lower()
            if "hoai" in u_email or "hoài" in u_name or "hoai" in u_name:
                print(f"--> Found baby {doc.id} linked to user Hoai ({u_email}). Marking for deletion...")
                babies_to_delete.append((doc.id, data.get('name'), u_email))
            elif u_email != "nghiem@babycare.com" and doc.id.startswith("baby_") and not doc.id.startswith(f"baby_{g_uid}"):
                # Also check any generic auto-seeded baby
                pass

    if babies_to_delete:
        print(f"\nDeleting {len(babies_to_delete)} auto-seeded babies...")
        for b_id, b_name, u_email in babies_to_delete:
            db.collection("babies").document(b_id).delete()
            print(f"-> Deleted baby '{b_name}' ({b_id}) of user '{u_email}'.")
            
            # Also clean up guardians collection if any
            for g_doc in db.collection("guardians").where("baby_id", "==", b_id).stream():
                db.collection("guardians").document(g_doc.id).delete()
                print(f"   -> Deleted guardian record {g_doc.id}")
        print("Cleanup completed successfully.")
    else:
        print("\nNo auto-seeded babies found for user Hoai.")

if __name__ == "__main__":
    main()
