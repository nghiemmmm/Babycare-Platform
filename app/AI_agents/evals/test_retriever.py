import os
import json
import anyio
from app.AI_agents.knowledge.retriever import MedicalRetriever
from app.AI_agents.evals.evaluator import LLMJudge

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass

async def main():
    safe_print("=== DANH GIA CHAT LUONG RETRIEVER ===")
    
    # Doc Golden Dataset
    dataset_path = "tests/data/golden_dataset.json"
    if not os.path.exists(dataset_path):
        safe_print(f"Loi: Khong tim thay file du lieu chuan tai {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    retriever = MedicalRetriever()
    judge = LLMJudge()

    results = []
    
    total_hit_at_3 = 0.0
    total_mrr = 0.0
    total_recall_at_5 = 0.0
    total_context_precision = 0.0
    total_context_recall = 0.0
    retriever_count = 0

    # Loc ra cac test case co expected_context_keywords (la cac test case su dung RAG)
    rag_cases = [c for c in test_cases if len(c.get("expected_context_keywords", [])) > 0]
    total_cases = len(rag_cases)
    
    safe_print(f"Dang chay danh gia retriever tren {total_cases} kich ban RAG...")

    for idx, case in enumerate(rag_cases, 1):
        query = case["input_query"]
        expected_keywords = case.get("expected_context_keywords", [])
        expected_notes = case.get("expected_response_notes", "")
        
        safe_print(f"\n[{idx}/{total_cases}] Query: '{query}'")
        
        # 1. Retrieve chunks
        try:
            chunks_3 = retriever.pipeline.retrieve(query, k=3)
            chunks_5 = retriever.pipeline.retrieve(query, k=5)
        except Exception as e:
            safe_print(f"-> Loi truy xuat: {e}")
            continue

        if not chunks_3:
            safe_print("-> Khong tim thay chunks nao!")
            continue

        retriever_count += 1
        
        # 2. Hit@3
        hit = False
        for chunk in chunks_3:
            for kw in expected_keywords:
                if kw.lower() in chunk.page_content.lower():
                    hit = True
                    break
            if hit:
                break
        hit_at_3 = 1.0 if hit else 0.0
        total_hit_at_3 += hit_at_3

        # 3. MRR
        mrr_val = 0.0
        for rank, chunk in enumerate(chunks_3, 1):
            found = False
            for kw in expected_keywords:
                if kw.lower() in chunk.page_content.lower():
                    found = True
                    break
            if found:
                mrr_val = 1.0 / rank
                break
        mrr = mrr_val
        total_mrr += mrr

        # 4. Recall@5
        found_kws = set()
        for chunk in chunks_5:
            for kw in expected_keywords:
                if kw.lower() in chunk.page_content.lower():
                    found_kws.add(kw)
        recall_at_5 = len(found_kws) / len(expected_keywords) if len(expected_keywords) > 0 else 1.0
        total_recall_at_5 += recall_at_5

        # 5. Context Precision (LLM-as-a-Judge)
        relevant_count = 0
        precision_reasons = []
        for c_idx, chunk in enumerate(chunks_3, 1):
            try:
                prec_res = await judge.evaluate_chunk_relevance(query, chunk.page_content)
                is_rel = prec_res.get("relevant", False)
                if is_rel:
                    relevant_count += 1
                precision_reasons.append(f"Chunk {c_idx}: {'Hop le' if is_rel else 'Khong hop le'} ({prec_res.get('reason', '')})")
            except Exception as e:
                precision_reasons.append(f"Chunk {c_idx}: Error {str(e)}")
        context_precision = relevant_count / len(chunks_3) if len(chunks_3) > 0 else 0.0
        total_context_precision += context_precision

        # 6. Context Recall (LLM-as-a-Judge)
        combined_context_3 = "\n\n".join([f"Chunk {i}:\n{doc.page_content}" for i, doc in enumerate(chunks_3, 1)])
        try:
            rec_res = await judge.evaluate_context_recall(expected_notes, combined_context_3)
            context_recall = rec_res.get("score", 0.0)
            recall_reason = rec_res.get("reason", "")
        except Exception as e:
            context_recall = 0.0
            recall_reason = f"Error: {e}"
        total_context_recall += context_recall

        results.append({
            "id": idx,
            "query": query,
            "expected_keywords": expected_keywords,
            "hit_at_3": hit_at_3,
            "mrr": mrr,
            "recall_at_5": recall_at_5,
            "context_precision": context_precision,
            "context_precision_details": "; ".join(precision_reasons),
            "context_recall": context_recall,
            "context_recall_reason": recall_reason
        })
        
        safe_print(f"  -> Hit@3: {hit_at_3:.2f} | MRR: {mrr:.2f} | Recall@5: {recall_at_5:.2f}")
        safe_print(f"  -> Context Precision: {context_precision:.2f} | Context Recall: {context_recall:.2f}")

    avg_hit_at_3 = (total_hit_at_3 / retriever_count) if retriever_count > 0 else 0.0
    avg_mrr = (total_mrr / retriever_count) if retriever_count > 0 else 0.0
    avg_recall_at_5 = (total_recall_at_5 / retriever_count) if retriever_count > 0 else 0.0
    avg_context_precision = (total_context_precision / retriever_count) if retriever_count > 0 else 0.0
    avg_context_recall = (total_context_recall / retriever_count) if retriever_count > 0 else 0.0

    safe_print("\n=== KET QUA TONG QUAN RETRIEVER ===")
    safe_print(f"Average Hit@3: {avg_hit_at_3:.2f}")
    safe_print(f"Average MRR: {avg_mrr:.2f}")
    safe_print(f"Average Recall@5: {avg_recall_at_5:.2f}")
    safe_print(f"Average Context Precision: {avg_context_precision:.2f}")
    safe_print(f"Average Context Recall: {avg_context_recall:.2f}")

    # Ghi file bao cao
    report = f"""# Báo cáo Đánh giá Chất lượng Bộ truy xuất (Retriever Evaluation Report)

Báo cáo này tập trung đánh giá chất lượng của **MedicalRetriever (FAISS + BAAI/bge-m3)** sau khi đã tối ưu hóa kích thước phân mảnh (1500 ký tự).

---

## 📊 Chỉ số trung bình của Bộ truy xuất (Average Metrics)
* **Mean Hit@3**: `{avg_hit_at_3:.2f}` (Khả năng tìm thấy từ khóa chuẩn trong Top 3 tài liệu)
* **MRR (Mean Reciprocal Rank)**: `{avg_mrr:.2f}` (Xếp hạng nghịch đảo trung bình của kết quả đúng đầu tiên)
* **Recall@5**: `{avg_recall_at_5:.2f}` (Độ phủ của từ khóa trong Top 5 tài liệu)
* **Context Precision (Độ chính xác ngữ cảnh)**: `{avg_context_precision:.2f} / 1.0` (Tỷ lệ phân mảnh thực sự hữu ích được sắp xếp ở vị trí cao)
* **Context Recall (Độ phủ ngữ cảnh)**: `{avg_context_recall:.2f} / 1.0` (Khả năng bao phủ các thông tin mong đợi so với Ground Truth)

---

## 📝 Chi tiết đánh giá từng kịch bản RAG

| ID | Câu hỏi | Từ khóa mong đợi | Hit@3 | MRR | Recall@5 | Context Precision | Context Recall |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for r in results:
        report += f"| {r['id']} | {r['query']} | `{r['expected_keywords']}` | `{r['hit_at_3']:.2f}` | `{r['mrr']:.2f}` | `{r['recall_at_5']:.2f}` | `{r['context_precision']:.2f}` | `{r['context_recall']:.2f}` |\n"

    report += "\n## 🔍 Nhật ký giải thích chi tiết từ Giám khảo\n\n"
    for r in results:
        report += f"### Kịch bản {r['id']}: {r['query']}\n"
        report += f"* **Chi tiết Context Precision**: {r['context_precision_details']}\n"
        report += f"* **Chi tiết Context Recall**: Score: `{r['context_recall']:.2f}` - *{r['context_recall_reason']}*\n"
        report += "\n---\n\n"

    report_path = "tests/evaluation/retriever_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    safe_print(f"\nDa xuat bao cao tai {report_path}")

if __name__ == "__main__":
    anyio.run(main)
