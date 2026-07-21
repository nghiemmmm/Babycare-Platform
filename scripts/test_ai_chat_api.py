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
    print("BABYCARE AI: TESTING AI AGENT & CHAT ROOM ENDPOINTS")
    print("=" * 60)

    # 1. Get Active Baby ID
    status, babies = make_request("/api/v1/babies/")
    if status != 200 or not babies:
        print("[-] Error: Cannot list babies.")
        return
    baby_id = babies[0]["id"]
    print(f"[+] Active Baby ID: {baby_id}")

    # 2. LIST THREADS (GET /api/v1/ai/threads)
    print("\n1. GET /api/v1/ai/threads (List active chat sessions)")
    status, threads = make_request("/api/v1/ai/threads")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Number of existing threads: {len(threads)}")
        for t in threads:
            print(f"       - ID: {t['id']}, Title: {t['title']}, Last Updated: {t['last_updated']}")
    else:
        print(f"   [-] Error: {threads}")
        return

    # 3. CREATE NEW THREAD (POST /api/v1/ai/threads)
    print("\n2. POST /api/v1/ai/threads (Create a new chat session)")
    status, new_thread = make_request("/api/v1/ai/threads", method="POST")
    print(f"   Status: {status}")
    if status == 200 and new_thread:
        new_thread_id = new_thread["thread_id"]
        print(f"   [+] Created Thread successfully!")
        print(f"       - Thread ID: {new_thread_id}")
        print(f"       - Initial Title: {new_thread['title']}")
    else:
        print(f"   [-] Error creating thread: {new_thread}")
        return

    # 4. SEND GENERAL MESSAGE (POST /api/v1/ai/threads/{thread_id}/messages)
    print(f"\n3. POST /api/v1/ai/threads/{new_thread_id}/messages (Ask AI consultation)")
    msg_payload_1 = {
        "content": "Bé nhà em 6 tháng tuổi, hôm nay tập ngồi tựa lưng được 10 phút. Có nên cho bé ngồi lâu hơn không?"
    }
    status, chat_res_1 = make_request(
        f"/api/v1/ai/threads/{new_thread_id}/messages",
        method="POST",
        body=msg_payload_1
    )
    print(f"   Status: {status}")
    if status == 200 and chat_res_1:
        ai_resp = chat_res_1["ai_response"]
        print(f"   [+] AI Response: {ai_resp['content'][:150]}...")
        if ai_resp.get("citations"):
            print(f"   [+] Citations count: {len(ai_resp['citations'])}")
    else:
        print(f"   [-] Error sending message: {chat_res_1}")

    # 5. SEND LOGGING MESSAGE (POST /api/v1/ai/threads/{thread_id}/messages -> triggers Smart Extraction)
    print(f"\n4. POST /api/v1/ai/threads/{new_thread_id}/messages (Log feeding via chat - expect extraction)")
    msg_payload_2 = {
        "content": "Ghi nhận bé uống 180ml sữa công thức lúc 10:30 SA"
    }
    status, chat_res_2 = make_request(
        f"/api/v1/ai/threads/{new_thread_id}/messages",
        method="POST",
        body=msg_payload_2
    )
    print(f"   Status: {status}")
    if status == 200 and chat_res_2:
        ai_resp = chat_res_2["ai_response"]
        extracted = chat_res_2.get("extracted_logs", [])
        print(f"   [+] AI Response: {ai_resp['content'][:150]}...")
        print(f"   [+] Extracted Logs Count: {len(extracted)}")
        for log in extracted:
            print(f"       * Type: {log['type']}, Title: {log['title']}, Detail: {log['detail']}, Value: {log['value']}")
    else:
        print(f"   [-] Error sending message: {chat_res_2}")

    # 6. GET MESSAGES (GET /api/v1/ai/threads/{thread_id}/messages)
    print(f"\n5. GET /api/v1/ai/threads/{new_thread_id}/messages (Verify messages list from checkpointer)")
    status, messages = make_request(f"/api/v1/ai/threads/{new_thread_id}/messages")
    print(f"   Status: {status}")
    if status == 200:
        print(f"   [+] Number of saved messages: {len(messages)}")
        for m in messages:
            print(f"       - [{m['role'].upper()}] {m['content'][:80]}...")
    else:
        print(f"   [-] Error: {messages}")

    # 7. SLEEP TIMER TESTS
    print("\n--- 3. Testing Sleep Timer (Bấm giờ ngủ) ---")
    
    # 7.1 Start Timer
    timer_payload_start = {
        "baby_id": baby_id,
        "action": "start"
    }
    status, start_timer_res = make_request("/api/v1/ai/sleep/timer", method="POST", body=timer_payload_start)
    print(f"   - POST /api/v1/ai/sleep/timer (Start) -> Status: {status}")
    if status == 200 and start_timer_res:
        print(f"     [+] Timer started successfully! Status: {start_timer_res['status']}")
    else:
        print(f"     [-] Error: {start_timer_res}")
        return

    # 7.2 Stop Timer & Save Log
    timer_payload_stop = {
        "baby_id": baby_id,
        "action": "stop"
    }
    status, stop_timer_res = make_request("/api/v1/ai/sleep/timer", method="POST", body=timer_payload_stop)
    print(f"   - POST /api/v1/ai/sleep/timer (Stop) -> Status: {status}")
    if status == 200 and stop_timer_res:
        print(f"     [+] Timer stopped successfully! Status: {stop_timer_res['status']}")
    else:
        print(f"     [-] Error: {stop_timer_res}")

    print("\n" + "=" * 60)
    print("AI AGENT & CHAT ROOM ENDPOINTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
