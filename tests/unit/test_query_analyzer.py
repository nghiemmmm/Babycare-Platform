import pytest
import asyncio
from app.AI_agents.knowledge.query_analyzer import QueryAnalyzer, SearchPlan
from app.AI_agents.knowledge.rag_pipeline import compact_and_budget_context
from langchain_core.documents import Document

def test_query_analyzer_basic():
    async def run_test():
        analyzer = QueryAnalyzer()
        plan = await analyzer.analyze("Bé 6 tháng sốt 38.5 độ uống Hapacol 150mg được không?", domain_hint="health")
        assert isinstance(plan, SearchPlan)
        assert plan.dense_query != ""
        assert len(plan.keywords) > 0
    asyncio.run(run_test())


def test_compact_and_budget_context():
    docs = [
        Document(page_content="Hapacol 150mg dùng cho trẻ từ 10-15kg.", metadata={"source": "WHO Guidelines"}),
        Document(page_content="Không dùng quá 4 lần một ngày đối với paracetamol.", metadata={"source": "Bộ Y Tế"})
    ]
    plan = SearchPlan(intent="HEALTH", keywords=["hapacol"], dense_query="hapacol 150mg")
    compacted = compact_and_budget_context(docs, plan=plan, max_tokens=100)
    assert "Hapacol 150mg" in compacted
    assert "WHO Guidelines" in compacted
