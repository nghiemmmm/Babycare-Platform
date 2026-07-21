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
    if body:
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
    print("BABYCARE AI: TESTING DASHBOARD ENDPOINTS")
    print("=" * 60)

    # 1. GET /api/v1/babies
    status, babies = make_request("/api/v1/babies")
    print(f"1. GET /api/v1/babies -> Status: {status}")
    if status != 200 or not babies:
        print("[-] Error listing babies or empty list. Cannot proceed with other tests.")
        sys.exit(1)
    
    baby_id = babies[0]["id"]
    baby_name = babies[0]["name"]
    print(f"   [+] Active Baby Found: {baby_name} (ID: {baby_id})")

    # 2. GET /api/v1/dashboard
    status, dashboard = make_request(f"/api/v1/dashboard?baby_id={baby_id}")
    print(f"\n2. GET /api/v1/dashboard?baby_id={baby_id} -> Status: {status}")
    if status == 200:
        print(f"   [+] Milk Intake: {dashboard['milk_intake']['current']} / {dashboard['milk_intake']['target']} ml")
        print(f"   [+] Sleep Duration: {dashboard['sleep_duration']['current']} / {dashboard['sleep_duration']['target']} mins")
        print(f"   [+] Diaper Changes: {dashboard['diaper_changes']['current']} / {dashboard['diaper_changes']['target']}")
        print(f"   [+] Nap Timer Running: {dashboard['nap_timer_running']}")
        print(f"   [+] Medications due: {dashboard['medications_due']}")
        if dashboard.get('safety_alert'):
            print(f"   [+] Safety Alert level: {dashboard['safety_alert']['level']} - {dashboard['safety_alert']['message']}")
        if dashboard.get('growth_snapshot'):
            print(f"   [+] Growth Snapshot: {dashboard['growth_snapshot']['weight_kg']} kg, {dashboard['growth_snapshot']['height_cm']} cm")
        if dashboard.get('ai_tip'):
            print(f"   [+] AI Tip of the day: [{dashboard['ai_tip']['category']}] {dashboard['ai_tip']['content']}")
        print(f"   [+] Activity Stream items: {len(dashboard['activity_stream'])}")
    else:
        print(f"   [-] Error: {dashboard}")

    # 3. GET /api/v1/growth/measurements
    status, measurements = make_request(f"/api/v1/growth/measurements?baby_id={baby_id}")
    print(f"\n3. GET /api/v1/growth/measurements?baby_id={baby_id} -> Status: {status}")
    if status == 200:
        print(f"   [+] Found {len(measurements)} measurements.")
        for m in measurements[:2]:
            print(f"       - Age: {m['age_months']} months, Weight: {m['weight']} kg, Height: {m['height']} cm, Date: {m['date']}")
    else:
        print(f"   [-] Error: {measurements}")

    # 4. GET /api/v1/nutrition/feeds
    status, feeds = make_request(f"/api/v1/nutrition/feeds?baby_id={baby_id}")
    print(f"\n4. GET /api/v1/nutrition/feeds?baby_id={baby_id} -> Status: {status}")
    if status == 200:
        print(f"   [+] Found {len(feeds)} nutrition feeds.")
        for f in feeds[:2]:
            print(f"       - Type: {f['type']}, Details: {f['details']}, Amount: {f['amount']} ml, Time: {f['time']}")
    else:
        print(f"   [-] Error: {feeds}")

    # 5. GET /api/v1/nutrition/ingredients
    status, ingredients = make_request(f"/api/v1/nutrition/ingredients?baby_id={baby_id}")
    print(f"\n5. GET /api/v1/nutrition/ingredients?baby_id={baby_id} -> Status: {status}")
    if status == 200:
        print(f"   [+] Found {len(ingredients)} ingredients.")
        for i in ingredients[:2]:
            print(f"       - Name: {i['name']}, Reaction: {i['reaction']}, Date: {i['date']}")
    else:
        print(f"   [-] Error: {ingredients}")

    # 6. GET /api/v1/guardians
    status, guardians = make_request(f"/api/v1/guardians?baby_id={baby_id}")
    print(f"\n6. GET /api/v1/guardians?baby_id={baby_id} -> Status: {status}")
    if status == 200:
        print(f"   [+] Found {len(guardians)} guardians.")
        for g in guardians:
            print(f"       - Name: {g['name']}, Email: {g['email']}, Role: {g['role']}, Status: {g['status']}")
    else:
        print(f"   [-] Error: {guardians}")

    # 7. GET /api/v1/babies/{baby_id}/medication
    status, medications = make_request(f"/api/v1/babies/{baby_id}/medication")
    print(f"\n7. GET /api/v1/babies/{baby_id}/medication -> Status: {status}")
    if status == 200:
        print(f"   [+] Found {len(medications)} medication logs.")
        for m in medications[:2]:
            print(f"       - Name: {m['medication_name']}, Dosage: {m['dosage']}, Logged At: {m['logged_at']}")
    else:
        print(f"   [-] Error: {medications}")

    # 8. GET /api/v1/health/dashboard
    status, health_db = make_request(f"/api/v1/health/dashboard?baby_id={baby_id}")
    print(f"\n8. GET /api/v1/health/dashboard?baby_id={baby_id} -> Status: {status}")
    if status == 200:
        print(f"   [+] Safety Alert: [{health_db['safety_alert']['level']}] {health_db['safety_alert']['message']}")
        if health_db.get('countdown_widget'):
            print(f"   [+] Next eligible dose of {health_db['countdown_widget']['medication_name']}: {health_db['countdown_widget']['next_eligible_time']}")
            print(f"   [+] Is administer disabled: {health_db['countdown_widget']['is_administer_disabled']}")
    else:
        print(f"   [-] Error: {health_db}")

    # 9. GET /api/v1/ai/threads
    status, threads = make_request("/api/v1/ai/threads")
    print(f"\n9. GET /api/v1/ai/threads -> Status: {status}")
    if status == 200:
        print(f"   [+] Found {len(threads)} threads.")
        for t in threads[:2]:
            print(f"       - Thread ID: {t['id']}, Title: {t['title']}, Last Updated: {t['last_updated']}")
        thread_id = threads[0]["id"]
        
        # 10. GET /api/v1/ai/threads/{thread_id}/messages
        status, messages = make_request(f"/api/v1/ai/threads/{thread_id}/messages")
        print(f"\n10. GET /api/v1/ai/threads/{thread_id}/messages -> Status: {status}")
        if status == 200:
            print(f"   [+] Found {len(messages)} messages in thread '{thread_id}'.")
            for m in messages[:2]:
                print(f"       - Role: {m['role']}, Content snippet: {m['content'][:60]}...")
        else:
            print(f"   [-] Error: {messages}")
    else:
        print(f"   [-] Error: {threads}")

if __name__ == "__main__":
    run_tests()
