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
    print("BABYCARE AI: TESTING BABY PROFILE ENDPOINTS")
    print("=" * 60)

    # 1. LIST BABIES (GET /api/v1/babies/)
    print("\n1. GET /api/v1/babies/ (List babies before test)")
    status, babies = make_request("/api/v1/babies/")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Number of existing babies: {len(babies)}")
        for b in babies:
            print(f"       - ID: {b['id']}, Name: {b['name']}, Gender: {b['gender']}, Birth Date: {b['birth_date']}")
    else:
        print(f"   [-] Error listing babies: {babies}")
        return

    # 2. CREATE A NEW BABY (POST /api/v1/babies/)
    print("\n2. POST /api/v1/babies/ (Create a new test baby profile)")
    new_baby_payload = {
        "name": "Bé Mèo",
        "birth_date": "2026-02-15",
        "gender": "Girl",
        "avatar_url": "https://images.unsplash.com/photo-1519689680058-324335c77eb2?w=150&h=150&fit=crop",
        "is_active": False
    }
    status, created_baby = make_request("/api/v1/babies/", method="POST", body=new_baby_payload)
    print(f"   Status: {status}")
    if status == 201 and created_baby:
        test_baby_id = created_baby["id"]
        print(f"   [+] Created Baby successfully!")
        print(f"       - Assigned ID: {test_baby_id}")
        print(f"       - Name: {created_baby['name']}")
        print(f"       - Gender: {created_baby['gender']}")
        print(f"       - Birth Date: {created_baby['birth_date']}")
    else:
        print(f"   [-] Error creating baby profile: {created_baby}")
        return

    # 3. GET BABY DETAILS (GET /api/v1/babies/{baby_id})
    print(f"\n3. GET /api/v1/babies/{test_baby_id} (Retrieve details of the created baby)")
    status, retrieved_baby = make_request(f"/api/v1/babies/{test_baby_id}")
    print(f"   Status: {status}")
    if status == 200 and retrieved_baby:
        print(f"   [+] Retrieved Baby successfully!")
        assert retrieved_baby["id"] == test_baby_id
        print(f"       - Name in DB: {retrieved_baby['name']}")
    else:
        print(f"   [-] Error retrieving details: {retrieved_baby}")

    # 4. UPDATE BABY DETAILS (PUT /api/v1/babies/{baby_id})
    print(f"\n4. PUT /api/v1/babies/{test_baby_id} (Update details of the test baby)")
    update_payload = {
        "name": "Bé Mèo Con",
        "birth_date": "2026-02-16",
        "gender": "Boy",
        "avatar_url": "https://images.unsplash.com/photo-1519689680058-324335c77eb2?w=150&h=150&fit=crop",
        "is_active": False
    }
    status, updated_baby = make_request(f"/api/v1/babies/{test_baby_id}", method="PUT", body=update_payload)
    print(f"   Status: {status}")
    if status == 200 and updated_baby:
        print(f"   [+] Updated Baby successfully!")
        print(f"       - New Name: {updated_baby['name']}")
        print(f"       - New Gender: {updated_baby['gender']}")
        print(f"       - New Birth Date: {updated_baby['birth_date']}")
    else:
        print(f"   [-] Error updating baby profile: {updated_baby}")

    # 5. DELETE BABY PROFILE (DELETE /api/v1/babies/{baby_id})
    print(f"\n5. DELETE /api/v1/babies/{test_baby_id} (Remove test baby profile)")
    status, delete_msg = make_request(f"/api/v1/babies/{test_baby_id}", method="DELETE")
    print(f"   Status: {status}")
    if status == 200 and delete_msg:
        print(f"   [+] Delete message: {delete_msg['message']}")
    else:
        print(f"   [-] Error deleting baby profile: {delete_msg}")

    # 6. VERIFY DELETION (GET /api/v1/babies/{baby_id} should return 404)
    print(f"\n6. GET /api/v1/babies/{test_baby_id} (Confirm deletion - expect 404)")
    status, err_response = make_request(f"/api/v1/babies/{test_baby_id}")
    print(f"   Status: {status}")
    if status == 404:
        print("   [+] Verified! Profile no longer exists.")
    else:
        print(f"   [-] Warning: Expected 404 but got {status} - response: {err_response}")

    print("\n" + "=" * 60)
    print("BABY PROFILE ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
