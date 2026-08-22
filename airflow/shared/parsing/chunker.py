import re
from dataclasses import dataclass
from typing import List, Optional
from airflow.shared.parsing.pdf_parser import PageContent
from airflow.shared.utils.hashing import compute_text_sha256
from airflow.shared.utils.logging import get_logger

logger = get_logger("chunker")


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    content_hash: str
    token_count: int
    char_count: int
    page_number: Optional[int] = None

    @property
    def content(self) -> str:
        return self.text


class SlidingWindowChunker:
    """
    Phân đoạn văn bản sử dụng kỹ thuật Sliding Window có Overlap,
    tôn trọng ranh giới câu / đoạn văn để không làm đứt gãy ngữ nghĩa.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_length: int = 30,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap phải nhỏ hơn chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_length = min_chunk_length

    def _split_into_sentences(self, text: str) -> List[str]:
        """Tách chuỗi thành danh sách các câu dựa trên các dấu kết thúc câu."""
        sentence_endings = re.compile(r'(?<=[.!?。！？\n])\s+')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str, page_number: Optional[int] = None, start_index: int = 0) -> List[TextChunk]:
        """
        Chia một đoạn văn bản thành các chunks trượt.

        Args:
            text: Nội dung văn bản.
            page_number: Trang xuất xứ.
            start_index: Số thứ tự chunk bắt đầu.

        Returns:
            Danh sách TextChunk.
        """
        if not text or len(text.strip()) < self.min_chunk_length:
            return []

        sentences = self._split_into_sentences(text)
        chunks: List[TextChunk] = []
        current_chunk_sentences: List[str] = []
        current_length = 0
        chunk_idx = start_index

        for sent in sentences:
            sent_len = len(sent)
            if current_length + sent_len > self.chunk_size and current_chunk_sentences:
                chunk_str = " ".join(current_chunk_sentences).strip()
                if len(chunk_str) >= self.min_chunk_length:
                    chunks.append(TextChunk(
                        chunk_index=chunk_idx,
                        text=chunk_str,
                        content_hash=compute_text_sha256(chunk_str),
                        token_count=len(chunk_str.split()),
                        char_count=len(chunk_str),
                        page_number=page_number,
                    ))
                    chunk_idx += 1

                overlap_length = 0
                overlap_sentences = []
                for s in reversed(current_chunk_sentences):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk_sentences = overlap_sentences + [sent]
                current_length = sum(len(s) for s in current_chunk_sentences) + len(current_chunk_sentences) - 1
            else:
                current_chunk_sentences.append(sent)
                current_length += sent_len + 1

        if current_chunk_sentences:
            chunk_str = " ".join(current_chunk_sentences).strip()
            if len(chunk_str) >= self.min_chunk_length:
                chunks.append(TextChunk(
                    chunk_index=chunk_idx,
                    text=chunk_str,
                    content_hash=compute_text_sha256(chunk_str),
                    token_count=len(chunk_str.split()),
                    char_count=len(chunk_str),
                    page_number=page_number,
                ))

        return chunks

    def chunk_pages(self, pages: List[PageContent]) -> List[TextChunk]:
        """Phân đoạn một danh sách các PageContent đã trích xuất từ PDF."""
        all_chunks: List[TextChunk] = []
        current_index = 0

        for page in pages:
            if page.is_blank:
                continue
            page_chunks = self.chunk_text(
                text=page.text,
                page_number=page.page_number,
                start_index=current_index
            )
            all_chunks.extend(page_chunks)
            current_index += len(page_chunks)

        logger.info(f"[Chunker] Đã tạo thành công {len(all_chunks)} chunks từ {len(pages)} trang.")
        return all_chunks


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Helper function phân đoạn văn bản dạng chuỗi thuần túy trả về list các đoạn text.
    Khớp 100% với hàm chunk_text(full_text, chunk_size=512, overlap=50) trong Task 3.
    """
    chunker = SlidingWindowChunker(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = chunker.chunk_text(text)
    return [c.text for c in chunks]
