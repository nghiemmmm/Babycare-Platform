import os
import sys
import logging
from datetime import datetime, timezone, timedelta

# Add parent directory to sys.path to enable app module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.infrastructure.database.connection import get_firestore_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("seed_data")

USER_ID = "mock-user-id"
BABY_ID = "baby_bo_default"

def seed_database():
    logger.info("Bắt đầu khởi tạo dữ liệu mẫu (Seeding Firestore Database)...")
    db = get_firestore_db()
    now = datetime.now(timezone.utc).isoformat()

    # 1. Seed Baby Profile
    logger.info("1. Seeding Hồ sơ Bé ('babies')...")
    baby_ref = db.collection("babies").document(BABY_ID)
    baby_ref.set({
        "name": "Bé Bo",
        "birth_date": "2026-01-15",
        "gender": "Boy",
        "avatar_url": "/static/img/leo.png",
        "is_active": True,
        "guardians": [USER_ID],
        "created_at": now,
        "updated_at": now
    }, merge=True)

    # 2. Seed Guardians
    logger.info("2. Seeding Giám hộ ('guardians')...")
    guardians = [
        {
            "id": "g_1",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "name": "Sarah Jenkins",
            "relation": "Mẹ ruột (Chủ tài khoản)",
            "phone": "0901234567",
            "role": "Admin",
            "permissions": "Full Control",
            "created_at": now
        },
        {
            "id": "g_2",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "name": "David Jenkins",
            "relation": "Bố",
            "phone": "0909876543",
            "role": "Caregiver",
            "permissions": "View & Edit Logs",
            "created_at": now
        }
    ]
    for g in guardians:
        db.collection("guardians").document(g["id"]).set(g, merge=True)

    # 3. Seed Growth Measurements (Mốc 0 -> 6 tháng chuẩn WHO)
    logger.info("3. Seeding Tăng trưởng WHO ('growth_measurements' & sub-collections)...")
    growth_data = [
        {"id": "g_m0", "baby_id": BABY_ID, "date": "2026-01-15", "weight": 3.3, "height": 50.0, "head_circumference": 34.5, "logged_at": "2026-01-15T09:00:00Z", "created_at": now},
        {"id": "g_m1", "baby_id": BABY_ID, "date": "2026-02-15", "weight": 4.5, "height": 54.2, "head_circumference": 37.0, "logged_at": "2026-02-15T09:00:00Z", "created_at": now},
        {"id": "g_m2", "baby_id": BABY_ID, "date": "2026-03-15", "weight": 5.6, "height": 58.1, "head_circumference": 39.2, "logged_at": "2026-03-15T09:00:00Z", "created_at": now},
        {"id": "g_m3", "baby_id": BABY_ID, "date": "2026-04-15", "weight": 6.4, "height": 61.4, "head_circumference": 40.8, "logged_at": "2026-04-15T09:00:00Z", "created_at": now},
        {"id": "g_m4", "baby_id": BABY_ID, "date": "2026-05-15", "weight": 7.0, "height": 64.0, "head_circumference": 42.0, "logged_at": "2026-05-15T09:00:00Z", "created_at": now},
        {"id": "g_m5", "baby_id": BABY_ID, "date": "2026-06-15", "weight": 7.5, "height": 66.2, "head_circumference": 43.1, "logged_at": "2026-06-15T09:00:00Z", "created_at": now},
        {"id": "g_m6", "baby_id": BABY_ID, "date": "2026-07-15", "weight": 7.9, "height": 68.0, "head_circumference": 44.0, "logged_at": "2026-07-15T09:00:00Z", "created_at": now},
    ]
    for gm in growth_data:
        db.collection("growth_measurements").document(gm["id"]).set(gm, merge=True)
        db.collection("babies").document(BABY_ID).collection("growth_logs").document(gm["id"]).set({
            "height": gm["height"],
            "weight": gm["weight"],
            "head_circumference": gm["head_circumference"],
            "logged_at": gm["logged_at"],
            "who_status": {
                "age_in_months": float(gm["id"].replace("g_m", "")),
                "weight_status": "normal",
                "height_status": "normal",
                "head_circumference_status": "normal"
            }
        }, merge=True)

    # 4. Seed Feeds (Cữ bú & Dinh dưỡng)
    logger.info("4. Seeding Nhật ký Dinh dưỡng ('nutrition_feeds')...")
    feeds_data = [
        {
            "id": "feed_1",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "type": "Formula",
            "details": "Sữa công thức Nan Optipro 2",
            "amount": 150,
            "time": "12:00 PM",
            "date": "Today",
            "created_at": now
        },
        {
            "id": "feed_2",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "type": "Breast",
            "details": "Sữa mẹ bú trực tiếp (Bên trái)",
            "amount": 120,
            "time": "08:30 AM",
            "date": "Today",
            "created_at": now
        },
        {
            "id": "feed_3",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "type": "Solids",
            "details": "Bột ăn dặm Yến mạch + Táo tây hấp nghiền",
            "amount": 80,
            "time": "06:00 PM",
            "date": "Today",
            "created_at": now
        }
    ]
    for f in feeds_data:
        db.collection("nutrition_feeds").document(f["id"]).set(f, merge=True)

    # 5. Seed Food Ingredients & Allergen Warnings
    logger.info("5. Seeding Thực phẩm đã thử & Cảnh báo dị ứng ('food_ingredients')...")
    ingredients = [
        {"id": "ing_1", "baby_id": BABY_ID, "user_id": USER_ID, "name": "🍎 Táo tây hấp nghiền", "reaction": "Loved it", "created_at": now},
        {"id": "ing_2", "baby_id": BABY_ID, "user_id": USER_ID, "name": "🥣 Yến mạch mịn", "reaction": "Loved it", "created_at": now},
        {"id": "ing_3", "baby_id": BABY_ID, "user_id": USER_ID, "name": "🥕 Cà rốt luộc", "reaction": "Neutral", "created_at": now},
        {"id": "ing_4", "baby_id": BABY_ID, "user_id": USER_ID, "name": "🥛 Sữa bò công thức", "reaction": "Neutral", "created_at": now},
        {"id": "ing_5", "baby_id": BABY_ID, "user_id": USER_ID, "name": "🥜 Bơ đậu phộng thử lần 1", "reaction": "Allergic Reaction", "created_at": now}
    ]
    for ing in ingredients:
        db.collection("food_ingredients").document(ing["id"]).set(ing, merge=True)

    # 6. Seed Medication & Health Logs
    logger.info("6. Seeding Nhật ký Dùng thuốc & Bệnh trạng ('medication_logs', 'health_incidents')...")
    medications = [
        {
            "id": "med_1",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "medication_name": "Paracetamol 150mg",
            "name": "Paracetamol 150mg",
            "dosage": "1 gói (150mg)",
            "time": "08:00 AM",
            "logged_at": f"{datetime.now().strftime('%Y-%m-%d')} 08:00:00",
            "date": "Today",
            "prescribed_by": "Dr. Aris (Nhi khoa)",
            "status": "Active",
            "notes": "Dùng khi nhiệt độ > 38.5°C, mỗi liều cách nhau 4-6 tiếng.",
            "created_at": now
        },
        {
            "id": "med_2",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "medication_name": "Siro ho thảo dược Prospan",
            "name": "Siro ho thảo dược Prospan",
            "dosage": "2.5ml",
            "time": "02:00 PM",
            "logged_at": f"{datetime.now().strftime('%Y-%m-%d')} 14:00:00",
            "date": "Today",
            "prescribed_by": "Dr. Aris (Nhi khoa)",
            "status": "Active",
            "notes": "Uống 2 lần/ngày sau khi ăn dặm.",
            "created_at": now
        }
    ]
    for m in medications:
        db.collection("medication_logs").document(m["id"]).set(m, merge=True)
        db.collection("babies").document(BABY_ID).collection("medication_logs").document(m["id"]).set(m, merge=True)

    incidents = [
        {
            "id": "inc_1",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "title": "Sốt nhẹ sau tiêm chủng 5-trong-1",
            "date": "Hôm nay",
            "time": "08:15 AM",
            "status": "Confirmed",
            "symptoms": ["🌡️ Sốt 38.2°C", "😴 Quấy khóc nhẹ", "🔴 Sưng nhẹ vết tiêm"],
            "treatment": "Uống Paracetamol 150mg theo chỉ định, chườm ấm trán nách, cho bú tăng cường.",
            "prescribedBy": "Bác sĩ nhi khoa Aris",
            "temp": 38.2,
            "created_at": now
        },
        {
            "id": "inc_2",
            "baby_id": BABY_ID,
            "user_id": USER_ID,
            "title": "Viêm họng cấp tính",
            "date": "Hôm qua",
            "time": "04:30 PM",
            "status": "Resolved",
            "symptoms": ["🌬️ Ho khan", "👃 Sổ mũi nhẹ", "🥵 Đau họng"],
            "treatment": "Dùng siro ho thảo dược Prospan, nhỏ mũi nước muối sinh lý 0.9% và giữ ấm cổ.",
            "prescribedBy": "AI Y Khoa Gợi Ý",
            "temp": 37.8,
            "created_at": now
        }
    ]
    for inc in incidents:
        db.collection("health_incidents").document(inc["id"]).set(inc, merge=True)
        db.collection("babies").document(BABY_ID).collection("health_records").document(inc["id"]).set(inc, merge=True)

    # 7. Seed Chat Threads
    logger.info("7. Seeding Cuộc trò chuyện AI ('chat_threads')...")
    threads = [
        {
            "id": "thread_default",
            "user_id": USER_ID,
            "title": "Baby Progress Chat (Tổng quan)",
            "last_updated": now,
            "created_at": now
        },
        {
            "id": "thread_nutrition",
            "user_id": USER_ID,
            "title": "Tư vấn Thực đơn Ăn dặm 6 Tháng",
            "last_updated": now,
            "created_at": now
        },
        {
            "id": "thread_vaccine",
            "user_id": USER_ID,
            "title": "Lịch tiêm phòng Mũi 6 Tháng & Nhắc nhắc",
            "last_updated": now,
            "created_at": now
        }
    ]
    for t in threads:
        db.collection("chat_threads").document(t["id"]).set(t, merge=True)

    logger.info("SUCCESS: Đã hoàn tất nạp đầy đủ Dữ liệu mẫu vào Firestore Database!")

if __name__ == "__main__":
    seed_database()
