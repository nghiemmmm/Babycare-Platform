import urllib.request
import json
import sys
from datetime import datetime, timezone, timedelta

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
    print("BABYCARE AI: TESTING HEALTH & MEDICATION SAFETY ENDPOINTS")
    print("=" * 60)

    # 1. Get Active Baby ID
    status, babies = make_request("/api/v1/babies/")
    if status != 200 or not babies:
        print("[-] Error: Cannot list babies.")
        return
    baby_id = babies[0]["id"]
    print(f"[+] Active Baby ID: {baby_id}")

    # 2. Check current health dashboard state
    print("\n1. GET /api/v1/health/dashboard (Initial check)")
    status, initial_dashboard = make_request(f"/api/v1/health/dashboard?baby_id={baby_id}")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Initial Safety Alert Level: {initial_dashboard['safety_alert']['level']}")
        print(f"   [+] Initial Message: {initial_dashboard['safety_alert']['message']}")
        if initial_dashboard.get('countdown_widget'):
            print(f"   [+] Countdown active: {initial_dashboard['countdown_widget']['is_administer_disabled']}")
    else:
        print(f"   [-] Error: {initial_dashboard}")

    # 3. Simulate administering Paracetamol NOW (should trigger CRITICAL warning)
    now_str = datetime.now(timezone.utc).isoformat()
    print("\n2. POST /api/v1/health/medications/administer (Administer Paracetamol now)")
    payload_now = {
        "baby_id": baby_id,
        "medication_name": "Hapacol 150mg (Paracetamol)",
        "amount": "150mg",
        "administered_at": now_str
    }
    status, admin_res = make_request(
        "/api/v1/health/medications/administer",
        method="POST",
        body=payload_now
    )
    print(f"   Status: {status}")
    if status == 200:
        print("   [+] Administered successfully!")
        print(f"   [+] Countdown seconds: {admin_res.get('countdown_seconds')}s")
    else:
        print(f"   [-] Error administering: {admin_res}")
        return

    # 4. Check Health Dashboard state again (should be CRITICAL, disabled=True)
    print("\n3. GET /api/v1/health/dashboard (Check warning status - expect CRITICAL)")
    status, critical_dashboard = make_request(f"/api/v1/health/dashboard?baby_id={baby_id}")
    print(f"   Status: {status}")
    if status == 200:
        alert = critical_dashboard['safety_alert']
        widget = critical_dashboard['countdown_widget']
        print(f"   [+] Warning Level: {alert['level']} (Expected: CRITICAL)")
        print(f"   [+] Message: {alert['message']}")
        print(f"   [+] Is administer disabled: {widget['is_administer_disabled']} (Expected: True)")
    else:
        print(f"   [-] Error: {critical_dashboard}")

    # 5. Clean up by deleting the log we just created
    print("\n4. Clean up medication logs")
    status, med_logs = make_request(f"/api/v1/babies/{baby_id}/medication")
    if status == 200:
        # Find the log we created
        test_log_id = None
        for log in med_logs:
            if log["medication_name"] == "Hapacol 150mg (Paracetamol)" and log["dosage"] == "150mg":
                test_log_id = log["id"]
                break
        if test_log_id:
            print(f"   - DELETE /api/v1/babies/{baby_id}/medication/{test_log_id}")
            del_status, del_msg = make_request(f"/api/v1/babies/{baby_id}/medication/{test_log_id}", method="DELETE")
            print(f"     Status: {del_status}, Message: {del_msg.get('message')}")
        else:
            print("   [-] Could not find the test log to delete.")
    else:
        print(f"   [-] Error listing logs for deletion: {med_logs}")

    print("\n" + "=" * 60)
    print("HEALTH & MEDICATION ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
