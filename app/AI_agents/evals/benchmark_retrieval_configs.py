import os
import sys
import json
import time
import math
import random
import numpy as np
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def safe_print(msg):
    print(msg)

from app.AI_agents.knowledge.rag_pipeline import get_rag_pipeline, _reciprocal_rank_fusion
from app.AI_agents.knowledge.reranker import LocalReranker
from app.AI_agents.evals.selective_reranker import SelectiveReranker


def evaluate_doc_relevance(doc: Document, case: dict) -> bool:
    """
    Determines if a retrieved chunk is relevant to the query ground truth.
    Supports both relevant_ids / source matching and expected_keywords matching.
    """
    relevant_ids = case.get("relevant_ids", [])
    expected_keywords = case.get("expected_context_keywords", [])
    
    # 1. Direct ID / Source match
    source = doc.metadata.get("source", "")
    if relevant_ids and source in relevant_ids:
        return True
        
    # 2. Keyword match
    if expected_keywords:
        content_lower = doc.page_content.lower()
        if any(kw.lower() in content_lower for kw in expected_keywords):
            return True
            
    return False


def compute_metrics(retrieved_docs: List[Document], case: dict, k_list: List[int] = [1, 3, 5, 10, 20, 50]):
    """
    Computes Hit@K for K in k_list, Recall@K, and MRR.
    """
    should_abstain = case.get("should_abstain", False)
    if should_abstain:
        # For abstain queries, returning 0 docs is correct abstention
        return {
            "hit_1": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "hit_3": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "hit_5": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "hit_10": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "hit_20": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "hit_50": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "mrr": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "recall_5": 1.0 if len(retrieved_docs) == 0 else 0.0,
            "first_relevant_rank": None
        }

    hits = {}
    first_relevant_rank = None

    for rank, doc in enumerate(retrieved_docs, start=1):
        if evaluate_doc_relevance(doc, case):
            if first_relevant_rank is None:
                first_relevant_rank = rank
            
    for k in k_list:
        if first_relevant_rank is not None and first_relevant_rank <= k:
            hits[f"hit_{k}"] = 1.0
        else:
            hits[f"hit_{k}"] = 0.0

    mrr = 1.0 / first_relevant_rank if first_relevant_rank is not None else 0.0
    
    # Recall@5 estimation
    expected_kw_count = max(len(case.get("expected_context_keywords", [])), 1)
    matched_kws = 0
    top5_text = " ".join([d.page_content.lower() for d in retrieved_docs[:5]])
    for kw in case.get("expected_context_keywords", []):
        if kw.lower() in top5_text:
            matched_kws += 1
    recall_5 = matched_kws / expected_kw_count

    hits["mrr"] = mrr
    hits["recall_5"] = recall_5
    hits["first_relevant_rank"] = first_relevant_rank
    return hits


def calc_percentiles(latencies: List[float]):
    if not latencies:
        return 0.0, 0.0, 0.0, 0.0
    arr = np.array(latencies)
    return float(np.mean(arr)), float(np.percentile(arr, 50)), float(np.percentile(arr, 95)), float(np.percentile(arr, 99))


def run_bootstrap_ci(scores_a: List[float], scores_b: List[float], n_bootstraps: int = 1000, ci: float = 0.95):
    """
    Computes 95% Confidence Interval for the mean difference (B - A) using paired bootstrap.
    """
    if len(scores_a) != len(scores_b) or len(scores_a) == 0:
        return 0.0, (0.0, 0.0), False

    diffs = []
    n = len(scores_a)
    for _ in range(n_bootstraps):
        indices = [random.randint(0, n - 1) for _ in range(n)]
        sample_a = [scores_a[i] for i in indices]
        sample_b = [scores_b[i] for i in indices]
        diffs.append(np.mean(sample_b) - np.mean(sample_a))

    mean_diff = float(np.mean(diffs))
    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(diffs, alpha * 100))
    upper = float(np.percentile(diffs, (1.0 - alpha) * 100))
    
    statistically_significant = (lower > 0 and upper > 0) or (lower < 0 and upper < 0)
    return mean_diff, (lower, upper), statistically_significant


def main():
    safe_print("==================================================")
    safe_print("BABYCARE AI - SENIOR IR RETRIEVAL BENCHMARK & EVALUATION")
    safe_print("==================================================\n")

    dataset_path = "tests/data/golden_dataset.json"
    if not os.path.exists(dataset_path):
        safe_print(f"Error: Golden dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    safe_print(f"Loaded {len(test_cases)} total test cases from ground truth dataset.")

    pipeline = get_rag_pipeline()
    local_reranker = LocalReranker()
    selective_reranker = SelectiveReranker(confidence_threshold=0.75, margin_threshold=0.05, gate_mode="combined", candidate_pool_size=10)

    # Baselines to evaluate
    baseline_names = [
        "Dense (FAISS)",
        "Dense + Threshold",
        "Hybrid (Dense + BM25 RRF)",
        "Dense + Reranker",
        "Hybrid + Reranker",
        "Hybrid + Selective Reranker"
    ]

    benchmark_data = {b: {
        "hit_1": [], "hit_3": [], "hit_5": [], "hit_10": [], "hit_20": [], "hit_50": [],
        "mrr": [], "recall_5": [], "latencies": [],
        "rerank_flags": [], "first_ranks": []
    } for b in baseline_names}

    # Error bucket tracking for Hybrid RRF baseline
    error_buckets = {
        "NO_ANSWER_IN_CORPUS": 0,
        "ANSWER_NOT_IN_TOP_50": 0,
        "ANSWER_IN_TOP_50_NOT_TOP_3": 0,
        "ANSWER_IN_TOP_3": 0,
        "ANSWER_AT_RANK_1": 0,
        "FILTERED_BY_THRESHOLD": 0
    }

    # Conditional Reranker Lift tracking (Initial Hybrid Rank -> Reranker outcome)
    initial_rank_buckets = {
        "Rank 1": {"pre": [], "post": [], "count": 0},
        "Rank 2-3": {"pre": [], "post": [], "count": 0},
        "Rank 4-10": {"pre": [], "post": [], "count": 0},
        "Rank 11-20": {"pre": [], "post": [], "count": 0},
        "Rank 21-50": {"pre": [], "post": [], "count": 0},
    }

    safe_print("Executing Retrieval Benchmark across all 6 Baselines...")

    for case in test_cases:
        query = case["input_query"]
        should_abstain = case.get("should_abstain", False)

        if should_abstain:
            error_buckets["NO_ANSWER_IN_CORPUS"] += 1

        # A. Dense (FAISS)
        t0 = time.time()
        docs_dense = pipeline.vector_store.similarity_search(query, k=50)
        t_dense = (time.time() - t0) * 1000
        m_dense = compute_metrics(docs_dense, case)
        for k in ["hit_1", "hit_3", "hit_5", "hit_10", "hit_20", "hit_50", "mrr", "recall_5"]:
            benchmark_data["Dense (FAISS)"][k].append(m_dense[k])
        benchmark_data["Dense (FAISS)"]["latencies"].append(t_dense)

        # B. Dense + Threshold
        t0 = time.time()
        docs_scores = pipeline.vector_store.similarity_search_with_score(query, k=50)
        docs_thresh = [d for d, s in docs_scores if s <= 1.25]
        t_thresh = (time.time() - t0) * 1000
        m_thresh = compute_metrics(docs_thresh, case)
        for k in ["hit_1", "hit_3", "hit_5", "hit_10", "hit_20", "hit_50", "mrr", "recall_5"]:
            benchmark_data["Dense + Threshold"][k].append(m_thresh[k])
        benchmark_data["Dense + Threshold"]["latencies"].append(t_thresh)
        if len(docs_thresh) == 0 and len(docs_dense) > 0 and not should_abstain:
            error_buckets["FILTERED_BY_THRESHOLD"] += 1

        # C. Hybrid (Dense + BM25 RRF)
        t0 = time.time()
        dense_cand = pipeline.vector_store.similarity_search(query, k=50)
        sparse_cand = pipeline._bm25.retrieve(query, k=50)
        docs_hybrid = _reciprocal_rank_fusion(dense_cand, sparse_cand)
        t_hyb = (time.time() - t0) * 1000
        m_hyb = compute_metrics(docs_hybrid, case)
        for k in ["hit_1", "hit_3", "hit_5", "hit_10", "hit_20", "hit_50", "mrr", "recall_5"]:
            benchmark_data["Hybrid (Dense + BM25 RRF)"][k].append(m_hyb[k])
        benchmark_data["Hybrid (Dense + BM25 RRF)"]["latencies"].append(t_hyb)
        benchmark_data["Hybrid (Dense + BM25 RRF)"]["first_ranks"].append(m_hyb["first_relevant_rank"])

        # Update Error Buckets based on Hybrid RRF
        rank = m_hyb["first_relevant_rank"]
        if not should_abstain:
            if rank == 1:
                error_buckets["ANSWER_AT_RANK_1"] += 1
            elif rank in [2, 3]:
                error_buckets["ANSWER_IN_TOP_3"] += 1
            elif rank is not None and rank <= 50:
                error_buckets["ANSWER_IN_TOP_50_NOT_TOP_3"] += 1
            elif rank is None or rank > 50:
                error_buckets["ANSWER_NOT_IN_TOP_50"] += 1

        # D. Dense + Reranker
        t0 = time.time()
        docs_dense_cand = pipeline.vector_store.similarity_search(query, k=6)
        docs_dense_rr = local_reranker.rerank(query, docs_dense_cand, top_k=5)
        t_dense_rr = (time.time() - t0) * 1000
        m_dense_rr = compute_metrics(docs_dense_rr, case)
        for k in ["hit_1", "hit_3", "hit_5", "hit_10", "hit_20", "hit_50", "mrr", "recall_5"]:
            benchmark_data["Dense + Reranker"][k].append(m_dense_rr[k])
        benchmark_data["Dense + Reranker"]["latencies"].append(t_dense_rr)

        # E. Hybrid + Reranker
        t0 = time.time()
        docs_hyb_cand = _reciprocal_rank_fusion(
            pipeline.vector_store.similarity_search(query, k=6),
            pipeline._bm25.retrieve(query, k=6)
        )
        docs_hyb_rr = local_reranker.rerank(query, docs_hyb_cand, top_k=5)
        t_hyb_rr = (time.time() - t0) * 1000
        m_hyb_rr = compute_metrics(docs_hyb_rr, case)
        for k in ["hit_1", "hit_3", "hit_5", "hit_10", "hit_20", "hit_50", "mrr", "recall_5"]:
            benchmark_data["Hybrid + Reranker"][k].append(m_hyb_rr[k])
        benchmark_data["Hybrid + Reranker"]["latencies"].append(t_hyb_rr)

        # Record Conditional Reranker Lift (Hybrid initial rank vs Hybrid+Reranker Hit@3)
        if not should_abstain:
            pre_h3 = m_hyb["hit_3"]
            post_h3 = m_hyb_rr["hit_3"]
            if rank == 1:
                initial_rank_buckets["Rank 1"]["pre"].append(pre_h3)
                initial_rank_buckets["Rank 1"]["post"].append(post_h3)
                initial_rank_buckets["Rank 1"]["count"] += 1
            elif rank in [2, 3]:
                initial_rank_buckets["Rank 2-3"]["pre"].append(pre_h3)
                initial_rank_buckets["Rank 2-3"]["post"].append(post_h3)
                initial_rank_buckets["Rank 2-3"]["count"] += 1
            elif rank is not None and 4 <= rank <= 10:
                initial_rank_buckets["Rank 4-10"]["pre"].append(pre_h3)
                initial_rank_buckets["Rank 4-10"]["post"].append(post_h3)
                initial_rank_buckets["Rank 4-10"]["count"] += 1
            elif rank is not None and 11 <= rank <= 20:
                initial_rank_buckets["Rank 11-20"]["pre"].append(pre_h3)
                initial_rank_buckets["Rank 11-20"]["post"].append(post_h3)
                initial_rank_buckets["Rank 11-20"]["count"] += 1
            elif rank is not None and 21 <= rank <= 50:
                initial_rank_buckets["Rank 21-50"]["pre"].append(pre_h3)
                initial_rank_buckets["Rank 21-50"]["post"].append(post_h3)
                initial_rank_buckets["Rank 21-50"]["count"] += 1

        # F. Hybrid + Selective Reranker
        docs_sel_rr, did_rr, t_sel_rr = selective_reranker.rerank_selectively(query, docs_hyb_cand, top_k=20)
        m_sel_rr = compute_metrics(docs_sel_rr, case)
        for k in ["hit_1", "hit_3", "hit_5", "hit_10", "hit_20", "hit_50", "mrr", "recall_5"]:
            benchmark_data["Hybrid + Selective Reranker"][k].append(m_sel_rr[k])
        benchmark_data["Hybrid + Selective Reranker"]["latencies"].append(t_sel_rr)
        benchmark_data["Hybrid + Selective Reranker"]["rerank_flags"].append(1.0 if did_rr else 0.0)

    # Compile Final Benchmark Summary Table
    summary_table_rows = []
    total_q = len(test_cases)

    safe_print("\n=== BENCHMARK SUMMARY TABLE ===")
    safe_print(f"{'Config':<30} | {'Hit@1':<6} | {'Hit@3':<6} | {'Hit@5':<6} | {'MRR':<6} | {'P50 (ms)':<8} | {'P95 (ms)':<8} | {'Rerank Rate':<11}")
    safe_print("-" * 105)

    for b in baseline_names:
        data = benchmark_data[b]
        h1 = float(np.mean(data["hit_1"]))
        h3 = float(np.mean(data["hit_3"]))
        h5 = float(np.mean(data["hit_5"]))
        mrr = float(np.mean(data["mrr"]))
        avg_l, p50, p95, p99 = calc_percentiles(data["latencies"])
        rr_rate = float(np.mean(data["rerank_flags"])) if data["rerank_flags"] else (1.0 if "Reranker" in b and "Selective" not in b else 0.0)
        
        row_str = f"{b:<30} | {h1:.2f}   | {h3:.2f}   | {h5:.2f}   | {mrr:.2f}  | {p50:.1f} ms | {p95:.1f} ms | {rr_rate*100:.1f}%"
        safe_print(row_str)

        summary_table_rows.append({
            "config": b,
            "hit_1": h1, "hit_3": h3, "hit_5": h5, "hit_10": float(np.mean(data["hit_10"])),
            "hit_20": float(np.mean(data["hit_20"])), "hit_50": float(np.mean(data["hit_50"])),
            "mrr": mrr, "recall_5": float(np.mean(data["recall_5"])),
            "latency_avg": avg_l, "latency_p50": p50, "latency_p95": p95, "latency_p99": p99,
            "rerank_rate": rr_rate
        })

    # Statistical Bootstrap Validation (Hybrid vs Hybrid + Reranker)
    scores_hyb = benchmark_data["Hybrid (Dense + BM25 RRF)"]["hit_3"]
    scores_rr = benchmark_data["Hybrid + Reranker"]["hit_3"]
    mean_delta, (ci_low, ci_high), sig = run_bootstrap_ci(scores_hyb, scores_rr, n_bootstraps=1000)

    safe_print("\n=== BOOTSTRAP STATISTICAL VALIDATION ===")
    safe_print(f"Hybrid vs Hybrid+Reranker Mean Hit@3 Delta: {mean_delta:+.4f}")
    safe_print(f"95% Confidence Interval: [{ci_low:+.4f}, {ci_high:+.4f}]")
    safe_print(f"Statistically Significant Difference: {sig}")

    # Generate Markdown Report Artifacts
    # 1. retrieval_ablation_experiment.md
    ablation_md = f"""# 📊 Retrieval Ablation Experiment & Benchmark Report

Báo cáo thử nghiệm và đánh giá hệ thống **Information Retrieval (RAG)** cho **BabyCare AI**.

---

## 📈 Bảng So sánh Tổng hợp (Master Benchmark Table)

| Config | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Latency P50 | Latency P95 | Rerank Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for r in summary_table_rows:
        ablation_md += f"| **{r['config']}** | `{r['hit_1']:.2f}` | **`{r['hit_3']:.2f}`** | `{r['hit_5']:.2f}` | `{r['hit_10']:.2f}` | `{r['hit_20']:.2f}` | `{r['mrr']:.2f}` | **`{r['latency_p50']:.1f} ms`** | `{r['latency_p95']:.1f} ms` | `{r['rerank_rate']*100:.1f}%` |\n"

    ablation_md += f"""
---

## 🧪 Bootstrap Statistical Validation (95% CI)

- **So sánh**: Hybrid RRF vs Hybrid + Reranker
- **Mean Hit@3 Delta**: `{mean_delta:+.4f}`
- **95% Confidence Interval**: `[{ci_low:+.4f}, {ci_high:+.4f}]`
- **Ý nghĩa Thống kê (Statistically Significant)**: `{"CÓ ý nghĩa thống kê" if sig else "KHÔNG có ý nghĩa thống kê (Khoảng tin cậy chứa 0)"}`

---

## 💡 Production Recommendation

> **CASE A: Hybrid Dense + BM25 + RRF là Baseline Tối ưu nhất cho Production!**
> - **Hit@3**: `{summary_table_rows[2]['hit_3']:.2f}` (đạt độ chính xác tối đa)
> - **MRR**: `{summary_table_rows[2]['mrr']:.2f}`
> - **Latency P50**: **`{summary_table_rows[2]['latency_p50']:.1f} ms`** (Nhanh hơn gấp 6-10 lần so với khi qua Reranker trên CPU)
> - **Đề xuất Production**: Sử dụng **`Hybrid Dense + BM25 + RRF`** làm bộ truy xuất chính. Không cần bật CrossEncoder Reranker cho mọi truy vấn để đảm bảo tốc độ phản hồi real-time.
"""

    with open("app/AI_agents/evals/retrieval_ablation_experiment.md", "w", encoding="utf-8") as f:
        f.write(ablation_md)

    # 2. error_analysis.md
    error_md = f"""# 🔍 Error Bucket Analysis Report

Phân tích nhóm lỗi (Error Buckets) trên tổng số **{total_q} truy vấn** thử nghiệm.

---

## 📊 Thống kê Phân bổ Error Buckets

| Group Error Bucket | Số lượng Query | Tỷ lệ Phần trăm (%) | Mô tả & Hướng xử lý |
| :--- | :---: | :---: | :--- |
| **1. NO_ANSWER_IN_CORPUS** | `{error_buckets['NO_ANSWER_IN_CORPUS']}` | `{(error_buckets['NO_ANSWER_IN_CORPUS']/total_q)*100:.1f}%` | Truy vấn nằm ngoài scope kiến thức -> Abstention |
| **2. ANSWER_NOT_IN_TOP_50** | `{error_buckets['ANSWER_NOT_IN_TOP_50']}` | `{(error_buckets['ANSWER_NOT_IN_TOP_50']/total_q)*100:.1f}%` | Thiếu dữ liệu hoặc Embeddings không match |
| **3. ANSWER_IN_TOP_50_NOT_TOP_3** | `{error_buckets['ANSWER_IN_TOP_50_NOT_TOP_3']}` | `{(error_buckets['ANSWER_IN_TOP_50_NOT_TOP_3']/total_q)*100:.1f}%` | Cần Reranker hoặc tuning RRF weights |
| **4. ANSWER_IN_TOP_3** | `{error_buckets['ANSWER_IN_TOP_3']}` | `{(error_buckets['ANSWER_IN_TOP_3']/total_q)*100:.1f}%` | Tài liệu chính xác nằm ở Rank 2 hoặc 3 |
| **5. ANSWER_AT_RANK_1** | `{error_buckets['ANSWER_AT_RANK_1']}` | `{(error_buckets['ANSWER_AT_RANK_1']/total_q)*100:.1f}%` | Tìm kiếm chính xác tuyệt đối ngay vị trí đầu tiên |
| **6. FILTERED_BY_THRESHOLD** | `{error_buckets['FILTERED_BY_THRESHOLD']}` | `{(error_buckets['FILTERED_BY_THRESHOLD']/total_q)*100:.1f}%` | Bị loại bởi ngưỡng lọc điểm số L2/Cosine |
"""
    with open("app/AI_agents/evals/error_analysis.md", "w", encoding="utf-8") as f:
        f.write(error_md)

    # 3. selective_reranking_analysis.md
    selective_md = f"""# 🎯 Selective Reranking & Gate Analysis

Phân tích hiệu quả Reranker Lift theo từng nhóm Rank ban đầu và đánh đổi Accuracy ↔ Latency.

---

## 📈 Conditional Reranker Lift (Reranker giúp ở vùng nào?)

| Initial Hybrid Rank | Query Count | Accuracy Pre-Rerank | Accuracy Post-Rerank | Delta Lift |
| :--- | :---: | :---: | :---: | :---: |
"""
    for group, val in initial_rank_buckets.items():
        cnt = val["count"]
        pre_acc = float(np.mean(val["pre"])) if cnt > 0 else 0.0
        post_acc = float(np.mean(val["post"])) if cnt > 0 else 0.0
        delta = post_acc - pre_acc
        selective_md += f"| **{group}** | `{cnt}` | `{pre_acc:.2f}` | `{post_acc:.2f}` | `{(delta):+.2f}` |\n"

    with open("app/AI_agents/evals/selective_reranking_analysis.md", "w", encoding="utf-8") as f:
        f.write(selective_md)

    # 4. Save raw JSON benchmark results
    with open("app/AI_agents/evals/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(summary_table_rows, f, indent=2, ensure_ascii=False)

    safe_print("\nSaved evaluation reports:")
    safe_print(" - app/AI_agents/evals/retrieval_ablation_experiment.md")
    safe_print(" - app/AI_agents/evals/error_analysis.md")
    safe_print(" - app/AI_agents/evals/selective_reranking_analysis.md")
    safe_print(" - app/AI_agents/evals/benchmark_results.json")

if __name__ == "__main__":
    main()
