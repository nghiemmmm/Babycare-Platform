import os
import pypdf
from langchain_core.documents import Document

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
        return documents

