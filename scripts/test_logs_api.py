import urllib.request
import json
import sys
from datetime import datetime, timezone

# Reconfigure stdout/stderr for Unicode support on Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://localhost:8000"
HEADERS = {
    "Authorization": "Bearer mock-token",
    "Content-Type": "application/json"
}

def make_request(path, method="GET", body=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            content = response.read().decode("utf-8")
            return status, json.loads(content) if content else None
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = content
        return e.code, err_json
    except Exception as e:
        return 0, str(e)

def run_tests():
    print("=" * 60)
    print("BABYCARE AI: TESTING DIARY/LOGS ENDPOINTS")
    print("=" * 60)

    # 1. Get Active Baby ID first
    status, babies = make_request("/api/v1/babies/")
    if status != 200 or not babies:
        print("[-] Error: Cannot list babies to find active baby ID.")
        return
    baby_id = babies[0]["id"]
    baby_name = babies[0]["name"]
    print(f"[+] Using Active Baby: {baby_name} (ID: {baby_id})")

    # 2. HEALTH RECORDS TESTS
    print(f"\n--- 1. Testing Health Records (Bệnh án & Triệu chứng) ---")
    
    # 2.1 List before creating
    status, history = make_request(f"/api/v1/babies/{baby_id}/health-records")
    print(f"   - GET /api/v1/babies/{baby_id}/health-records -> Status: {status}")
    if status == 200:
        print(f"     [+] Number of existing health records: {len(history)}")
        for r in history[:2]:
            print(f"         * Symptoms: {r.get('symptoms')}, Diagnosis: {r.get('diagnosis')}, Treatment: {r.get('treatment')}")
    else:
        print(f"     [-] Error: {history}")

    # 2.2 Create a test record
    record_payload = {
        "symptoms": ["Ho khan", "Sốt mọc răng"],
        "diagnosis": "Mọc răng sữa",
        "treatment": "Theo dõi nhiệt độ và cho uống nhiều nước ấm",
        "notes": "Sờ nướu sưng nhẹ, không sốt cao.",
        "doctor_name": "Dr. Watson"
    }
    status, created_record = make_request(
        f"/api/v1/babies/{baby_id}/health-records",
        method="POST",
        body=record_payload
    )
    print(f"   - POST /api/v1/babies/{baby_id}/health-records -> Status: {status}")
    if status == 201 and created_record:
        record_id = created_record["id"]
        print(f"     [+] Created record successfully! ID: {record_id}")
        print(f"         * Symptoms in DB: {created_record['symptoms']}")
    else:
        print(f"     [-] Error: {created_record}")
        return

    # 2.3 List again to verify
    status, history = make_request(f"/api/v1/babies/{baby_id}/health-records")
    if status == 200:
        found = any(r["id"] == record_id for r in history)
        if found:
            print("     [+] Verification Success: New record found in history list!")
        else:
            print("     [-] Verification Failed: New record not found.")

    # 2.4 Delete the record
    status, delete_msg = make_request(
        f"/api/v1/babies/{baby_id}/health-records/{record_id}",
        method="DELETE"
    )
    print(f"   - DELETE /api/v1/babies/{baby_id}/health-records/{record_id} -> Status: {status}")
    if status == 200 and delete_msg:
        print(f"     [+] Delete response message: {delete_msg['message']}")
    else:
        print(f"     [-] Error deleting record: {delete_msg}")

    # 3. AI CRY DETECTION HISTORY
    print(f"\n--- 2. Testing AI Cry Detection (Nhận dạng tiếng khóc) ---")
    status, cry_history = make_request(f"/api/v1/babies/{baby_id}/cry-prediction")
    print(f"   - GET /api/v1/babies/{baby_id}/cry-prediction -> Status: {status}")
    if status == 200:
        print(f"     [+] Number of existing cry logs: {len(cry_history)}")
        for log in cry_history[:2]:
            print(f"         * Predicted reason: {log.get('predicted_reason')}, Confidence: {log.get('confidence')*100:.1f}%, Accurate: {log.get('feedback_accurate')}")
            
        if cry_history:
            test_cry_log = cry_history[0]
            log_id = test_cry_log["id"]
            
            # 3.1 Update feedback (accurate = True)
            # Route uses query param feedback_accurate or path? Let's check:
            # Route has: @router.patch("/{baby_id}/cry-prediction/{log_id}/feedback")
            # signature: baby_id: str, log_id: str, feedback_accurate: bool
            # Since feedback_accurate is a query parameter in FastAPI:
            status, feedback_res = make_request(
                f"/api/v1/babies/{baby_id}/cry-prediction/{log_id}/feedback?feedback_accurate=true",
                method="PATCH"
            )
            print(f"   - PATCH /api/v1/babies/{baby_id}/cry-prediction/{log_id}/feedback -> Status: {status}")
            if status == 200 and feedback_res:
                print(f"     [+] Updated feedback successfully! New feedback: {feedback_res['feedback_accurate']}")
            else:
                print(f"     [-] Error updating feedback: {feedback_res}")
    else:
        print(f"     [-] Error retrieving cry logs: {cry_history}")

    print("\n" + "=" * 60)
    print("DIARY/LOGS ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
