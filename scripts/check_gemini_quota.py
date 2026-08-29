"""
====================================================================
🛠 SCRIPT KIỂM TRA QUOTA & ĐỀ XUẤT MODEL THAY THẾ - BABYCARE AI
====================================================================
Kiểm tra xem các model đang được khai báo trong app/AI_agents/core/constant.py
có còn Quota hoạt động không. 
Nếu mô hình nào hết Quota (429) hoặc lỗi, script sẽ tự động quét danh sách các
mô hình dự phòng (Fallback Candidates) và đề xuất model thay thế khả dụng nhất!

Cách dùng:
  python scripts/check_gemini_quota.py
  hoặc: make check-quota
"""

import sys
import os
import time
import asyncio
import io

# Đảm bảo in UTF-8 mượt mà trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Tự động import cài đặt từ dự án BabyCare
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
    api_key = settings.GEMINI_API_KEY
except Exception:
    api_key = os.getenv("GEMINI_API_KEY", "")

if not api_key:
    print("❌ KHÔNG TÌM THẤY GEMINI_API_KEY trọn vẹn trong file .env!")
    sys.exit(1)

# Import các constant model từ app.AI_agents.core.constant
try:
    from app.AI_agents.core import constant as agent_const
except ImportError:
    import app.AI_agents.core.constant as agent_const

# Danh sách các hằng số cần kiểm tra trong constant.py
CONSTANTS_TO_CHECK = [
    ("DEFAULT_CHAT_MODEL", getattr(agent_const, "DEFAULT_CHAT_MODEL", "gemini-3.5-flash")),
    ("CHAT_AGENT_MODEL", getattr(agent_const, "CHAT_AGENT_MODEL", "gemini-3.5-flash")),
    ("HEALTH_AGENT_MODEL", getattr(agent_const, "HEALTH_AGENT_MODEL", "gemini-3.5-flash")),
    ("NUTRITION_AGENT_MODEL", getattr(agent_const, "NUTRITION_AGENT_MODEL", "gemini-3.5-flash")),
    ("OUT_OF_SCOPE_MODEL", getattr(agent_const, "OUT_OF_SCOPE_MODEL", "gemini-3.5-flash")),
    ("VOICE_LOGGING_MODEL", getattr(agent_const, "VOICE_LOGGING_MODEL", "gemini-3.5-flash")),
    ("QUERY_ANALYZER_MODEL", getattr(agent_const, "QUERY_ANALYZER_MODEL", "gemini-3.5-flash")),
    ("WEEKLY_REPORT_MODEL", getattr(agent_const, "WEEKLY_REPORT_MODEL", "gemini-3.5-flash")),
    ("CRY_ANALYSIS_MODEL", getattr(agent_const, "CRY_ANALYSIS_MODEL", "gemini-3.5-flash")),
    ("NUTRITION_RECOMMENDER_MODEL", getattr(agent_const, "NUTRITION_RECOMMENDER_MODEL", "gemini-3.5-flash")),
    ("TASK_PLANNER_MODEL", getattr(agent_const, "TASK_PLANNER_MODEL", "gemini-3.5-flash")),
]

# Danh sách candidate models để test thay thế nếu model chính hết Quota
FALLBACK_CANDIDATES = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-latest",
]

from langchain_google_genai import ChatGoogleGenerativeAI

async def test_model_quota(model_name: str) -> tuple[bool, str, int]:
    """Test 1 model cụ thể, trả về (is_healthy, detail_message, response_time_ms)."""
    t0 = time.time()
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0,
            timeout=12.0,
            max_retries=1
        )
        res = await llm.ainvoke("Ping")
        duration_ms = int((time.time() - t0) * 1000)
        return True, f"OK ({duration_ms}ms)", duration_ms
    except Exception as e:
        err_str = str(e)
        duration_ms = int((time.time() - t0) * 1000)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            return False, "429 HẾT QUOTA / RATE LIMIT", duration_ms
        elif "404" in err_str or "NOT_FOUND" in err_str:
            return False, "404 MODEL KHÔNG TỒN TẠI", duration_ms
        elif "401" in err_str or "UNAUTHENTICATED" in err_str:
            return False, "401 API KEY KHÔNG HỢP LỆ", duration_ms
        else:
            return False, f"LỖI KHÁC ({err_str[:60]}...)", duration_ms

async def main():
    print("====================================================================")
    print(f"🔑 GEMINI_API_KEY: {api_key[:10]}...{api_key[-4:]}")
    print("📌 KIỂM TRA QUOTA CÁC MODEL TRONG app/AI_agents/core/constant.py")
    print("====================================================================\n")

    # 1. Gom danh sách các model unique từ constant.py
    unique_declared_models = set(m for _, m in CONSTANTS_TO_CHECK)
    model_health_results = {}

    print("🔍 [BƯỚC 1] Đang kiểm tra tình trạng Quota các model đã khai báo trong constant.py...")
    for model_name in unique_declared_models:
        print(f"   ► Đang test model: [{model_name}]...", end="", flush=True)
        is_ok, msg, ms = await test_model_quota(model_name)
        model_health_results[model_name] = (is_ok, msg, ms)
        if is_ok:
            print(f" ✅ {msg}")
        else:
            print(f" ❌ {msg}")
        await asyncio.sleep(0.5)

    print("\n--------------------------------------------------------------------")
    print("📋 BẢNG TRẠNG THÁI HẰNG SỐ TRONG CONSTANT.PY:")
    print("--------------------------------------------------------------------")
    failed_constants = []
    for const_name, model_name in CONSTANTS_TO_CHECK:
        is_ok, msg, _ = model_health_results[model_name]
        status_icon = "✅ CÒN QUOTA" if is_ok else "❌ HẾT QUOTA / LỖI"
        print(f"• {const_name:<30} -> [{model_name}] : {status_icon} ({msg})")
        if not is_ok:
            failed_constants.append((const_name, model_name))

    # 2. Nếu có model bị lỗi/hết quota, tìm các Model Thay Thế khả dụng
    healthy_fallbacks = []
    if failed_constants:
        print("\n====================================================================")
        print("⚠️ PHÁT HIỆN MODEL HẾT QUOTA / LỖI! Đang Quét Tìm Model Thay Thế...")
        print("====================================================================\n")

        for candidate in FALLBACK_CANDIDATES:
            if candidate in model_health_results:
                is_ok, msg, ms = model_health_results[candidate]
            else:
                print(f"   ► Kiểm tra model dự phòng: [{candidate}]...", end="", flush=True)
                is_ok, msg, ms = await test_model_quota(candidate)
                model_health_results[candidate] = (is_ok, msg, ms)
                if is_ok:
                    print(f" ✅ {msg}")
                else:
                    print(f" ❌ {msg}")
                await asyncio.sleep(0.5)
            
            if is_ok:
                healthy_fallbacks.append((candidate, msg))

    # 3. Báo cáo & Khuyến nghị thay thế
    print("\n====================================================================")
    print("📊 TỔNG KẾT & ĐỀ XUẤT MODEL THAY THẾ:")
    print("====================================================================")

    if not failed_constants:
        print("🎉 TẤT CẢ MODEL KHAI BÁO TRONG CONSTANT.PY ĐỀU CÒN QUOTA TỐT!")
        print("Hệ thống BabyCare AI đang hoạt động bình thường, không cần thay thế.")
    else:
        print(f"🚨 Có {len(failed_constants)} hằng số model bị ảnh hưởng do hết quota hoặc lỗi:")
        for const_name, old_model in failed_constants:
            print(f"  ❌ {const_name} ([{old_model}])")
        
        print("\n💡 DANH SÁCH MODEL DỰ PHÒNG KHẢ DỤNG (CÒN QUOTA KHỎE):")
        if healthy_fallbacks:
            for idx, (fb_model, fb_msg) in enumerate(healthy_fallbacks, 1):
                print(f"  {idx}. [{fb_model}] -> {fb_msg}")
            
            best_recommendation = healthy_fallbacks[0][0]
            print(f"\n👉 GỢI Ý CẬP NHẬT TRONG app/AI_agents/core/constant.py:")
            print(f"   Thay thế model bị lỗi thành: \"{best_recommendation}\"")
        else:
            print("  🚨 KHÔNG TÌM THẤY Model dự phòng nào còn Quota trên Gemini API Key này!")
            print("  👉 Vui lòng tạo API Key mới tại: https://aistudio.google.dev/ và cập nhật file .env")

    print("====================================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
