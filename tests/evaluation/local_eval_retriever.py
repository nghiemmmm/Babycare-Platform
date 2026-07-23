import os
import json
import anyio
from app.AI_agents.knowledge.retriever import MedicalRetriever

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass

async def main():
    safe_print("=== LOCAL RETRIEVER EVALUATION (COST-FREE) ===")
    
    # Read Golden Dataset
    dataset_path = "tests/data/golden_dataset.json"
    if not os.path.exists(dataset_path):
        safe_print(f"Error: Golden dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    retriever = MedicalRetriever()
    results = []
    
    # Filter cases that utilize RAG (non-empty expected_context_keywords)
    rag_cases = [c for c in test_cases if len(c.get("expected_context_keywords", [])) > 0]
    total_cases = len(rag_cases)
    
    if total_cases == 0:
        safe_print("No test cases with expected_context_keywords found.")
        return
        
    safe_print(f"Running evaluation on {total_cases} RAG test cases...")
    
    total_hit_at_1 = 0.0
    total_hit_at_3 = 0.0
    total_hit_at_5 = 0.0
    total_mrr = 0.0
    total_recall_at_3 = 0.0
    total_recall_at_5 = 0.0
    
    for idx, case in enumerate(rag_cases, 1):
        query = case["input_query"]
        expected_keywords = case.get("expected_context_keywords", [])
        
        safe_print(f"[{idx}/{total_cases}] Query: '{query}'")
        
        # Retrieve chunks
        try:
            chunks = retriever.pipeline.retrieve(query, k=5)
        except Exception as e:
            safe_print(f"  -> Retrieval error: {e}")
            continue
            
        if not chunks:
            safe_print("  -> No chunks retrieved.")
            results.append({
                "id": idx,
                "query": query,
                "expected_keywords": expected_keywords,
                "hit_at_1": 0.0,
                "hit_at_3": 0.0,
                "hit_at_5": 0.0,
                "mrr": 0.0,
                "recall_at_3": 0.0,
                "recall_at_5": 0.0,
                "retrieved_content": []
            })
            continue
            
        chunks_3 = chunks[:3]
        chunks_1 = chunks[:1]
        
        # 1. Hit@1
        hit_1 = any(any(kw.lower() in chunk.page_content.lower() for kw in expected_keywords) for chunk in chunks_1)
        hit_at_1 = 1.0 if hit_1 else 0.0
        total_hit_at_1 += hit_at_1
        
        # 2. Hit@3
        hit_3 = any(any(kw.lower() in chunk.page_content.lower() for kw in expected_keywords) for chunk in chunks_3)
        hit_at_3 = 1.0 if hit_3 else 0.0
        total_hit_at_3 += hit_at_3

        # 3. Hit@5
        hit_5 = any(any(kw.lower() in chunk.page_content.lower() for kw in expected_keywords) for chunk in chunks)
        hit_at_5 = 1.0 if hit_5 else 0.0
        total_hit_at_5 += hit_at_5

        # 4. MRR
        mrr_val = 0.0
        for rank, chunk in enumerate(chunks, 1):
            if any(kw.lower() in chunk.page_content.lower() for kw in expected_keywords):
                mrr_val = 1.0 / rank
                break
        mrr = mrr_val
        total_mrr += mrr

        # 5. Recall@3
        found_kws_3 = set()
        for chunk in chunks_3:
            for kw in expected_keywords:
                if kw.lower() in chunk.page_content.lower():
                    found_kws_3.add(kw)
        recall_at_3 = len(found_kws_3) / len(expected_keywords) if len(expected_keywords) > 0 else 1.0
        total_recall_at_3 += recall_at_3

        # 6. Recall@5
        found_kws_5 = set()
        for chunk in chunks:
            for kw in expected_keywords:
                if kw.lower() in chunk.page_content.lower():
                    found_kws_5.add(kw)
        recall_at_5 = len(found_kws_5) / len(expected_keywords) if len(expected_keywords) > 0 else 1.0
        total_recall_at_5 += recall_at_5
        
        results.append({
            "id": idx,
            "query": query,
            "expected_keywords": expected_keywords,
            "hit_at_1": hit_at_1,
            "hit_at_3": hit_at_3,
            "hit_at_5": hit_at_5,
            "mrr": mrr,
            "recall_at_3": recall_at_3,
            "recall_at_5": recall_at_5,
            "retrieved_content": [c.page_content for c in chunks_3]
        })
        
        safe_print(f"  -> Hit@1: {hit_at_1:.2f} | Hit@3: {hit_at_3:.2f} | Hit@5: {hit_at_5:.2f} | MRR: {mrr:.2f} | Recall@5: {recall_at_5:.2f}")

    avg_hit_at_1 = total_hit_at_1 / total_cases
    avg_hit_at_3 = total_hit_at_3 / total_cases
    avg_hit_at_5 = total_hit_at_5 / total_cases
    avg_mrr = total_mrr / total_cases
    avg_recall_at_3 = total_recall_at_3 / total_cases
    avg_recall_at_5 = total_recall_at_5 / total_cases
    
    safe_print("\n=== OVERALL LOCAL RETRIEVER RESULTS ===")
    safe_print(f"Mean Hit@1: {avg_hit_at_1:.2f}")
    safe_print(f"Mean Hit@3: {avg_hit_at_3:.2f}")
    safe_print(f"Mean Hit@5: {avg_hit_at_5:.2f}")
    safe_print(f"Mean Reciprocal Rank (MRR): {avg_mrr:.2f}")
    safe_print(f"Mean Recall@3: {avg_recall_at_3:.2f}")
    safe_print(f"Mean Recall@5: {avg_recall_at_5:.2f}")

    # Generate Markdown Report
    report = f"""# Báo cáo Đánh giá Bộ truy xuất Cục bộ (Local Retriever Evaluation Report)

Báo cáo này đánh giá chất lượng của **MedicalRetriever (FAISS + BAAI/bge-m3)** cục bộ bằng các chỉ số định lượng toán học (không dùng LLM-as-a-Judge) để tiết kiệm chi phí API.

---

## 📊 Chỉ số Trung bình Hệ thống (Average Metrics)
* **Mean Hit@1**: `{avg_hit_at_1:.2f}` (Tỷ lệ tìm thấy từ khóa chuẩn trong kết quả đầu tiên)
* **Mean Hit@3**: `{avg_hit_at_3:.2f}` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 3)
* **Mean Hit@5**: `{avg_hit_at_5:.2f}` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 5)
* **MRR (Mean Reciprocal Rank)**: `{avg_mrr:.2f}` (Xếp hạng nghịch đảo trung bình của kết quả khớp từ khóa đầu tiên)
* **Mean Recall@3**: `{avg_recall_at_3:.2f}` (Độ phủ của từ khóa trong Top 3 tài liệu)
* **Mean Recall@5**: `{avg_recall_at_5:.2f}` (Độ phủ của từ khóa trong Top 5 tài liệu)

---

## 📝 Chi tiết Đánh giá Từng Kịch bản

| ID | Câu hỏi của Phụ huynh | Từ khóa mong đợi | Hit@1 | Hit@3 | Hit@5 | MRR | Recall@3 | Recall@5 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for r in results:
        report += f"| {r['id']} | {r['query']} | `{r['expected_keywords']}` | `{r['hit_at_1']:.2f}` | `{r['hit_at_3']:.2f}` | `{r['hit_at_5']:.2f}` | `{r['mrr']:.2f}` | `{r['recall_at_3']:.2f}` | `{r['recall_at_5']:.2f}` |\n"

    report += "\n## 🔍 Nhật ký Nội dung Truy xuất chi tiết (Top 3 Chunks)\n\n"
    for r in results:
        report += f"### Kịch bản {r['id']}: {r['query']}\n"
        report += f"* **Từ khóa mong đợi**: `{r['expected_keywords']}`\n"
        report += f"* **Nội dung các phân mảnh truy xuất được (Top 3)**:\n"
        for i, chunk in enumerate(r['retrieved_content'], 1):
            # Clean newlines for markdown display
            cleaned_chunk = chunk.replace('\n', ' ')
            report += f"  {i}. \"{cleaned_chunk[:200]}...\"\n"
        report += "\n---\n\n"

    report_path = "tests/evaluation/local_retriever_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    safe_print(f"\nBáo cáo đã được xuất thành công tại: {report_path}")

if __name__ == "__main__":
    anyio.run(main)
