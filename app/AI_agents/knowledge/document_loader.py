import os
import json
from langchain_core.documents import Document

# Các pattern nhận biết chunk bị nhiễm rác từ LLM enrichment lỗi
_NOISE_PATTERNS = [
    "are correctwen",
    "an AI from Alibaba",
    "a language model from Alibaba",
    "Your response did not follow",
    "it's too brief",
    "expand significantly",
    "I will follow the instructions",
    "I are knowledgeable",
    "I are an large language model",
    "are askedwen",
    "Sentence should not repeat",
    "metadata metadata for improved",
    "CLOCKS",
    "This adhering to the rules",
    "This it information is located",
]

def _is_noisy(text: str) -> bool:
    """Trả về True nếu text chứa artifact từ quá trình LLM enrichment bị lỗi."""
    text_lower = text.lower()
    return any(p.lower() in text_lower for p in _NOISE_PATTERNS)


class DocumentLoader:
    def __init__(self, directory_path: str = "app/AI_agents/knowledge/documents"):
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

    def _load_jsonl(self, filepath: str, domain: str) -> list[Document]:
        """
        Load file .jsonl — mỗi dòng là một chunk JSON với các trường:
          - enriched_text: context + text gốc (dùng để embed — semantic phong phú hơn)
          - text: nội dung gốc (lưu vào metadata để fallback / debug)
          - metadata: chapter, section, subsection

        Lọc bỏ:
          - Chunk có enriched_text rỗng
          - Chunk có enriched_text bị nhiễm rác AI enrichment lỗi
        """
        filename = os.path.basename(filepath)
        documents = []
        skipped_empty = 0
        skipped_noisy = 0

        with open(filepath, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue

                enriched = row.get("enriched_text", "").strip()
                text_raw = row.get("text", "").strip()
                meta = row.get("metadata", {}) or {}

                # Bỏ chunk rỗng
                if not enriched:
                    skipped_empty += 1
                    continue

                # Bỏ chunk bị nhiễm rác LLM
                if _is_noisy(enriched):
                    skipped_noisy += 1
                    continue

                documents.append(Document(
                    page_content=enriched,
                    metadata={
                        "source": filename,
                        "domain": domain,
                        "text_original": text_raw[:200],   # lưu text gốc để debug
                        "chapter": meta.get("chapter"),
                        "section": meta.get("section"),
                        "subsection": meta.get("subsection"),
                        "line": lineno,
                    }
                ))

        print(
            f"[DocumentLoader] {filename}: "
            f"loaded={len(documents)}, "
            f"skipped_empty={skipped_empty}, "
            f"skipped_noisy={skipped_noisy}"
        )
        return documents

    def load(self) -> list[Document]:
        documents = []
        for root, _dirs, filenames in os.walk(self.directory_path):
            # Domain = tên thư mục con trực tiếp chứa file (vd "allergy_safety", "illness_diet",
            # "nutrition_general"); file nằm ngay ở thư mục gốc documents/ -> domain mặc định "general".
            domain = "general" if root == self.directory_path else os.path.basename(root)
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if filename.endswith(".md") or filename.endswith(".txt"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        documents.append(Document(page_content=text, metadata={"source": filename, "domain": domain}))
                elif filename.endswith(".pdf"):
                    try:
                        import pypdf
                        reader = pypdf.PdfReader(filepath)
                        for i, page in enumerate(reader.pages):
                            text = page.extract_text()
                            if text and text.strip():
                                documents.append(Document(
                                    page_content=text,
                                    metadata={"source": filename, "page": i + 1, "domain": domain}
                                ))
                    except Exception as e:
                        print(f"Lỗi khi đọc tệp PDF {filename}: {e}")
                elif filename.endswith(".jsonl"):
                    documents.extend(self._load_jsonl(filepath, domain))
        return documents


