# 2.4 Branching Strategy for AI/ML Teams

| Branch | Base From | Merges Into | Purpose & Production Gate |
|---|---|---|---|
| **`main`** *(master)* | — | — | **Production-ready code only.** Protected branch. Yêu cầu PR + CI pass + Model validation gate. Tự động deploy sang Production. |
| **`develop`** | `main` | `main` | **Integration branch.** Tất cả các nhánh feature/experiment merge vào đây trước. Tự động deploy sang môi trường Staging. |
| **`feature/xxx`** | `develop` | `develop` | Phát triển tính năng mới riêng lẻ (ngắn hạn). Ví dụ: `feature/add-rag-retrieval`, `feature/whisper-stt`. |
| **`experiment/xxx`** | `develop` | `develop` | **Đặc thù AI/ML:** Dành cho thử nghiệm mô hình, fine-tuning trọng số (ví dụ: `experiment/ast-finetuning-cry`). Lưu vết thử nghiệm song song với code. |
| **`hotfix/xxx`** | `main` | `main` & `develop` | Vá lỗi khẩn cấp trên Production. Tách từ `main`, merge ngược lại vào cả `main` và `develop`. |
| **`release/x.y.z`** | `develop` | `main` & `develop` | Chuẩn bị phát hành phiên bản mới. Kiểm thử cuối cùng, nâng version, cập nhật changelog. Merge vào `main` kèm tạo Git Tag. |

---

> 📖 *Xem hướng dẫn chi tiết & mẫu lệnh Git tại Skill:* **[.agents/skills/branch-management/SKILL.md](file:///d:/ViT/BABYCARE/babycare-ai/.agents/skills/branch-management/SKILL.md)**