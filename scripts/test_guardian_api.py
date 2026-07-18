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
    print("BABYCARE AI: TESTING GUARDIAN/FAMILY CIRCLE ENDPOINTS")
    print("=" * 60)

    # 1. Get Active Baby ID first
    status, babies = make_request("/api/v1/babies/")
    if status != 200 or not babies:
        print("[-] Error: Cannot list babies to find active baby ID.")
        return
    baby_id = babies[0]["id"]
    baby_name = babies[0]["name"]
    print(f"[+] Using Active Baby: {baby_name} (ID: {baby_id})")

    # 2. LIST GUARDIANS (GET /api/v1/guardians?baby_id=...)
    print(f"\n1. GET /api/v1/guardians?baby_id={baby_id} (List guardians circle)")
    status, guardians = make_request(f"/api/v1/guardians?baby_id={baby_id}")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Number of caregivers found: {len(guardians)}")
        for g in guardians:
            print(f"       - ID: {g['id']}, Name: {g['name']}, Email: {g['email']}, Role: {g['role']}, Status: {g['status']}")
    else:
        print(f"   [-] Error: {guardians}")
        return

    # 3. INVITE A NEW MEMBER (POST /api/v1/guardians/invite?baby_id=...)
    print(f"\n2. POST /api/v1/guardians/invite?baby_id={baby_id} (Invite Grandma Martha)")
    invite_payload = {
        "name": "Bà nội Martha",
        "email": "martha@family.com",
        "role": "GUARDIAN"
    }
    status, invite_res = make_request(
        f"/api/v1/guardians/invite?baby_id={baby_id}",
        method="POST",
        body=invite_payload
    )
    print(f"   Status: {status}")
    if status == 200 and invite_res:
        new_g_id = invite_res["invitation_id"]
        print(f"   [+] Invitation Success!")
        print(f"       - Invitation ID: {new_g_id}")
        print(f"       - Status: {invite_res['success']}")
    else:
        print(f"   [-] Error inviting member: {invite_res}")
        return

    # 4. LIST GUARDIANS AGAIN TO VERIFY INCLUSION
    print(f"\n3. GET /api/v1/guardians?baby_id={baby_id} (Verify list after invite)")
    status, guardians = make_request(f"/api/v1/guardians?baby_id={baby_id}")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Number of caregivers now: {len(guardians)}")
        found = False
        for g in guardians:
            print(f"       - Name: {g['name']}, Role: {g['role']}, Status: {g['status']}")
            if g["id"] == new_g_id:
                found = True
        if found:
            print("   [+] Verification Success: Invited member is present in the list!")
        else:
            print("   [-] Verification Failed: Invited member is missing from the list.")
    else:
        print(f"   [-] Error: {guardians}")

    # 5. REMOVE GUARDIAN (DELETE /api/v1/guardians/{guardian_id}?baby_id=...)
    print(f"\n4. DELETE /api/v1/guardians/{new_g_id}?baby_id={baby_id} (Remove Grandma Martha)")
    status, delete_res = make_request(
        f"/api/v1/guardians/{new_g_id}?baby_id={baby_id}",
        method="DELETE"
    )
    print(f"   Status: {status}")
    if status == 200 and delete_res:
        print(f"   [+] Deletion success message: {delete_res['message']}")
    else:
        print(f"   [-] Error removing member: {delete_res}")

    # 6. LIST GUARDIANS TO VERIFY REMOVAL
    print(f"\n5. GET /api/v1/guardians?baby_id={baby_id} (Confirm removal)")
    status, guardians = make_request(f"/api/v1/guardians?baby_id={baby_id}")
    if status == 200:
        print(f"   [+] Caregivers remaining: {len(guardians)}")
        if not any(g["id"] == new_g_id for g in guardians):
            print("   [+] Verification Success: Grandma Martha was removed from the list.")
        else:
            print("   [-] Verification Failed: Grandma Martha is still present.")
    else:
        print(f"   [-] Error: {guardians}")

    print("\n" + "=" * 60)
    print("GUARDIAN/FAMILY CIRCLE ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
