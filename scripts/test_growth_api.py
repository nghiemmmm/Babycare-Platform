import urllib.request
import json
import sys

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
    print("BABYCARE AI: TESTING GROWTH TRACKING ENDPOINTS")
    print("=" * 60)

    # 1. Get Active Baby ID
    status, babies = make_request("/api/v1/babies/")
    if status != 200 or not babies:
        print("[-] Error: Cannot list babies.")
        return
    baby_id = babies[0]["id"]
    print(f"[+] Active Baby ID: {baby_id}")

    # 2. LIST MEASUREMENTS (GET /api/v1/growth/measurements?baby_id=...)
    print("\n1. GET /api/v1/growth/measurements (List measurements before test)")
    status, measurements = make_request(f"/api/v1/growth/measurements?baby_id={baby_id}")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Number of existing measurements: {len(measurements)}")
        for m in measurements[:3]:
            print(f"       - ID: {m['id']}, Age: {m['age_months']} months, Weight: {m['weight']} kg, Height: {m['height']} cm, Date: {m['date']}")
    else:
        print(f"   [-] Error: {measurements}")
        return

    # 3. ADD NEW MEASUREMENT (POST /api/v1/growth/measurements)
    print("\n2. POST /api/v1/growth/measurements (Add a new physical measurement)")
    payload = {
        "baby_id": baby_id,
        "weight": 8.5,
        "height": 71.0,
        "head_circumference": 43.5,
        "date": "2026-07-18"
    }
    status, res = make_request("/api/v1/growth/measurements", method="POST", body=payload)
    print(f"   Status: {status}")
    if status == 200 and res:
        new_m_id = res["measurement_id"]
        percentiles = res["percentiles"]
        print(f"   [+] Added successfully!")
        print(f"       - Assigned ID: {new_m_id}")
        print(f"       - WHO Weight Percentile: {percentiles['weight_percentile']}")
        print(f"       - WHO Height Percentile: {percentiles['height_percentile']}")
        print(f"       - WHO Head Circumference Percentile: {percentiles['head_percentile']}")
    else:
        print(f"   [-] Error adding measurement: {res}")
        return

    # 4. LIST AGAIN TO VERIFY INCLUSION
    print("\n3. GET /api/v1/growth/measurements (Verify inclusion)")
    status, measurements = make_request(f"/api/v1/growth/measurements?baby_id={baby_id}")
    if status == 200:
        found = any(m["id"] == new_m_id for m in measurements)
        if found:
            print("   [+] Verification Success: New measurement is present in the list!")
        else:
            print("   [-] Verification Failed: New measurement is missing.")
    else:
        print(f"   [-] Error: {measurements}")

    # 5. DELETE MEASUREMENT (DELETE /api/v1/babies/{baby_id}/growth/{log_id})
    print(f"\n4. DELETE /api/v1/babies/{baby_id}/growth/{new_m_id} (Clean up measurement)")
    status, del_msg = make_request(f"/api/v1/babies/{baby_id}/growth/{new_m_id}", method="DELETE")
    print(f"   Status: {status}")
    if status == 200 and del_msg:
        print(f"   [+] Deletion success message: {del_msg['message']}")
    else:
        print(f"   [-] Error deleting measurement: {del_msg}")

    # 6. VERIFY DELETION
    print("\n5. GET /api/v1/growth/measurements (Confirm deletion)")
    status, measurements = make_request(f"/api/v1/growth/measurements?baby_id={baby_id}")
    if status == 200:
        if not any(m["id"] == new_m_id for m in measurements):
            print("   [+] Verification Success: Measurement was removed from the list.")
        else:
            print("   [-] Verification Failed: Measurement is still present.")
    else:
        print(f"   [-] Error: {measurements}")

    print("\n" + "=" * 60)
    print("GROWTH TRACKING ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
