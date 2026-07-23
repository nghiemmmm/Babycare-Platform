"""
RAG Retrieval Evaluation Script

Chạy một danh sách câu hỏi mẫu qua MedicalRetriever thật, kiểm tra nguồn tài liệu
kỳ vọng có xuất hiện trong top-k hay không. Không phải framework đánh giá phức tạp -
chỉ để phát hiện sớm khi corpus/chunking/domain filter làm giảm chất lượng truy hồi.

Usage: python -m app.AI_agents.knowledge.eval_retrieval
"""

CASES = [
    {
        "query": "Bé 6 tháng có nên ăn mật ong không?",
        "domain": "allergy_safety",
        "expect_source_contains": "di_ung",
    },
    {
        "query": "Dấu hiệu dị ứng đậu phộng ở trẻ nhỏ là gì?",
        "domain": "allergy_safety",
        "expect_source_contains": "di_ung",
    },
    {
        "query": "Bé bị tiêu chảy nên ăn gì?",
        "domain": "illness_diet",
        "expect_source_contains": "dinh_duong_khi_om",
    },
    {
        "query": "Dinh dưỡng cho bé đang bị viêm phổi",
        "domain": "illness_diet",
        "expect_source_contains": "VIEM_PHOI",
    },
    {
        "query": "Bé sốt thì nên cho ăn uống thế nào?",
        "domain": "illness_diet",
        "expect_source_contains": "dinh_duong_khi_om",
    },
    {
        "query": "Thực đơn ăn dặm cho bé 8 tháng tuổi",
        "domain": "nutrition_general",
        "expect_source_contains": "chedoandam",
    },
    {
        "query": "Khi nào bắt đầu cho bé ăn dặm bổ sung",
        "domain": "nutrition_general",
        "expect_source_contains": "chedoandam",
    },
    {
        "query": "Bé quấy khóc dạ đề phải làm sao?",
        "domain": None,
        "expect_source_contains": "parenting_guidelines",
    },
]


def main():
    from app.AI_agents.knowledge.retriever import MedicalRetriever

    retriever = MedicalRetriever()
    passed = 0
    for case in CASES:
        docs = retriever.pipeline.retrieve(case["query"], k=3, domain=case["domain"])
        sources = [d.metadata.get("source", "") for d in docs]
        found = any(case["expect_source_contains"].lower() in s.lower() for s in sources)
        status = "OK" if found else "MISS"
        if found:
            passed += 1
        print(f"[{status}] domain={case['domain']} | \"{case['query']}\"")
        print(f"       kỳ vọng chứa: {case['expect_source_contains']!r} | top-k sources: {sources}")

    print(f"\n{passed}/{len(CASES)} case đạt.")


if __name__ == "__main__":
    main()
