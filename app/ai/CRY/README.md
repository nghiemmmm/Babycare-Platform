# 👶 **CRY — Standalone Infant Cry Classification Module**

Thư mục độc lập chứa toàn bộ mã nguồn, dữ liệu nhãn và weights mô hình phục vụ suy luận tiếng khóc trẻ em.

---

## 📂 **Cấu trúc thư mục**

```text
CRY/
├── inference.py               # Script suy luận chính (CLI & API function)
├── README.md                  # Hướng dẫn sử dụng
├── models/
│   ├── __init__.py            # Export ASTModel
│   └── ast_models.py          # Kiến trúc Audio Spectrogram Transformer
├── data/
│   └── esc_class_labels_indices.csv # Danh mục 9 nhãn tiếng khóc
└── weights/
    └── best_audio_model.pth   # Trọng số mô hình đã huấn luyện (~350MB)
```

---

## 🚀 **Cách chạy suy luận**

### **1. Chạy từ Dòng lệnh (CLI)**
```bash
python CRY/inference.py --audio_path "path/to/baby_cry_sample.wav"
```

### **2. Import trực tiếp vào mã Python khác**
```python
from CRY.inference import inference

result = inference("path/to/baby_cry_sample.wav")
print(f"Dự đoán: {result['label']} (Độ tin cậy: {result['confidence']})")
print("Chi tiết điểm số từng lớp:", result['scores'])
```

---

## 📊 **Kết quả đầu ra (JSON Format)**
```json
{
  "label": "hu",
  "confidence": 0.9421,
  "scores": {
    "bp": 0.0123,
    "bu": 0.0211,
    "ch": 0.0055,
    "dc": 0.0142,
    "dk": 0.0089,
    "hu": 0.9421,
    "lo": 0.0102,
    "sc": 0.0078,
    "ti": 0.0034
  },
  "duration": 5.2,
  "model_version": "AST base384 (Infant Cry Fine-tuned)"
}
```
