from typing import Callable
import math
import re
from langchain_core.documents import Document

class SparseBM25Retriever:
    """
    A lightweight, local, dependency-free implementation of BM25
    specifically tailored for retrieving relevant chunks from indexed documents.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: list[Document] = []
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lens = []
        self.doc_term_freqs = []  # list of dicts: term -> count
        self.idf = {}  # term -> idf

    def _tokenize(self, text: str) -> list[str]:
        """Simple Vietnamese-friendly tokenizer (lowercasing, cleaning punctuation)."""
        text = text.lower()
        # Remove punctuation, keep words/numbers
        tokens = re.findall(r'\w+', text)
        return tokens

    def fit(self, documents: list[Document]):
        """Index a list of documents/chunks."""
        self.documents = documents
        self.corpus_size = len(documents)
        
        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            self.doc_lens = []
            self.doc_term_freqs = []
            self.idf = {}
            return

        self.doc_lens = []
        self.doc_term_freqs = []
        doc_freqs = {}  # term -> number of docs containing term
        total_len = 0

        for doc in documents:
            tokens = self._tokenize(doc.page_content)
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len

            term_freq = {}
            for t in tokens:
                term_freq[t] = term_freq.get(t, 0) + 1

            self.doc_term_freqs.append(term_freq)

            # Record document frequency for each term
            for t in term_freq.keys():
                doc_freqs[t] = doc_freqs.get(t, 0) + 1

        self.avg_doc_len = total_len / self.corpus_size

        # Calculate IDF for each term: math.log(1 + (corpus_size - doc_freq + 0.5) / (doc_freq + 0.5))
        for term, df in doc_freqs.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

    def retrieve(self, query: str, k: int = 10, filter_func: Callable[[dict], bool] = None) -> list[Document]:
        """Query BM25 to get the top k document chunks."""
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for idx in range(self.corpus_size):
            doc = self.documents[idx]
            if filter_func and not filter_func(doc.metadata):
                continue

            score = 0.0
            doc_len = self.doc_lens[idx]
            term_freqs = self.doc_term_freqs[idx]

            for term in query_tokens:
                if term in term_freqs:
                    tf = term_freqs[term]
                    idf_val = self.idf.get(term, 0.0)
                    
                    # BM25 formula
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += idf_val * (numerator / denominator)

            scores.append((score, doc))

        # Sort documents by score descending
        sorted_scored_docs = sorted(scores, key=lambda x: x[0], reverse=True)
        
        # Filter out docs with 0 score (no token match) unless we have fewer documents than requested k
        top_docs = []
        for score, doc in sorted_scored_docs:
            if score > 0.0 or len(top_docs) < k:
                top_docs.append(doc)
            if len(top_docs) >= k:
                break
                
        return top_docs
