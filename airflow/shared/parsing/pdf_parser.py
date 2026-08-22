import os
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pypdf import PdfReader
from airflow.shared.utils.logging import get_logger

logger = get_logger("pdf_parser")


@dataclass
class PageContent:
    page_number: int
    text: str
    char_count: int
    word_count: int
    is_blank: bool


@dataclass
class PDFParseResult:
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages: List[PageContent] = field(default_factory=list)
    total_pages: int = 0


class PDFParser:
    """
    Trích xuất văn bản từ tập tin PDF theo từng trang bằng PyPDF,
    bảo toàn metadata tài liệu (title, author) và làm sạch text.
    """

    def __init__(self, min_char_threshold: int = 10):
        self.min_char_threshold = min_char_threshold

    def clean_text(self, text: str) -> str:
        """Làm sạch các ký tự đặc biệt, ngắt dòng thừa và chuẩn hóa khoảng trắng."""
        if not text:
            return ""
        text = text.replace("\x00", " ")
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def extract_metadata(self, reader: PdfReader) -> Dict[str, Any]:
        """Trích xuất metadata tài liệu PDF (Title, Author, Subject, Creator)."""
        meta = {}
        if reader.metadata:
            raw_meta = reader.metadata
            meta["title"] = str(raw_meta.title) if raw_meta.title else None
            meta["author"] = str(raw_meta.author) if raw_meta.author else None
            meta["subject"] = str(raw_meta.subject) if raw_meta.subject else None
            meta["creator"] = str(raw_meta.creator) if raw_meta.creator else None
        return meta

    def parse_file(self, file_path: str) -> List[PageContent]:
        """Đọc và trích xuất toàn bộ các trang từ file PDF."""
        result = self.parse_document(file_path)
        return result.pages

    def parse_document(self, file_path: str) -> PDFParseResult:
        """Đọc và trích xuất cả Metadata và Pages từ file PDF."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File PDF không tồn tại tại: {file_path}")

        pages: List[PageContent] = []
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            doc_metadata = self.extract_metadata(reader)
            logger.info(f"[PDFParser] Bắt đầu trích xuất: {file_path} ({total_pages} trang)")

            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                try:
                    raw_text = page.extract_text() or ""
                    cleaned = self.clean_text(raw_text)
                    char_count = len(cleaned)
                    word_count = len(cleaned.split())
                    is_blank = char_count < self.min_char_threshold

                    pages.append(PageContent(
                        page_number=page_num,
                        text=cleaned,
                        char_count=char_count,
                        word_count=word_count,
                        is_blank=is_blank
                    ))
                except Exception as page_err:
                    logger.warning(f"[PDFParser] Lỗi trích xuất trang {page_num}: {page_err}")
                    pages.append(PageContent(
                        page_number=page_num,
                        text="",
                        char_count=0,
                        word_count=0,
                        is_blank=True
                    ))

            logger.info(f"[PDFParser] Hoàn tất trích xuất {len(pages)} trang.")
            return PDFParseResult(
                metadata=doc_metadata,
                pages=pages,
                total_pages=len(pages)
            )

        except Exception as e:
            logger.error(f"[PDFParser] Không thể đọc file PDF {file_path}: {e}")
            raise


def parse_pdf(file_path: str, min_char_threshold: int = 10) -> List[Dict[str, Any]]:
    """
    Helper function trích xuất PDF thành danh sách dictionaries các trang.
    Dùng trực tiếp trong Airflow Task 2: pages = parse_pdf(doc.file_path).
    """
    parser = PDFParser(min_char_threshold=min_char_threshold)
    pages = parser.parse_file(file_path)
    return [asdict(p) for p in pages]
