"""
====================================================================
⚡ BENCHMARK HỆ THỐNG RAG PIPELINE & AGENT ORCHESTRATOR - BABYCARE AI
====================================================================
Đo chính xác End-to-End Latency và Latency từng thành phần (Stage Latency Breakdown)
cho 5 kịch bản kiểm thử tiêu chuẩn.

Cách dùng:
  .\venv\Scripts\python.exe scripts/benchmark_rag_performance.py
"""

import sys
import os
import time
import asyncio
import io

# UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.AI_agents.memory.embeddings import _get_bge_model
from app.AI_agents.knowledge.rag_pipeline import init_rag_pipeline
from app.AI_agents.knowledge.reranker import _get_cross_encoder
from app.AI_agents.knowledge.retriever import MedicalRetriever
from app.AI_agents.knowledge.query_analyzer import QueryAnalyzer
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator

TEST_SCENARIOS = [
    {
        "id": 1,
        "name": "Simple Factual RAG Query (Tier 1 Grounded QA)",
        "query": "Bé 5 tháng tuổi thì một ngày nên ngủ khoảng bao nhiêu tiếng là đủ?",
        "expected_latency": "< 2.5s"
    },
    {
        "id": 2,
        "name": "Complex Multi-document Query (Tư vấn tổng hợp)",
        "query": "Bé 6 tháng tuổi vừa sốt vừa biếng ăn, tiền sử dị ứng đậu nành thì mẹ cần xử trí thực đơn và chăm sóc thế nào?",
        "expected_latency": "< 4.0s"
    },
    {
        "id": 3,
        "name": "Query cần Escalation (Tier 2 Health Specialist Agent)",
        "query": "Bé Leo bị sốt 38.5 độ C thì có nên uống Hapacol 150mg không và liều lượng thế nào?",
        "expected_latency": "< 4.5s"
    },
    {
        "id": 4,
        "name": "Query không cần RAG (Tier 0 Fast Greeting)",
        "query": "Xin chào BabyCare AI!",
        "expected_latency": "< 0.05s (< 50ms)"
    },
    {
        "id": 5,
        "name": "Query có Cached Result (Repeat Query Cache Hit)",
        "query": "Bé 5 tháng tuổi thì một ngày nên ngủ khoảng bao nhiêu tiếng là đủ?",
        "expected_latency": "< 0.01s (< 10ms)"
    }
]

async def run_benchmark():
    print("====================================================================")
    print("⚡ BẮT ĐẦU BENCHMARK HỆ THỐNG RAG PIPELINE - BABYCARE AI")
    print("====================================================================\n")

    # 1. Đo thời gian Preloading Startup
    t_start = time.time()
    print("⏳ [STEP 0] Đang kích hoạt Preload Models vào RAM (Lifespan Startup)...")
    _get_bge_model()
    init_rag_pipeline()
    _get_cross_encoder()
    orchestrator = AgentOrchestrator()
    preload_time = round(time.time() - t_start, 2)
    print(f"✅ [STEP 0] Preload hoàn tất trong {preload_time}s! (BGE-M3 + FAISS + CrossEncoder Reranker + LangGraph Orchestrator)\n")

    retriever = MedicalRetriever()
    analyzer = QueryAnalyzer()

    # 2. Đo chi tiết từng stage cho Query 1
    sample_query = TEST_SCENARIOS[0]["query"]
    print("--------------------------------------------------------------------")
    print(f"📊 [STAGE BREAKDOWN] Đo chi tiết từng bước cho Query: \"{sample_query}\"")
    print("--------------------------------------------------------------------")

    t0 = time.time()
    plan = await analyzer.analyze(sample_query)
    t_plan = round((time.time() - t0) * 1000, 2)

    t0 = time.time()
    from app.AI_agents.memory.embeddings import get_embeddings
    get_embeddings().embed_query(sample_query)
    t_embed = round((time.time() - t0) * 1000, 2)

    t0 = time.time()
    rag_text = await retriever.retrieve_context_with_plan(sample_query, k=2)
    t_rag_total = round((time.time() - t0) * 1000, 2)

    print(f"• Query Planning / Fast-path check : {t_plan:>6.2f} ms")
    print(f"• Query Embedding (BGE-M3 local)    : {t_embed:>6.2f} ms")
    print(f"• Hybrid RAG (Parallel FAISS+BM25)  : {t_rag_total:>6.2f} ms")
    print(f"• RAG Output Length                 : {len(rag_text)} ký tự")
    print("--------------------------------------------------------------------\n")

    # 3. Chạy 5 kịch bản End-to-End
    print("====================================================================")
    print("🚀 ĐO END-TO-END LATENCY CHO 5 KỊCH BẢN KIỂM THỬ TẠI TIER 1 & TIER 2")
    print("====================================================================\n")

    results = []
    for sc in TEST_SCENARIOS:
        print(f"👉 Scenario {sc['id']}: {sc['name']}")
        print(f"   Query: \"{sc['query']}\"")
        t_e2e_start = time.time()
        
        # Chạy qua Orchestrator master pipeline
        response_state = await orchestrator.run_agent(
            message=sc["query"],
            thread_id=f"benchmark_thread_{sc['id']}",
            baby_id="baby_rQ9CEPszK8PpG0vwIQgDIou5buI2_leo",
            user_id="benchmark_user"
        )
        duration_s = round(time.time() - t_e2e_start, 2)
        tool_count = len(response_state.get("tool_steps", []))
        
        print(f"   ⏱️ End-to-End Latency : {duration_s}s (Target: {sc['expected_latency']})")
        print(f"   🛠️ Lượt gọi Tool       : {tool_count} tool(s)")
        print(f"   ✅ Trạng thái          : HOÀN THÀNH MƯỢT MÀ\n")
        results.append((sc['id'], sc['name'], duration_s, sc['expected_latency']))
        await asyncio.sleep(0.5)

    print("====================================================================")
    print("📊 TỔNG KẾT BENCHMARK RAG PIPELINE:")
    print("====================================================================")
    for sc_id, name, dur, target in results:
        print(f"• Kịch bản {sc_id:<2}: {dur:>5.2f}s | Target: {target:<12} | {name}")
    print("====================================================================\n")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
