import sys
import os
import asyncio

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.modules.ai_agent.router import list_chat_threads, get_thread_messages
from app.modules.auth.schemas import UserRecord

async def test_chat_history():
    user = UserRecord(uid="rQ9CEPszK8PpG0vwIQgDIou5buI2", email="nghiem@babycare.com", name="Minh Anh")
    print("=== FETCHING CHAT THREADS FOR DEMO USER ===")
    threads = await list_chat_threads(user)
    print(f"Total threads returned: {len(threads)}")
    for t in threads:
        print(f" - Thread ID: {t.id} | Title: {t.title} | Last Updated: {t.last_updated}")
        try:
            msgs = await get_thread_messages(t.id, user)
            print(f"   -> Messages count: {len(msgs)}")
            for m in msgs:
                print(f"      [{m.role}] {m.content[:60]}... ({m.timestamp})")
        except Exception as e:
            print(f"   -> ERROR fetching messages for thread {t.id}: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_history())
