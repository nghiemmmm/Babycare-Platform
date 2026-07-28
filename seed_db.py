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
    print("=== STARTING COMPREHENSIVE FIRESTORE DATABASE SEEDING FOR DEMO USER ===")
    
    try:
        db = get_firestore_db()
        print("Successfully connected to Firebase Firestore.")
    except Exception as e:
        print(f"Error connecting to Firebase: {e}")
        return

    # 1. Seed Healthcare Tips Collection
    print("\n[1/7] Seeding master 'healthcare_tips' collection...")
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
        },
        {
            "slug": "xu-ly-di-ung-dau-nanh",
            "title": "Chăm sóc trẻ bị dị ứng đạm đậu nành",
            "category": "Dị ứng & Dinh dưỡng",
            "min_age_months": 6,
            "max_age_months": 24,
            "content": "Tránh hoàn toàn các sản phẩm từ đậu nành như sữa đậu nành, đậu phụ, tương, dầu đậu nành. Khi mua thực phẩm đóng gói, luôn đọc kỹ nhãn thành phần để phát hiện Soy Protein / Soy Lecithin."
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

    # 2. Seed Alert Rules
    print("\n[2/7] Seeding master 'alert_rules' collection...")
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
            "name": "Cảnh báo Dị ứng Đậu nành",
            "condition": "allergy == 'Đậu nành'",
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

    # 3. Seed Demo Account & Sample Babies
    print("\n[3/7] Seeding Demo Account & Sample Baby Data...")
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

        user_uid = demo_user.uid

        # Firestore User Profile
        user_ref = db.collection("users").document(user_uid)
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
        leo_id = f"baby_{user_uid}_leo"
        bo_id = f"baby_{user_uid}_bo"

        babies = [
            {
                "id": leo_id,
                "user_id": user_uid,
                "guardians": [user_uid],
                "name": "Leo",
                "birth_date": "2023-04-20",
                "gender": "boy",
                "allergies": ["Đậu nành"],
                "avatar_url": "/static/img/leo.png",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": bo_id,
                "user_id": user_uid,
                "guardians": [user_uid],
                "name": "Bo",
                "birth_date": "2023-11-15",
                "gender": "girl",
                "allergies": [],
                "avatar_url": "/static/img/bo.png",
                "is_active": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for b in babies:
            db.collection("babies").document(b["id"]).set(b, merge=True)
            # Also seed simplified fallback ID for static frontend queries if needed
            if b["id"] == leo_id:
                db.collection("babies").document("baby-leo").set(b, merge=True)
            if b["id"] == bo_id:
                db.collection("babies").document("baby-bo").set(b, merge=True)

        print(f"-> Successfully seeded {len(babies)} sample baby profiles for Demo User.")

        # 4. Seed Guardians
        print("\n[4/7] Seeding Guardians...")
        guardians = [
            {
                "id": f"g1_{user_uid}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "Minh Anh",
                "relation": "Mẹ ruột (Chủ tài khoản)",
                "email": demo_email,
                "phone": "0901234567",
                "role": "ADMIN",
                "status": "Synced",
                "permissions": "Full Control",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"g2_{user_uid}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "Hoàng Nam",
                "relation": "Bố",
                "email": "hoangnam@family.vn",
                "phone": "0909876543",
                "role": "Caregiver",
                "status": "Synced",
                "permissions": "View & Edit Logs",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"g3_{user_uid}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "Bà Nội Kim Yến",
                "relation": "Bà nội",
                "email": "kimyen.grandma@family.vn",
                "phone": "0988112233",
                "role": "Viewer",
                "status": "Invited",
                "permissions": "View Only",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for g in guardians:
            db.collection("guardians").document(g["id"]).set(g, merge=True)

        # 5. Seed Growth Measurements (WHO trajectory)
        print("\n[5/7] Seeding Growth Measurements for Leo & Bo...")
        growth_logs_leo = [
            {
                "id": f"m0_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-04-20",
                "age_months": 0,
                "weight": 3.3,
                "height": 50.0,
                "head_circumference": 34.5,
                "status": "Normal",
                "notes": "Chỉ số sinh thường hoàn toàn khỏe mạnh.",
                "logged_at": "2023-04-20T08:00:00Z"
            },
            {
                "id": f"m1_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-05-20",
                "age_months": 1,
                "weight": 4.4,
                "height": 54.0,
                "head_circumference": 37.0,
                "status": "Normal",
                "notes": "Tăng trưởng tốt tháng đầu tiên.",
                "logged_at": "2023-05-20T09:00:00Z"
            },
            {
                "id": f"m2_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-06-20",
                "age_months": 2,
                "weight": 5.5,
                "height": 57.8,
                "head_circumference": 39.0,
                "status": "Normal",
                "notes": "Phát triển theo đường trung bình WHO.",
                "logged_at": "2023-06-20T09:00:00Z"
            },
            {
                "id": f"m3_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-07-20",
                "age_months": 3,
                "weight": 6.2,
                "height": 61.0,
                "head_circumference": 40.5,
                "status": "Normal",
                "notes": "Đạt mốc lẫy thành thạo.",
                "logged_at": "2023-07-20T09:00:00Z"
            },
            {
                "id": f"m4_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-08-15",
                "age_months": 4,
                "weight": 6.6,
                "height": 63.2,
                "head_circumference": 41.5,
                "status": "Normal",
                "notes": "Cân nặng tăng đều, bác sĩ khen bé lanh lợi.",
                "logged_at": "2023-08-15T09:00:00Z"
            },
            {
                "id": f"m5_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-09-20",
                "age_months": 5,
                "weight": 6.8,
                "height": 64.0,
                "head_circumference": 41.8,
                "status": "Normal",
                "notes": "Tiến trình tăng trưởng ổn định.",
                "logged_at": "2023-09-20T10:00:00Z"
            },
            {
                "id": f"m6_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "date": "2023-10-24",
                "age_months": 6,
                "weight": 7.2,
                "height": 66.0,
                "head_circumference": 42.5,
                "status": "Height Alert (Risk of Stunting)",
                "notes": "Leo có chiều cao tiệm cận chuẩn dưới WHO (bằng percentile 15). Cần bổ sung Vitamin D3 K2 và tập tummy time năng động.",
                "logged_at": "2023-10-24T10:00:00Z"
            }
        ]

        for g in growth_logs_leo:
            db.collection("growth_records").document(g["id"]).set(g, merge=True)
            db.collection("growth_measurements").document(g["id"]).set(g, merge=True)
            db.collection("babies").document(leo_id).collection("growth_logs").document(g["id"]).set(g, merge=True)

        # Growth records for Bo
        growth_logs_bo = [
            {
                "id": f"m0_{bo_id}",
                "baby_id": bo_id,
                "user_id": user_uid,
                "date": "2023-11-15",
                "age_months": 0,
                "weight": 3.1,
                "height": 49.0,
                "head_circumference": 33.8,
                "status": "Normal",
                "notes": "Bé sinh thường khỏe mạnh.",
                "logged_at": "2023-11-15T08:00:00Z"
            },
            {
                "id": f"m3_{bo_id}",
                "baby_id": bo_id,
                "user_id": user_uid,
                "date": "2024-02-15",
                "age_months": 3,
                "weight": 5.8,
                "height": 59.5,
                "head_circumference": 39.5,
                "status": "Normal",
                "notes": "Phát triển rất tốt.",
                "logged_at": "2024-02-15T09:00:00Z"
            }
        ]
        for g in growth_logs_bo:
            db.collection("growth_records").document(g["id"]).set(g, merge=True)
            db.collection("growth_measurements").document(g["id"]).set(g, merge=True)
            db.collection("babies").document(bo_id).collection("growth_logs").document(g["id"]).set(g, merge=True)

        # 6. Seed Nutrition Feeds & Food Trial Ingredients (Allergy Soy)
        print("\n[6/7] Seeding Nutrition Feeds & Allergen Ingredients...")
        feeds = [
            {
                "id": f"feed1_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "type": "Formula",
                "details": "180ml Sữa Nan Optipro 2",
                "amount": 180,
                "time": "01:00 PM",
                "date": "Today",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"feed2_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "type": "Solids",
                "details": "Bột ăn dặm Yến mạch + Táo tây hấp nghiền",
                "amount": 1,
                "time": "10:30 AM",
                "date": "Today",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"feed3_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "type": "Breast",
                "details": "Sữa mẹ bú trực tiếp (Bên trái 15 phút)",
                "amount": 120,
                "time": "08:00 AM",
                "date": "Today",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for f in feeds:
            db.collection("nutrition_feeds").document(f["id"]).set(f, merge=True)

        ingredients = [
            {
                "id": f"ing1_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "🍎 Táo tây hấp nghiền",
                "reaction": "Loved it",
                "date": "2023-10-23",
                "notes": "Bé ăn ngon miệng, không trớ.",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"ing2_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "🥣 Bột yến mạch mịn",
                "reaction": "Loved it",
                "date": "2023-10-20",
                "notes": "Tốt cho tiêu hóa.",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"ing3_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "🥕 Cà rốt luộc nghiền",
                "reaction": "Neutral",
                "date": "2023-10-18",
                "notes": "Bé ăn bình thường.",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"ing4_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "🥦 Súp lơ xanh hấp",
                "reaction": "Neutral",
                "date": "2023-10-15",
                "notes": "Bé nhè bớt một chút.",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"ing5_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "name": "🚨 Sữa đậu nành & Đậu phụ thử nghiệm",
                "reaction": "Allergic Reaction",
                "date": "2023-10-10",
                "notes": "Bé nổi mẩn đỏ xung quanh miệng và ngứa ngáy sau 20 phút. Bác sĩ xác nhận dị ứng đạm đậu nành!",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for ing in ingredients:
            db.collection("food_ingredients").document(ing["id"]).set(ing, merge=True)

        # 7. Seed Medication Logs, Health Incidents & Chat Threads
        print("\n[7/7] Seeding Medication Logs, Health Incidents & AI Chat Threads...")
        medications = [
            {
                "id": f"med1_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "medication_name": "Hapacol 150mg (Paracetamol)",
                "name": "Hapacol 150mg (Paracetamol)",
                "dosage": "150mg (1 gói)",
                "time": "11:45 AM",
                "date": "Today",
                "prescribed_by": "Dr. Aris (Nhi khoa)",
                "status": "Active",
                "notes": "Uống khi sốt > 38.5°C, mỗi liều cách 4-6 tiếng.",
                "logged_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"med2_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "medication_name": "Vitamin D3 K2",
                "name": "Vitamin D3 K2",
                "dosage": "2 giọt",
                "time": "08:00 AM",
                "date": "Today",
                "prescribed_by": "Bổ sung hàng ngày",
                "status": "Active",
                "notes": "Nhỏ trực tiếp vào miệng bé buổi sáng.",
                "logged_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": f"med3_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "medication_name": "Siro ho thảo dược Prospan",
                "name": "Siro ho thảo dược Prospan",
                "dosage": "2.5ml",
                "time": "02:00 PM",
                "date": "Today",
                "prescribed_by": "Dr. Aris (Nhi khoa)",
                "status": "Active",
                "notes": "Uống 2 lần/ngày sau khi ăn dặm.",
                "logged_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for m in medications:
            db.collection("medication_logs").document(m["id"]).set(m, merge=True)
            db.collection("babies").document(leo_id).collection("medication_logs").document(m["id"]).set(m, merge=True)

        incidents = [
            {
                "id": f"inc1_{leo_id}",
                "baby_id": leo_id,
                "user_id": user_uid,
                "title": "Sốt nhẹ sau tiêm chủng 5-trong-1 Mũi 3",
                "date": "2023-10-15",
                "status": "Recovered",
                "symptoms": "Sốt 38.2°C, quấy khóc nhẹ, chỗ tiêm đùi trái hơi sưng vồng đỏ.",
                "treatment": "Uống 1 gói Hapacol 150mg, chườm mát, tăng cường bú mẹ.",
                "doctor_notes": "Phản ứng bình thường sau vắc xin. Đã hạ sốt hoàn toàn sau 24h.",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for inc in incidents:
            db.collection("health_incidents").document(inc["id"]).set(inc, merge=True)

        # Chat threads & messages
        chat_thread_ref = db.collection("chat_threads").document(f"thread_{user_uid}_leo")
        chat_thread_ref.set({
            "id": f"thread_{user_uid}_leo",
            "user_id": user_uid,
            "baby_id": leo_id,
            "title": "Tư vấn Thực đơn Ăn dặm Dị ứng Đậu nành cho Bé Leo",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }, merge=True)

        messages = [
            {
                "id": f"c1_{user_uid}",
                "role": "assistant",
                "content": "Chào mẹ Minh Anh! Em đã kiểm tra hồ sơ của bé Leo (6 tháng tuổi). Leo đang có chiều cao 66cm và cân nặng 7.2kg. Do bé có tiền sử **Dị ứng Đậu nành**, em đã thiết lập cảnh báo lọc tự động toàn bộ món ăn chứa Soy Protein/Soy Lecithin trong gợi ý ăn dặm. Mẹ có cần em tư vấn thêm thực đơn yến mạch + rau củ cho bé hôm nay không ạ?",
                "timestamp": "11:46 AM",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for msg in messages:
            chat_thread_ref.collection("messages").document(msg["id"]).set(msg, merge=True)

        print("\n=== COMPREHENSIVE SEEDING COMPLETED SUCCESSFULLY! ===")

    except Exception as e:
        print(f"Error seeding Demo account data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_database()
