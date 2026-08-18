import os
import json
import anyio
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
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
    safe_print("=== Khoi dong he thong danh gia AI Agent ===")
    
    # Doc Golden Dataset
    dataset_path = "tests/data/golden_dataset.json"
    if not os.path.exists(dataset_path):
        safe_print(f"Loi: Khong tim thay file du lieu chuan tai {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    orchestrator = AgentOrchestrator()
    retriever = MedicalRetriever()
    judge = LLMJudge()

    results = []
    
    total_cases = len(test_cases)
    intent_correct = 0
    total_relevancy = 0.0
    total_faithfulness = 0.0
    faithfulness_count = 0
    
    # Retriever Quality Accumulators
    total_hit_at_3 = 0.0
    total_mrr = 0.0
    total_recall_at_5 = 0.0
    total_context_precision = 0.0
    total_context_recall = 0.0
    retriever_count = 0

    safe_print(f"Dang chay danh gia {total_cases} test cases...")

    for idx, case in enumerate(test_cases, 1):
        query = case["input_query"]
        expected_intent = case["expected_intent"]
        expected_keywords = case.get("expected_context_keywords", [])
        expected_notes = case.get("expected_response_notes", "")
        
        safe_print(f"\n[{idx}/{total_cases}] Query: '{query}'")
        
        thread_id = f"eval-thread-{idx}"
        baby_id = "baby-123" if "Bo" in query or expected_intent in ["check_health", "check_nutrition"] else None
        user_id = "user-123" if baby_id else None
        
        # 1. Run Agent
        try:
            state_result = await orchestrator.run_agent(
                message=query,
                thread_id=thread_id,
                baby_id=baby_id,
                user_id=user_id
            )
            actual_output = state_result["messages"][-1].content
            actual_intent = state_result.get("extracted_intent", "chat")
        except Exception as e:
            safe_print(f"-> Loi khi chay agent: {e}")
            continue

        # 2. Evaluate Intent
        intent_match = (actual_intent == expected_intent)
        if intent_match:
            intent_correct += 1
        
        # 3. Retrieve Context and Evaluate Retriever Quality
        rag_context = ""
        eval_faithfulness = False
        
        hit_at_3 = 0.0
        mrr = 0.0
        recall_at_5 = 0.0
        context_precision = 0.0
        context_recall = 0.0
        eval_retriever = False

        if expected_intent in ["chat", "check_health", "check_nutrition"]:
            # RAG Context
            rag_context = retriever.retrieve_context(query)
            if "Không tìm thấy tài liệu" not in rag_context:
                eval_faithfulness = True
            
            # Fetch chunks for detailed retrieval metrics
            chunks_3 = retriever.pipeline.retrieve(query, k=3)
            chunks_5 = retriever.pipeline.retrieve(query, k=5)
            
            if chunks_3 and len(expected_keywords) > 0:
                eval_retriever = True
                retriever_count += 1
                
                # 3a. Hit@3
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

                # 3b. MRR
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

                # 3c. Recall@5
                found_kws = set()
                for chunk in chunks_5:
                    for kw in expected_keywords:
                        if kw.lower() in chunk.page_content.lower():
                            found_kws.add(kw)
                recall_at_5 = len(found_kws) / len(expected_keywords) if len(expected_keywords) > 0 else 1.0
                total_recall_at_5 += recall_at_5

                # 3d. Context Precision (LLM-as-a-Judge)
                relevant_count = 0
                for chunk in chunks_3:
                    prec_res = await judge.evaluate_chunk_relevance(query, chunk.page_content)
                    if prec_res.get("relevant", False):
                        relevant_count += 1
                context_precision = relevant_count / len(chunks_3) if len(chunks_3) > 0 else 0.0
                total_context_precision += context_precision

                # 3e. Context Recall (LLM-as-a-Judge)
                combined_context_3 = "\n\n".join([f"Chunk {i}:\n{doc.page_content}" for i, doc in enumerate(chunks_3, 1)])
                rec_res = await judge.evaluate_context_recall(expected_notes, combined_context_3)
                context_recall = rec_res.get("score", 0.0)
                total_context_recall += context_recall

        # 4. LLM-as-a-Judge Response Evaluation
        relevancy_res = await judge.evaluate_relevancy(query, actual_output)
        relevancy_score = relevancy_res.get("score", 0.0)
        relevancy_reason = relevancy_res.get("reason", "")
        total_relevancy += relevancy_score

        faithfulness_score = 1.0
        faithfulness_reason = "N/A - Khong su dung RAG"
        if eval_faithfulness:
            faithfulness_res = await judge.evaluate_faithfulness(query, actual_output, rag_context)
            faithfulness_score = faithfulness_res.get("score", 0.0)
            faithfulness_reason = faithfulness_res.get("reason", "")
            total_faithfulness += faithfulness_score
            faithfulness_count += 1

        results.append({
            "id": idx,
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "intent_match": "PASS" if intent_match else "FAIL",
            "actual_output": actual_output,
            "relevancy_score": relevancy_score,
            "relevancy_reason": relevancy_reason,
            "faithfulness_score": faithfulness_score if eval_faithfulness else None,
            "faithfulness_reason": faithfulness_reason,
            # Retriever quality metrics
            "eval_retriever": eval_retriever,
            "hit_at_3": hit_at_3,
            "mrr": mrr,
            "recall_at_5": recall_at_5,
            "context_precision": context_precision,
            "context_recall": context_recall
        })
        
        safe_print(f"  -> Intent: {actual_intent} ({'Khop' if intent_match else 'Khong khop'})")
        safe_print(f"  -> Relevancy: {relevancy_score:.2f}")
        if eval_faithfulness:
            safe_print(f"  -> Faithfulness: {faithfulness_score:.2f}")
        if eval_retriever:
            safe_print(f"  -> Hit@3: {hit_at_3:.2f} | MRR: {mrr:.2f} | Recall@5: {recall_at_5:.2f}")
            safe_print(f"  -> Context Precision: {context_precision:.2f} | Context Recall: {context_recall:.2f}")

    intent_accuracy = (intent_correct / total_cases) * 100
    avg_relevancy = total_relevancy / total_cases
    avg_faithfulness = (total_faithfulness / faithfulness_count) if faithfulness_count > 0 else 1.0
    
    avg_hit_at_3 = (total_hit_at_3 / retriever_count) if retriever_count > 0 else 1.0
    avg_mrr = (total_mrr / retriever_count) if retriever_count > 0 else 1.0
    avg_recall_at_5 = (total_recall_at_5 / retriever_count) if retriever_count > 0 else 1.0
    avg_context_precision = (total_context_precision / retriever_count) if retriever_count > 0 else 1.0
    avg_context_recall = (total_context_recall / retriever_count) if retriever_count > 0 else 1.0

    safe_print("\n=== KET QUA DANH GIA TONG QUAN ===")
    safe_print(f"Intent Accuracy: {intent_accuracy:.2f}%")
    safe_print(f"Average Answer Relevancy: {avg_relevancy:.2f}")
    safe_print(f"Average Faithfulness (RAG): {avg_faithfulness:.2f}")
    safe_print(f"Average Hit@3: {avg_hit_at_3:.2f}")
    safe_print(f"Average MRR: {avg_mrr:.2f}")
    safe_print(f"Average Recall@5: {avg_recall_at_5:.2f}")
    safe_print(f"Average Context Precision: {avg_context_precision:.2f}")
    safe_print(f"Average Context Recall: {avg_context_recall:.2f}")

    # Sinh markdown report
    report_content = f"""# Báo cáo Đánh giá Chất lượng AI Agent (Evaluation Report)

Báo cáo này tổng hợp kết quả chạy kiểm định chất lượng tự động sử dụng phương pháp **LLM-as-a-Judge (Gemini 2.5 Flash)** trên tập dữ liệu chuẩn Golden Dataset chứa 12 kịch bản thực tế.

---

## 📊 Chỉ số Trung bình Hệ thống

### 1. Chỉ số Khả năng Trả lời (Response Quality)
* **Intent Accuracy (Độ chính xác phân loại luồng)**: `{intent_accuracy:.2f}%`
* **Average Answer Relevancy (Độ phù hợp trung bình)**: `{avg_relevancy:.2f} / 1.0`
* **Average Faithfulness (Độ trung thực trung bình - RAG)**: `{avg_faithfulness:.2f} / 1.0`

### 2. Chỉ số Bộ truy xuất (Retriever Quality)
* **Mean Hit@3**: `{avg_hit_at_3:.2f}`
* **MRR (Mean Reciprocal Rank)**: `{avg_mrr:.2f}`
* **Recall@5**: `{avg_recall_at_5:.2f}`
* **Context Precision (Độ chính xác ngữ cảnh)**: `{avg_context_precision:.2f} / 1.0`
* **Context Recall (Độ phủ ngữ cảnh)**: `{avg_context_recall:.2f} / 1.0`

---

## 📝 Chi tiết Từng Kịch bản Kiểm thử

| ID | Câu hỏi | Ý định (Expected) | Ý định (Actual) | Khớp | Relevancy | Faithfulness | Hit@3 | MRR | Recall@5 | Context Precision | Context Recall |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for r in results:
        f_score_str = f"{r['faithfulness_score']:.2f}" if r['faithfulness_score'] is not None else "N/A"
        hit_str = f"{r['hit_at_3']:.2f}" if r['eval_retriever'] else "N/A"
        mrr_str = f"{r['mrr']:.2f}" if r['eval_retriever'] else "N/A"
        rec5_str = f"{r['recall_at_5']:.2f}" if r['eval_retriever'] else "N/A"
        cp_str = f"{r['context_precision']:.2f}" if r['eval_retriever'] else "N/A"
        cr_str = f"{r['context_recall']:.2f}" if r['eval_retriever'] else "N/A"
        
        report_content += f"| {r['id']} | {r['query']} | `{r['expected_intent']}` | `{r['actual_intent']}` | {'✅' if r['intent_match'] == 'PASS' else '❌'} | `{r['relevancy_score']:.2f}` | `{f_score_str}` | {hit_str} | {mrr_str} | {rec5_str} | {cp_str} | {cr_str} |\n"

    report_content += "\n## 🔍 Nhật ký giải thích chi tiết từ Giám khảo\n\n"
    for r in results:
        report_content += f"### Kịch bản {r['id']}: {r['query']}\n"
        report_content += f"* **Phản hồi của Agent**:\n  > {r['actual_output']}\n"
        report_content += f"* **Nhận xét Độ phù hợp (Relevancy)**: Score: `{r['relevancy_score']:.2f}` - *{r['relevancy_reason']}*\n"
        if r['faithfulness_score'] is not None:
            report_content += f"* **Nhận xét Độ trung thực (Faithfulness)**: Score: `{r['faithfulness_score']:.2f}` - *{r['faithfulness_reason']}*\n"
        if r['eval_retriever']:
            report_content += f"* **Nhận xét chỉ số Retriever**:\n"
            report_content += f"  - Hit@3: `{r['hit_at_3']:.2f}` | MRR: `{r['mrr']:.2f}` | Recall@5: `{r['recall_at_5']:.2f}`\n"
            report_content += f"  - Context Precision: `{r['context_precision']:.2f}`\n"
            report_content += f"  - Context Recall: `{r['context_recall']:.2f}`\n"
        report_content += "\n---\n\n"

    os.makedirs("tests/evaluation", exist_ok=True)
    with open("tests/evaluation/eval_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    safe_print("\nDa tao bao cao danh gia chi tiet tai tests/evaluation/eval_report.md")

if __name__ == "__main__":
    anyio.run(main)


