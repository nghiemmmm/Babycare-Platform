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

    # 1. Seed Master Vaccines Collection
    print("\n[1/3] Seeding master 'vaccines' collection...")
    vaccines = [
        # Sơ sinh
        {
            "code": "BCG",
            "name": "Vắc xin phòng bệnh Lao",
            "disease": "Bệnh Lao",
            "recommended_age_months": 0,
            "description": "Tiêm trong vòng 24 giờ đầu sau sinh hoặc càng sớm càng tốt."
        },
        {
            "code": "HepB-sosinhi",
            "name": "Vắc xin Viêm gan B (sơ sinh)",
            "disease": "Viêm gan B",
            "recommended_age_months": 0,
            "description": "Tiêm trong vòng 24 giờ đầu sau sinh."
        },
        # 2 tháng tuổi
        {
            "code": "DPT-HepB-Hib-1",
            "name": "Vắc xin 5 trong 1 (Mũi 1)",
            "disease": "Bạch hầu, Ho gà, Uốn ván, Viêm gan B, Viêm phổi/Viêm màng não mủ do Hib",
            "recommended_age_months": 2,
            "description": "Vắc xin phối hợp phòng 5 bệnh nguy hiểm ở trẻ nhỏ."
        },
        {
            "code": "OPV-1",
            "name": "Vắc xin Bại liệt đường uống (Lần 1)",
            "disease": "Bệnh Bại liệt",
            "recommended_age_months": 2,
            "description": "Nhỏ 2 giọt vào miệng trẻ."
        },
        # 3 tháng tuổi
        {
            "code": "DPT-HepB-Hib-2",
            "name": "Vắc xin 5 trong 1 (Mũi 2)",
            "disease": "Bạch hầu, Ho gà, Uốn ván, Viêm gan B, Viêm phổi/Viêm màng não mủ do Hib",
            "recommended_age_months": 3,
            "description": "Mũi thứ hai nhắc lại."
        },
        {
            "code": "OPV-2",
            "name": "Vắc xin Bại liệt đường uống (Lần 2)",
            "disease": "Bệnh Bại liệt",
            "recommended_age_months": 3,
            "description": "Nhỏ 2 giọt vào miệng trẻ."
        },
        # 4 tháng tuổi
        {
            "code": "DPT-HepB-Hib-3",
            "name": "Vắc xin 5 trong 1 (Mũi 3)",
            "disease": "Bạch hầu, Ho gà, Uốn ván, Viêm gan B, Viêm phổi/Viêm màng não mủ do Hib",
            "recommended_age_months": 4,
            "description": "Mũi thứ ba hoàn thành phác đồ cơ bản."
        },
        {
            "code": "OPV-3",
            "name": "Vắc xin Bại liệt đường uống (Lần 3)",
            "disease": "Bệnh Bại liệt",
            "recommended_age_months": 4,
            "description": "Nhỏ 2 giọt vào miệng trẻ."
        },
        # 5 tháng tuổi
        {
            "code": "IPV-1",
            "name": "Vắc xin Bại liệt dạng tiêm (Mũi 1)",
            "disease": "Bệnh Bại liệt",
            "recommended_age_months": 5,
            "description": "Tiêm bắp đùi để củng cố miễn dịch bại liệt."
        },
        # 9 tháng tuổi
        {
            "code": "Measles-1",
            "name": "Vắc xin Sởi đơn (Mũi 1)",
            "disease": "Bệnh Sởi",
            "recommended_age_months": 9,
            "description": "Tiêm dưới da phòng bệnh Sởi đơn."
        },
        # 12 tháng tuổi
        {
            "code": "JEV-1",
            "name": "Vắc xin Viêm não Nhật Bản (Mũi 1)",
            "disease": "Bệnh Viêm não Nhật Bản",
            "recommended_age_months": 12,
            "description": "Mũi khởi đầu tiêm phòng viêm não."
        },
        {
            "code": "JEV-2",
            "name": "Vắc xin Viêm não Nhật Bản (Mũi 2)",
            "disease": "Bệnh Viêm não Nhật Bản",
            "recommended_age_months": 12.5,
            "description": "Tiêm sau mũi 1 khoảng 1 đến 2 tuần."
        },
        # 18 tháng tuổi
        {
            "code": "DPT-4",
            "name": "Vắc xin Bạch hầu - Ho gà - Uốn ván (Mũi 4)",
            "disease": "Bạch hầu, Ho gà, Uốn ván",
            "recommended_age_months": 18,
            "description": "Tiêm nhắc lại phòng 3 bệnh truyền nhiễm."
        },
        {
            "code": "MR-1",
            "name": "Vắc xin Sởi - Rubella (Mũi nhắc)",
            "disease": "Bệnh Sởi, Bệnh Rubella",
            "recommended_age_months": 18,
            "description": "Tiêm nhắc sởi và bổ sung phòng ngừa bệnh Rubella."
        },
        # 24 tháng tuổi
        {
            "code": "JEV-3",
            "name": "Vắc xin Viêm não Nhật Bản (Mũi 3)",
            "disease": "Bệnh Viêm não Nhật Bản",
            "recommended_age_months": 24,
            "description": "Tiêm nhắc lại sau mũi thứ 2 khoảng 1 năm."
        }
    ]

    try:
        batch = db.batch()
        for v in vaccines:
            doc_ref = db.collection("vaccines").document(v["code"])
            batch.set(doc_ref, {
                "name": v["name"],
                "disease": v["disease"],
                "recommended_age_months": v["recommended_age_months"],
                "description": v["description"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        batch.commit()
        print(f"-> Successfully seeded {len(vaccines)} vaccines.")
    except Exception as e:
        print(f"Error seeding vaccines: {e}")
        return

    # 2. Seed Healthcare Tips Collection
    print("\n[2/3] Seeding master 'healthcare_tips' collection...")
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

    # 3. Seed Alert Rules
    print("\n[3/3] Seeding master 'alert_rules' collection...")
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
            "rule_code": "SLEEP_DEPRIVATION_ALERT",
            "name": "Cảnh báo Thiếu ngủ",
            "condition": "daily_sleep_hours <= 10",
            "severity": "low"
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
