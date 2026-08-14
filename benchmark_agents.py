import sys
import asyncio
import time
import json
import logging
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator

# Force UTF-8 encoding for stdout
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO)

async def run_benchmarks():
    orchestrator = AgentOrchestrator()
    
    test_queries = [
        ("Health Single Domain", "Bé Leo bị sốt 38.5 độ, tư vấn giúp em"),
        ("Nutrition Single Domain", "Cho bé 6 tháng ăn dặm loại gì thì tốt?"),
        ("Activity Logging", "Ghi nhận bé vừa uống 150ml sữa công thức"),
        ("General Chat", "Chào bạn, bé nhà mình hôm nay thế nào?"),
        ("Cross Domain Hand-off", "Bé bị sốt 38.5 độ, mình vừa cho uống 150mg Hapacol")
    ]
    
    print("\n==================================================")
    print(" RUNNING ARCHITECTURE BENCHMARK SUITE ")
    print("==================================================\n")
    
    for name, query in test_queries:
        t0 = time.time()
        thread_id = f"bench_{int(t0)}"
        res = await orchestrator.run_agent(
            message=query,
            thread_id=thread_id,
            baby_id="mock_baby_123",
            user_id="mock_user_123"
        )
        elapsed = time.time() - t0
        tool_steps = res.get("tool_steps", [])
        
        print(f"[Benchmark Test]: {name}")
        print(f"   Query: \"{query}\"")
        print(f"   Total Execution Latency: {elapsed:.2f}s")
        print(f"   Tool Steps Count: {len(tool_steps)}")
        for step in tool_steps:
            print(f"     - [{step.get('tool_name')}] {step.get('display_name')} ({step.get('status')}) -> {step.get('result_summary')}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
