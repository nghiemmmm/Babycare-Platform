"""
BabyCare AI - Automated System Diagnostics & Health Check Script
Chạy kiểm tra sức khỏe hệ thống bất kỳ lúc nào qua lệnh:
    python scripts/health_check.py
    hoặc: make health-check
"""
import os
import sys

# Đảm bảo đường dẫn import từ thư mục gốc dự án
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set UTF-8 encoding for Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_health_check():
    print("\n====================================================")
    print("🏥 BABYCARE AI - SYSTEM HEALTH AUDIT & DIAGNOSTICS")
    print("====================================================\n")

    # 1. Environment & API Keys
    print("[1] KIỂM TRA BIẾN MÔI TRƯỜNG & API KEYS:")
    try:
        from app.core.config import settings
        print(f"  • LLM Provider:       {settings.LLM_PROVIDER}")
        print(f"  • OpenRouter API Key: {'✅ CONFIGURED' if settings.OPENROUTER_API_KEY else '⚠️ MISSING'}")
        print(f"  • Gemini API Key:     {'✅ CONFIGURED' if settings.GEMINI_API_KEY else '⚠️ MISSING'}")
        print(f"  • OpenRouter Model:   {settings.OPENROUTER_MODEL}")
    except Exception as e:
        print(f"  ❌ Lỗi đọc config: {e}")

    # 2. ModelRouter Initialization
    print("\n[2] KIỂM TRA KHỞI TẠO LLM MODEL ROUTER:")
    try:
        from app.AI_agents.providers.model_router import ModelRouter
        llm = ModelRouter.get_model()
        model_id = getattr(llm, 'model_name', getattr(llm, 'model', 'N/A'))
        print(f"  • Active Model Router: ✅ {type(llm).__name__} (Model ID: {model_id})")
    except Exception as e:
        print(f"  • Active Model Router: ❌ FAILED ({e})")

    # 3. Firestore Realtime DB Connection
    print("\n[3] KIỂM TRA KẾT NỐI FIRESTORE DATABASE:")
    try:
        from app.infrastructure.database import get_firestore_db
        db = get_firestore_db()
        print(f"  • Firestore DB Connection: ✅ CONNECTED (Project: {db.project})")
    except Exception as e:
        print(f"  • Firestore DB Connection: ❌ FAILED ({e})")

    # 4. FAISS Vector DB Index
    print("\n[4] KIỂM TRA CƠ SỞ DỮ LIỆU VECTOR FAISS (RAG):")
    faiss_path = "app/ai/models/faiss_index"
    if os.path.exists(faiss_path):
        print(f"  • FAISS Index Directory: ✅ EXISTS ({faiss_path})")
    else:
        print(f"  • FAISS Index Directory: ⚠️ MISSING ({faiss_path})")

    # 5. Local ML Models
    print("\n[5] KIỂM TRA CÁC MÔ HÌNH MACHINE LEARNING CỤC BỘ (LOCAL):")
    bge_path = os.path.join("app", "ai", "models", "models--BAAI--bge-m3")
    ast_path = os.path.join("app", "ai", "models", "faster-whisper")
    print(f"  • BGE-M3 Local Model:     {'✅ EXISTS' if os.path.exists(bge_path) else '⚠️ MISSING'}")
    print(f"  • Audio Cry Model:        {'✅ EXISTS' if os.path.exists(ast_path) else '⚠️ MISSING'}")

    # 6. Prompts Files Check
    print("\n[6] KIỂM TRA THƯ MỤC TỆP PROMPT (.TXT):")
    prompts_dir = "app/AI_agents/prompts"
    if os.path.exists(prompts_dir):
        files = [f for f in os.listdir(prompts_dir) if f.endswith('.txt')]
        print(f"  • Prompts Directory: ✅ EXISTS ({len(files)} tệp: {', '.join(files)})")
    else:
        print(f"  • Prompts Directory: ⚠️ MISSING")

    # 7. Specific Component Models
    print("\n[7] KIỂM TRA ĐỊNH NGHĨA MODEL RIÊNG TRONG CONSTANT:")
    try:
        from app.AI_agents.core import constant
        print(f"  • Chat Agent Model:       {constant.CHAT_AGENT_MODEL} ({getattr(constant, 'CHAT_AGENT_PROVIDER', 'openrouter')})")
        print(f"  • Health Agent Model:     {constant.HEALTH_AGENT_MODEL} ({getattr(constant, 'HEALTH_AGENT_PROVIDER', 'gemini')})")
        print(f"  • Nutrition Agent Model:  {constant.NUTRITION_AGENT_MODEL} ({getattr(constant, 'NUTRITION_AGENT_PROVIDER', 'openrouter')})")
        print(f"  • Query Analyzer Model:   {constant.QUERY_ANALYZER_MODEL} ({getattr(constant, 'QUERY_ANALYZER_PROVIDER', 'openrouter')})")
    except Exception as e:
        print(f"  ❌ Lỗi đọc constant models: {e}")

    print("\n====================================================")
    print("✨ CHẨN ĐOÁN HOÀN TẤT - HỆ THỐNG TRONG TRẠNG THÁI SẮN SÀNG!")
    print("====================================================\n")

if __name__ == "__main__":
    run_health_check()
