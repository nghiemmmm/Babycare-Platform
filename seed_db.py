import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add current directory to path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables from .env
load_dotenv()

from app.infrastructure.database.connection import get_firestore_db

def seed_database():
    print("=== STARTING FIRESTORE DATABASE SEEDING ===")
    
    try:
        db = get_firestore_db()
        print("Successfully connected to Firebase Firestore.")
    except Exception as e:
        print(f"Error connecting to Firebase: {e}")
        return

    # 1. Seed Healthcare Tips Collection
    print("\n[1/2] Seeding master 'healthcare_tips' collection...")
    tips = [
        {
            "slug": "cho-con-bu-dung-tu-the",
            "title": "Hướng dẫn tư thế cho bé bú đúng cách",
            "category": "Dinh dưỡng",
            "min_age_months": 0,
            "max_age_months": 6,
            "content": "Bé cần ngậm sâu quầng vú của mẹ thay vì chỉ ngậm núm vú. Tư thế cho bú đúng giúp bé bú được nhiều sữa hơn và tránh làm đau mẹ. Bụng bé phải áp sát vào bụng mẹ, đầu và thân bé thẳng hàng."
        },
        {
            "slug": "thiet-lap-giac-ngu-cho-tre",
            "title": "Thiết lập lịch ngủ khoa học cho trẻ sơ sinh",
            "category": "Giấc ngủ",
            "min_age_months": 0,
            "max_age_months": 3,
            "content": "Trẻ sơ sinh ngủ từ 16-18 tiếng mỗi ngày. Hãy phân biệt ngày và đêm cho bé bằng cách giữ phòng sáng vào ban ngày và hoàn toàn tối, yên tĩnh vào ban đêm. Không nên kích thích bé trước khi đi ngủ."
        },
        {
            "slug": "bat-dau-an-dam",
            "title": "Bí quyết bắt đầu cho bé ăn dặm lành mạnh",
            "category": "Ăn dặm",
            "min_age_months": 6,
            "max_age_months": 12,
            "content": "Trẻ 6 tháng tuổi bắt đầu bước vào giai đoạn ăn dặm. Bắt đầu bằng bột loãng, mịn và chuyển dần sang sệt, đặc. Nên cho bé thử các loại rau củ đơn lẻ trước để phát hiện dị ứng thực phẩm."
        }
    ]

    try:
        batch = db.batch()
        for t in tips:
            doc_ref = db.collection("healthcare_tips").document(t["slug"])
            batch.set(doc_ref, {
                "title": t["title"],
                "category": t["category"],
                "min_age_months": t["min_age_months"],
                "max_age_months": t["max_age_months"],
                "content": t["content"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        batch.commit()
        print(f"-> Successfully seeded {len(tips)} healthcare tips.")
    except Exception as e:
        print(f"Error seeding tips: {e}")
        return

    # 2. Seed Alert Rules
    print("\n[2/2] Seeding master 'alert_rules' collection...")
    rules = [
        {
            "rule_code": "FEVER_ALERT",
            "name": "Cảnh báo Sốt cao",
            "condition": "body_temperature >= 38.5",
            "severity": "high"
        },
        {
            "rule_code": "WEIGHT_LOSS_ALERT",
            "name": "Cảnh báo Sụt cân",
            "condition": "weight_change_percentage <= -5.0",
            "severity": "medium"
        },
        {
            "rule_code": "ALLERGY_ALERT",
            "name": "Cảnh báo Dị ứng Ăn dặm",
            "condition": "reaction == 'allergic'",
            "severity": "high"
        }
    ]

    try:
        batch = db.batch()
        for r in rules:
            doc_ref = db.collection("alert_rules").document(r["rule_code"])
            batch.set(doc_ref, {
                "name": r["name"],
                "condition": r["condition"],
                "severity": r["severity"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        batch.commit()
        print(f"-> Successfully seeded {len(rules)} alert rules.")
    except Exception as e:
        print(f"Error seeding alert rules: {e}")
        return

    print("\n=== DATABASE SEEDING COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    seed_database()
