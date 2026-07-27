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

    # 3. Seed Demo Account & Sample Babies
    print("\n[3/3] Seeding Demo Account & Sample Baby Data...")
    demo_email = "nghiem@babycare.com"
    demo_password = "Nghiem1234"
    demo_name = "Minh Anh (Mẹ bé Leo)"

    from firebase_admin import auth
    try:
        try:
            demo_user = auth.get_user_by_email(demo_email)
            auth.update_user(demo_user.uid, password=demo_password, display_name=demo_name)
            print(f"-> Updated existing Demo User in Firebase Auth: {demo_user.uid}")
        except auth.UserNotFoundError:
            demo_user = auth.create_user(
                email=demo_email,
                password=demo_password,
                display_name=demo_name
            )
            print(f"-> Created new Demo User in Firebase Auth: {demo_user.uid}")

        # Firestore User Profile
        user_ref = db.collection("users").document(demo_user.uid)
        user_ref.set({
            "email": demo_email,
            "name": demo_name,
            "role": "USER",
            "active": True,
            "first_login": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "last_login_at": datetime.now(timezone.utc).isoformat()
        }, merge=True)

        # Seed Babies
        babies = [
            {
                "id": f"baby_{demo_user.uid}_leo",
                "user_id": demo_user.uid,
                "guardians": [demo_user.uid],
                "name": "Leo",
                "birth_date": "2023-04-20",
                "gender": "boy",
                "allergies": ["Đậu nành"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"baby_{demo_user.uid}_bo",
                "user_id": demo_user.uid,
                "guardians": [demo_user.uid],
                "name": "Bo",
                "birth_date": "2023-11-15",
                "gender": "girl",
                "allergies": [],
                "is_active": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for b in babies:
            db.collection("babies").document(b["id"]).set(b, merge=True)

        print(f"-> Successfully seeded {len(babies)} sample baby profiles for Demo User.")

        # Seed Growth Records for Leo
        leo_id = f"baby_{demo_user.uid}_leo"
        growth_logs = [
            {
                "id": f"m1_{leo_id}",
                "baby_id": leo_id,
                "user_id": demo_user.uid,
                "date": "2023-10-24",
                "age_months": 6,
                "weight": 7.2,
                "height": 66.0,
                "head_circumference": 42.5,
                "notes": "Chiều cao hơi dưới chuẩn WHO median, cân nặng bình thường.",
                "logged_at": "2023-10-24T10:00:00Z"
            },
            {
                "id": f"m2_{leo_id}",
                "baby_id": leo_id,
                "user_id": demo_user.uid,
                "date": "2023-09-20",
                "age_months": 5,
                "weight": 6.8,
                "height": 64.0,
                "head_circumference": 41.8,
                "notes": "Tăng trưởng đều.",
                "logged_at": "2023-09-20T10:00:00Z"
            }
        ]
        for g in growth_logs:
            db.collection("growth_records").document(g["id"]).set(g, merge=True)
        print(f"-> Successfully seeded growth logs for Demo User.")

        # Seed Medication Logs for Leo
        med_logs = [
            {
                "id": f"med1_{leo_id}",
                "baby_id": leo_id,
                "user_id": demo_user.uid,
                "medication_name": "Hapacol 150mg (Paracetamol)",
                "dosage": "150mg",
                "prescribed_by": "Bác sĩ Nhi khoa",
                "logged_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"med2_{leo_id}",
                "baby_id": leo_id,
                "user_id": demo_user.uid,
                "medication_name": "Vitamin D3 K2",
                "dosage": "2 giọt",
                "prescribed_by": "Bổ sung hàng ngày",
                "logged_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for m in med_logs:
            db.collection("medication_logs").document(m["id"]).set(m, merge=True)
        print(f"-> Successfully seeded medication logs for Demo User.")

    except Exception as e:
        print(f"Error seeding Demo account: {e}")

    print("\n=== DATABASE SEEDING COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    seed_database()

