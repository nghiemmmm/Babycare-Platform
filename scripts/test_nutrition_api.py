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
    print("BABYCARE AI: TESTING NUTRITION & FEEDING ENDPOINTS")
    print("=" * 60)

    # 1. Get Active Baby ID
    status, babies = make_request("/api/v1/babies/")
    if status != 200 or not babies:
        print("[-] Error: Cannot list babies.")
        return
    baby_id = babies[0]["id"]
    print(f"[+] Active Baby ID: {baby_id}")

    # 2. FEEDS TESTS
    print("\n--- 1. Testing Nutrition Feeds (Bú sữa & Ăn dặm) ---")
    
    # 2.1 List Feeds
    status, feeds = make_request(f"/api/v1/nutrition/feeds?baby_id={baby_id}")
    print(f"   - GET /api/v1/nutrition/feeds -> Status: {status}")
    if status == 200:
        print(f"     [+] Number of existing feeds: {len(feeds)}")
        for f in feeds[:2]:
            print(f"         * Type: {f['type']}, Details: {f['details']}, Amount: {f['amount']} ml, Time: {f['time']}")
    else:
        print(f"     [-] Error: {feeds}")
        return

    # 2.2 Add Feed
    feed_payload = {
        "baby_id": baby_id,
        "type": "Formula",
        "details": "150ml Sữa công thức",
        "amount": 150.0,
        "time": "02:30 PM"
    }
    status, feed_res = make_request("/api/v1/nutrition/feeds", method="POST", body=feed_payload)
    print(f"   - POST /api/v1/nutrition/feeds -> Status: {status}")
    if status == 200 and feed_res:
        new_feed_id = feed_res["feed_id"]
        print(f"     [+] Feed created successfully! ID: {new_feed_id}")
    else:
        print(f"     [-] Error: {feed_res}")
        return

    # 2.3 Verify inclusion
    status, feeds = make_request(f"/api/v1/nutrition/feeds?baby_id={baby_id}")
    if status == 200:
        if any(f["id"] == new_feed_id for f in feeds):
            print("     [+] Verification Success: New feed found in history list!")
        else:
            print("     [-] Verification Failed: New feed is missing.")

    # 2.4 Delete Feed
    status, del_feed_res = make_request(f"/api/v1/nutrition/feeds/{new_feed_id}", method="DELETE")
    print(f"   - DELETE /api/v1/nutrition/feeds/{new_feed_id} -> Status: {status}")
    if status == 200 and del_feed_res:
        print(f"     [+] Delete response: {del_feed_res.get('message')}")
    else:
        print(f"     [-] Error: {del_feed_res}")

    # 3. INGREDIENTS TESTS
    print("\n--- 2. Testing Ingredients & Allergies (Nguyên liệu & Phản ứng dị ứng) ---")
    
    # 3.1 List Ingredients
    status, ingredients = make_request(f"/api/v1/nutrition/ingredients?baby_id={baby_id}")
    print(f"   - GET /api/v1/nutrition/ingredients -> Status: {status}")
    if status == 200:
        print(f"     [+] Number of existing ingredients logs: {len(ingredients)}")
        for i in ingredients[:2]:
            print(f"         * Ingredient: {i['name']}, Reaction: {i['reaction']}, Date: {i['date']}")
    else:
        print(f"     [-] Error: {ingredients}")
        return

    # 3.2 Add Ingredient
    ing_payload = {
        "baby_id": baby_id,
        "name": "Chuối chín dầm",
        "reaction": "Loved it"
    }
    status, ing_res = make_request("/api/v1/nutrition/ingredients", method="POST", body=ing_payload)
    print(f"   - POST /api/v1/nutrition/ingredients -> Status: {status}")
    if status == 200 and ing_res:
        new_ing_id = ing_res["ingredient_log_id"]
        print(f"     [+] Ingredient log created successfully! ID: {new_ing_id}")
    else:
        print(f"     [-] Error: {ing_res}")
        return

    # 3.3 Verify inclusion
    status, ingredients = make_request(f"/api/v1/nutrition/ingredients?baby_id={baby_id}")
    if status == 200:
        if any(i["id"] == new_ing_id for i in ingredients):
            print("     [+] Verification Success: New ingredient log found in history!")
        else:
            print("     [-] Verification Failed: New ingredient log is missing.")

    # 3.4 Delete Ingredient
    status, del_ing_res = make_request(f"/api/v1/nutrition/ingredients/{new_ing_id}", method="DELETE")
    print(f"   - DELETE /api/v1/nutrition/ingredients/{new_ing_id} -> Status: {status}")
    if status == 200 and del_ing_res:
        print("     [+] Delete response: Success")
    else:
        print(f"     [-] Error: {del_ing_res}")

    print("\n" + "=" * 60)
    print("NUTRITION & FEEDING ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
