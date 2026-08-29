import sys
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path("d:/ViT/BABYCARE/babycare-ai")
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.infrastructure.database import get_firestore_db

out_file = ROOT / "scripts" / "db_urls_report.txt"

def inspect():
    db = get_firestore_db()
    lines = []
    lines.append("=" * 60)
    lines.append("BÁO CÁO CÁC ĐƯỜNG DẪN URL ĐANG LƯU TRONG FIRESTORE DATABASE")
    lines.append("=" * 60)
    
    # 1. Babies
    lines.append("\n[1] BẢNG 'babies' (Hồ sơ em bé):")
    babies = list(db.collection("babies").stream())
    for b in babies:
        d = b.to_dict()
        lines.append(f"  - Document ID: {b.id}")
        lines.append(f"    * Tên bé: {d.get('name')}")
        lines.append(f"    * avatar_url: {d.get('avatar_url')}")
        
    # 2. Cry logs
    lines.append("\n[2] BẢNG 'cry_logs' (Nhật ký tiếng khóc):")
    total_cries = 0
    for b in babies:
        cries = list(b.reference.collection("cry_logs").stream())
        for c in cries:
            total_cries += 1
            cd = c.to_dict()
            lines.append(f"  - Bé {b.to_dict().get('name')} | Cry Log ID: {c.id}")
            lines.append(f"    * audio_url: {cd.get('audio_url')}")
            lines.append(f"    * prediction: {cd.get('prediction')}")
            lines.append(f"    * logged_at: {cd.get('logged_at')}")
    if total_cries == 0:
        lines.append("  (Chưa có bản ghi âm tiếng khóc nào trong subcollection)")
        
    lines.append("=" * 60)
    
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"DONE writing report to {out_file}")

if __name__ == "__main__":
    inspect()
