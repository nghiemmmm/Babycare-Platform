"""
Script seed dữ liệu mẫu vào Firestore cho bé Leo.
Chạy: PYTHONPATH=. python scripts/seed_demo_data.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone, date, timedelta
from app.infrastructure.database import get_firestore_db

# ─── Config ────────────────────────────────────────────────────────────────────
BABY_ID = None  # Sẽ lấy từ Firestore (bé đầu tiên của mock-user-id)
USER_ID = "mock-user-id"
TODAY = date.today().isoformat()
NOW = datetime.now(timezone.utc)


def get_baby_id(db) -> str:
    """Lấy baby_id đầu tiên của mock-user-id."""
    docs = list(db.collection("babies").where("guardians", "array_contains", USER_ID).limit(1).stream())
    if not docs:
        raise RuntimeError("Khong tim thay be. Hay chay backend truoc de auto-seed Leo.")
    baby_id = docs[0].id
    print(f"[OK] Su dung baby_id: {baby_id} ({docs[0].to_dict().get('name')})")
    return baby_id


def seed_growth_logs(db, baby_id: str):
    """Seed 3 bản ghi đo tăng trưởng."""
    col = db.collection("babies").document(baby_id).collection("growth_logs")

    # Xóa existing để tránh duplicate
    for doc in col.stream():
        doc.reference.delete()

    logs = [
        {
            "height": 66.0, "weight": 7.2, "head_circumference": 42.5,
            "logged_at": (NOW - timedelta(days=60)).isoformat(),
            "date": (date.today() - timedelta(days=60)).isoformat()
        },
        {
            "height": 64.0, "weight": 6.8, "head_circumference": 41.8,
            "logged_at": (NOW - timedelta(days=90)).isoformat(),
            "date": (date.today() - timedelta(days=90)).isoformat()
        },
        {
            "height": 62.5, "weight": 6.3, "head_circumference": 41.0,
            "logged_at": (NOW - timedelta(days=120)).isoformat(),
            "date": (date.today() - timedelta(days=120)).isoformat()
        },
    ]
    for i, log in enumerate(logs):
        col.document(f"growth_{i+1}").set(log)
    print(f"  [OK] Seeded {len(logs)} growth logs")


def seed_medication_logs(db, baby_id: str):
    """Seed 2 bản ghi uống thuốc."""
    col = db.collection("babies").document(baby_id).collection("medication_logs")

    for doc in col.stream():
        doc.reference.delete()

    logs = [
        {
            "medication_name": "Hapacol 150mg (Paracetamol)",
            "dosage": "150mg",
            "prescribed_by": "Bác sĩ kê đơn",
            "notes": "Cho bé uống khi sốt cao trên 38.5 độ C, liều cách nhau 4-6 tiếng.",
            "logged_at": (NOW - timedelta(hours=5)).isoformat()
        },
        {
            "medication_name": "Vitamin D3 K2",
            "dosage": "2 giọt",
            "prescribed_by": "Bổ sung hàng ngày",
            "notes": "Uống vào buổi sáng để hấp thụ tốt nhất.",
            "logged_at": NOW.replace(hour=8, minute=0, second=0).isoformat()
        },
    ]
    for i, log in enumerate(logs):
        col.document(f"med_{i+1}").set(log)
    print(f"  [OK] Seeded {len(logs)} medication logs")


def seed_nutrition_feeds(db, baby_id: str):
    """Seed feeds vào collection nutrition_feeds."""

    existing = list(db.collection("nutrition_feeds").where("baby_id", "==", baby_id).stream())
    for doc in existing:
        doc.reference.delete()

    feeds = [
        {
            "baby_id": baby_id, "type": "Formula", "amount": 180.0,
            "details": "180ml Sữa công thức", "time": "10:30 SA",
            "date": TODAY, "created_at": (NOW - timedelta(hours=3)).isoformat()
        },
        {
            "baby_id": baby_id, "type": "Breast", "amount": 120.0,
            "details": "120ml Sữa mẹ", "time": "07:00 SA",
            "date": TODAY, "created_at": (NOW - timedelta(hours=6)).isoformat()
        },
        {
            "baby_id": baby_id, "type": "Solids", "amount": 0.0,
            "details": "Súp khoai lang nghiền (2 thìa cafe)", "time": "12:00 TR",
            "date": TODAY, "created_at": (NOW - timedelta(hours=1)).isoformat()
        },
        {
            "baby_id": baby_id, "type": "Formula", "amount": 0.0,
            "details": "Sleep Nap Duration: 1h 30m", "time": "09:00 SA",
            "date": TODAY, "created_at": (NOW - timedelta(hours=4)).isoformat()
        },
    ]
    for i, feed in enumerate(feeds):
        db.collection("nutrition_feeds").document(f"feed_{i+1}").set(feed)
    print(f"  [OK] Seeded {len(feeds)} nutrition feeds")


def seed_ingredients(db, baby_id: str):
    """Seed ingredients vào nutrition_ingredients."""

    existing = list(db.collection("nutrition_ingredients").where("baby_id", "==", baby_id).stream())
    for doc in existing:
        doc.reference.delete()

    ingredients = [
        {
            "baby_id": baby_id, "name": "Khoai lang ngọt",
            "reaction": "Loved it", "date": TODAY,
            "created_at": NOW.isoformat()
        },
        {
            "baby_id": baby_id, "name": "Bí đỏ",
            "reaction": "Neutral", "date": (date.today() - timedelta(days=3)).isoformat(),
            "created_at": (NOW - timedelta(days=3)).isoformat()
        },
        {
            "baby_id": baby_id, "name": "Bơ chín",
            "reaction": "Spat out", "date": (date.today() - timedelta(days=7)).isoformat(),
            "created_at": (NOW - timedelta(days=7)).isoformat()
        },
    ]
    for i, ing in enumerate(ingredients):
        db.collection("nutrition_ingredients").document(f"ing_{i+1}").set(ing)
    print(f"  [OK] Seeded {len(ingredients)} ingredients")


def seed_healthcare_tips(db):
    """Seed AI tips phân loại theo độ tuổi."""

    for doc in db.collection("healthcare_tips").stream():
        doc.reference.delete()

    tips = [
        {
            "min_age_months": 0, "max_age_months": 5,
            "category": "Dinh dưỡng",
            "content": "Trong 6 tháng đầu, sữa mẹ hoặc sữa công thức là nguồn dinh dưỡng duy nhất bé cần. Bú theo nhu cầu, trung bình 8-12 lần mỗi ngày đối với trẻ sơ sinh.",
        },
        {
            "min_age_months": 6, "max_age_months": 12,
            "category": "Ăn dặm",
            "content": "Bắt đầu cho bé ăn dặm từ 6 tháng tuổi với các món đơn giản như khoai lang hoặc bí đỏ nghiền. Hãy cho bé ăn 1-2 thìa nhỏ sau khi bú sữa và theo dõi phản ứng dị ứng.",
        },
        {
            "min_age_months": 13, "max_age_months": 24,
            "category": "Phát triển",
            "content": "Giai đoạn 1-2 tuổi bé cần 3 bữa chính và 2 bữa phụ mỗi ngày. Đa dạng hóa các loại thực phẩm để bé nhận đủ chất dinh dưỡng và tránh dùng gia vị nhiều muối đường.",
        },
    ]
    for i, tip in enumerate(tips):
        db.collection("healthcare_tips").document(f"tip_{i+1}").set(tip)
    print(f"  [OK] Seeded {len(tips)} healthcare tips")


def main():
    print("=== BabyCare Seed Script (Vietnamese) ===")
    print("=" * 40)

    db = get_firestore_db()
    baby_id = get_baby_id(db)

    print("\nSeeding Firestore collections...")
    seed_growth_logs(db, baby_id)
    seed_medication_logs(db, baby_id)
    seed_nutrition_feeds(db, baby_id)
    seed_ingredients(db, baby_id)
    seed_healthcare_tips(db)

    print("\nSeed hoan tat!")
    print(f"   Baby ID: {baby_id}")
    print("   Kiem tra tai: http://localhost:8000/api/docs")


if __name__ == "__main__":
    main()
