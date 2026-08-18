import time
from typing import List, Tuple, Optional, Dict, Any
from langchain_core.documents import Document
from app.AI_agents.knowledge.reranker import LocalReranker

class SelectiveReranker:
    """
    Selective Reranker Gate module for Production & Evaluation:
    Combines Confidence Threshold, Margin Threshold, and Candidate Pool limits
    to selectively bypass or execute CrossEncoder Reranking.
    """
    def __init__(
        self,
        confidence_threshold: float = 0.75,
        margin_threshold: float = 0.05,
        gate_mode: str = "combined",  # "confidence", "margin", "combined", "always"
        candidate_pool_size: int = 10
    ):
        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold
        self.gate_mode = gate_mode
        self.candidate_pool_size = candidate_pool_size
        self._reranker: Optional[LocalReranker] = None

    @property
    def reranker(self) -> LocalReranker:
        if self._reranker is None:
            self._reranker = LocalReranker()
        return self._reranker

    def should_bypass(self, candidates_with_scores: List[Tuple[Document, float]]) -> bool:
        """
        Determines whether to bypass reranking based on top-1 confidence score and margin (top1 - top2).
        Note: Lower distance or higher similarity score depending on metric. For normalized scores [0..1]:
        """
        if not candidates_with_scores:
            return True
            
        if len(candidates_with_scores) == 1:
            return True
            
        top1_score = candidates_with_scores[0][1]
        top2_score = candidates_with_scores[1][1]
        margin = abs(top1_score - top2_score)

        if self.gate_mode == "confidence":
            return top1_score >= self.confidence_threshold
        elif self.gate_mode == "margin":
            return margin >= self.margin_threshold
        elif self.gate_mode == "combined":
            return (top1_score >= self.confidence_threshold) and (margin >= self.margin_threshold)
        elif self.gate_mode == "always":
            return False
        elif self.gate_mode == "never":
            return True
            
        return False

    def rerank_selectively(
        self,
        query: str,
        candidates: List[Document],
        scores: Optional[List[float]] = None,
        top_k: int = 3
    ) -> Tuple[List[Document], bool, float]:
        """
        Returns: (reranked_docs, did_rerank, latency_ms)
        """
        t0 = time.time()
        
        # Candidate pool limit
        pool = candidates[:self.candidate_pool_size]
        
        if not pool:
            return [], False, (time.time() - t0) * 1000

        # Construct (doc, score) pairs if scores provided
        paired = []
        if scores and len(scores) >= len(pool):
            paired = list(zip(pool, scores[:len(pool)]))
        else:
            # Fake pseudo score based on rank position if scores not provided
            paired = [(doc, 1.0 / (idx + 1)) for idx, doc in enumerate(pool)]

        if self.should_bypass(paired):
            latency_ms = (time.time() - t0) * 1000
            return pool[:top_k], False, latency_ms

        # Execute Reranker
        reranked = self.reranker.rerank(query, pool, top_k=top_k)
        latency_ms = (time.time() - t0) * 1000
        return reranked, True, latency_ms
