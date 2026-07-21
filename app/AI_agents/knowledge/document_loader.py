import os
import pypdf
from langchain_core.documents import Document
from app.AI_agents.core.constant import RAG_DOCUMENT_DIR

class DocumentLoader:
    def __init__(self, directory_path: str = RAG_DOCUMENT_DIR):
        self.directory_path = directory_path
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)
            self._seed_default_guidelines()

    def _seed_default_guidelines(self):
        default_file = os.path.join(self.directory_path, "parenting_guidelines.md")
        content = """# Hướng dẫn chăm sóc trẻ sơ sinh
1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác.
2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg mỗi liều, cách mỗi 4-6 tiếng nếu sốt lại.
3. Biểu hiện bé đói: Bé liếm môi, mút tay, quay đầu tìm vú.
4. Cách xử lý khi bé khóc dạ đề (colic): Ôm ấp bé, massage bụng nhẹ nhàng theo chiều kim đồng hồ, tắm nước ấm.
"""
        with open(default_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _get_metadata_for_file(self, filename: str, page: int = 1) -> dict:
        """Returns enriched metadata based on filename and page number."""
        name_lower = filename.lower()
        metadata = {
            "source": filename,
            "page": page,
            "category": "health",      # Default category
            "age_min_months": 0,       # Default min age
            "age_max_months": 999,     # Default max age
            "content_type": "guideline" # Default content type
        }

        if "chedoandam" in name_lower:
            metadata.update({
                "category": "nutrition",
                "age_min_months": 6,
                "age_max_months": 24,
                "content_type": "recipe"
            })
        elif "healthy" in name_lower:
            metadata.update({
                "category": "health",
                "age_min_months": 0,
                "age_max_months": 60,
                "content_type": "guideline"
            })
        elif "babycare" in name_lower:
            metadata.update({
                "category": "health",
                "age_min_months": 0,
                "age_max_months": 36,
                "content_type": "guideline"
            })
        elif "parenting_guidelines" in name_lower:
            metadata.update({
                "category": "health",
                "age_min_months": 0,
                "age_max_months": 12,
                "content_type": "guideline"
            })
            
        return metadata

    def load(self) -> list[Document]:
        documents = []
        for filename in os.listdir(self.directory_path):
            filepath = os.path.join(self.directory_path, filename)
            if filename.endswith(".md") or filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                    documents.append(Document(page_content=text, metadata=self._get_metadata_for_file(filename, 1)))
            elif filename.endswith(".pdf"):
                try:
                    reader = pypdf.PdfReader(filepath)
                    # Limit to first 5 pages to keep indexing fast during development
                    pages_to_load = min(len(reader.pages), 5)
                    for i in range(pages_to_load):
                        page = reader.pages[i]
                        text = page.extract_text()
                        if text and text.strip():
                            documents.append(Document(
                                page_content=text,
                                metadata=self._get_metadata_for_file(filename, i + 1)
                            ))
                except Exception as e:
                    print(f"Lỗi khi đọc tệp PDF {filename}: {e}")
        return documents

