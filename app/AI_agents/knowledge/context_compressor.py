import logging
from typing import List, Optional, Any
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Nén ngữ cảnh RAG & Quản lý ngân sách Token (Context Compaction & Token Budget Manager).
    """
    @staticmethod
    def compact_and_budget_context(docs: List[Document], plan: Any = None, max_tokens: int = 800) -> str:
        """
        Nén ngữ cảnh & Quản lý ngân sách Token áp dụng 4 bước nâng cao:
        1. Remove Duplicates: Khử trùng lặp giữa các chunk.
        2. Rerank: Duy trì thứ tự ưu tiên điểm số Rerank.
        3. Merge Related Chunks: Gộp các chunk thuộc cùng một nguồn tài liệu.
        4. Preserve Metadata: Giữ nguyên metadata nguồn, trang, chapter.
        """
        if not docs:
            return "Không tìm thấy tài liệu y tế phù hợp."

        # 1. Remove Duplicates (Khử trùng lặp dựa trên nội dung)
        seen_hashes = set()
        unique_docs = []
        for doc in docs:
            content_snippet = doc.page_content.strip()[:150].lower()
            if content_snippet not in seen_hashes:
                seen_hashes.add(content_snippet)
                unique_docs.append(doc)

        # 2 & 3. Merge Related Chunks (Gộp các chunk cùng nguồn tài liệu & bảo tồn thứ tự Rerank)
        grouped_docs: dict[str, dict] = {}
        for doc in unique_docs:
            source = doc.metadata.get("source", "Tài liệu Y tế")
            page = doc.metadata.get("page")
            chapter = doc.metadata.get("chapter")

            key = source
            if key not in grouped_docs:
                grouped_docs[key] = {
                    "source": source,
                    "pages": set(),
                    "chapters": set(),
                    "contents": []
                }

            if page:
                grouped_docs[key]["pages"].add(str(page))
            if chapter:
                grouped_docs[key]["chapters"].add(str(chapter))

            lines = [line.strip() for line in doc.page_content.strip().split("\n") if line.strip()]
            grouped_docs[key]["contents"].append("\n".join(lines))

        # 4. Preserve Metadata & Token Budget Guard
        max_chars = max_tokens * 4
        context_parts = []
        current_length = 0

        for i, (source_key, data) in enumerate(grouped_docs.items(), 1):
            meta_info = f"Nguồn: {data['source']}"
            if data["pages"]:
                meta_info += f" | Trang: {', '.join(sorted(data['pages']))}"
            if data["chapters"]:
                meta_info += f" | Mục: {', '.join(sorted(data['chapters']))}"

            merged_text = "\n---\n".join(data["contents"])
            part = f"--- Tài liệu {i} ({meta_info}) ---\n{merged_text}"
            part_len = len(part)

            if current_length + part_len > max_chars:
                remaining_chars = max_chars - current_length
                if remaining_chars > 100:
                    context_parts.append(part[:remaining_chars] + "\n...[Cắt bớt do giới hạn Token Budget]")
                break

            context_parts.append(part)
            current_length += part_len

        return "\n\n".join(context_parts)


def compact_and_budget_context(docs: List[Document], plan: Any = None, max_tokens: int = 800) -> str:
    """Helper tương thích ngược cho compact_and_budget_context."""
    return ContextCompressor.compact_and_budget_context(docs, plan=plan, max_tokens=max_tokens)
