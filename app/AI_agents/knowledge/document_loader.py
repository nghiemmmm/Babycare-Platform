import os
import json
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
        files = os.listdir(self.directory_path)
        has_jsonl = any(f.endswith(".jsonl") for f in files)
        
        for filename in files:
            filepath = os.path.join(self.directory_path, filename)
            if filename.endswith(".jsonl"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for idx, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                # Lấy trường enriched_text làm page_content chính để embedding
                                content = data.get("enriched_text") or data.get("text", "")
                                if not content or not content.strip():
                                    continue
                                
                                # Metadata chỉ lấy riêng từng item trong jsonl
                                item_meta = data.get("metadata")
                                meta = dict(item_meta) if isinstance(item_meta, dict) else {}
                                meta["source"] = filename
                                meta["line"] = idx + 1
                                
                                # Lưu lại text gốc và context trong metadata để truy xuất khi cần
                                if "text" in data:
                                    meta["original_text"] = data["text"]
                                if "context" in data:
                                    meta["context"] = data["context"]
                                
                                documents.append(Document(page_content=content, metadata=meta))
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"Lỗi khi đọc tệp JSONL {filename}: {e}")
            elif not has_jsonl and filename.endswith(".pdf"):
                try:
                    reader = pypdf.PdfReader(filepath)
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text and text.strip():
                            metadata = self._get_metadata_for_file(filename, page=i+1)
                            documents.append(Document(page_content=text, metadata=metadata))
                except Exception as e:
                    print(f"Lỗi khi đọc tệp PDF {filename}: {e}")
            elif not has_jsonl and (filename.endswith(".txt") or filename.endswith(".md")):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        if text and text.strip():
                            metadata = self._get_metadata_for_file(filename)
                            documents.append(Document(page_content=text, metadata=metadata))
                except Exception as e:
                    print(f"Lỗi khi đọc tệp văn bản {filename}: {e}")
        return documents


