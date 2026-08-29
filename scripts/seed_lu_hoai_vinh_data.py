"""
Script tạo dữ liệu mẫu thực tế cho Bé Lu, chỉ liên quan đến 2 người: Mẹ Hoài & Bảo Mẫu Vinh.
"""
import os
import sys
from datetime import datetime, date, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath("."))
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
load_dotenv()

from app.infrastructure.database.connection import get_firestore_db

def seed_data():
    db = get_firestore_db()

    BABY_ID = "bEofmoFl3Sc1rhbwzvqi" # Bé Lu
    HOAI_UID = "pemvc0gMaEdGcAN1YTNdLtuMinF3" # Mẹ Hoài
    VINH_UID = "yWsbRdWEgeMOrEUexShSMhXio1F3" # Bảo Mẫu Vinh
    TODAY_STR = date.today().isoformat()
    NOW_UTC = datetime.now(timezone.utc).isoformat()

    print(f"[*] Bắt đầu tạo dữ liệu mẫu cho Bé Lu ({BABY_ID}) gắn với Hoài và Vinh...")

    # 1. Cập nhật hồ sơ Bé Lu để đảm bảo cả 2 người cùng là Guardians
    baby_ref = db.collection("babies").document(BABY_ID)
    baby_ref.set({
        "name": "Lu",
        "gender": "Boy",
        "birth_date": "2025-10-25",
        "guardians": [HOAI_UID, VINH_UID],
        "allergies": [],
        "blood_type": "O+",
        "pediatrician_name": "BS. Nguyễn Văn An (Bệnh viện Nhi Đồng)",
        "is_active": True,
        "avatar_url": "https://res.cloudinary.com/dtdkqzqvo/image/upload/v1787679195/babycare/avatars/p66vhu1wecot7vfasdhq.jpg",
        "updated_at": NOW_UTC
    }, merge=True)
    print(" [+] Đã cập nhật thông tin hồ sơ Bé Lu.")

    # 2. Cập nhật bảng Guardians
    db.collection("guardians").document(f"g_hoai_{BABY_ID}").set({
        "baby_id": BABY_ID,
        "user_id": HOAI_UID,
        "name": "Mẹ Hoài",
        "email": "nguyenducnghiemthptllqt@gmail.com",
        "role": "ADMIN",
        "status": "Synced",
        "created_at": NOW_UTC
    }, merge=True)

    db.collection("guardians").document(f"g_vinh_{BABY_ID}").set({
        "baby_id": BABY_ID,
        "user_id": VINH_UID,
        "name": "Bảo Mẫu Vinh",
        "email": "nguyenductop1112005@gmail.com",
        "role": "GUARDIAN",
        "status": "Synced",
        "created_at": NOW_UTC
    }, merge=True)
    print(" [+] Đã tạo/đồng bộ danh sách Guardians (Mẹ Hoài: ADMIN, Bảo Mẫu Vinh: GUARDIAN).")

    # 3. Lời dặn bàn giao buổi sáng (Handover Note)
    handover_id = f"ho_{BABY_ID}_{TODAY_STR}"
    db.collection("handover_notes").document(handover_id).set({
        "baby_id": BABY_ID,
        "date": TODAY_STR,
        "created_by": HOAI_UID,
        "author_name": "Mẹ Hoài",
        "content": "Hôm nay bé Lu dậy lúc 6h30 sáng rất vui vẻ. Nhờ chú Vinh cho bé uống 5 giọt Vitamin D3 K2 lúc 9h sáng, cữ sữa trưa 150ml lúc 11h30 và cho bé ngủ trưa tầm 12h30 nhé. Chiều mẹ Hoài sẽ về đón tay lúc 16h30!",
        "voice_note_url": None,
        "photo_urls": [],
        "acknowledged_by": [VINH_UID],
        "created_at": NOW_UTC,
        "updated_at": NOW_UTC
    })
    print(" [+] Đã tạo Lời dặn bàn giao trong ngày (Mẹ Hoài tạo -> Bảo Mẫu Vinh xác nhận).")

    # 4. Nhiệm vụ điều phối trong ngày (Care Tasks)
    tasks = [
        {
            "id": f"task_lu_1_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_type": "medication",
            "title": "Cho bé Lu uống Vitamin D3 K2 (5 giọt)",
            "scheduled_time": f"{TODAY_STR}T09:00:00Z",
            "assigned_to": VINH_UID,
            "assigned_name": "Bảo Mẫu Vinh",
            "created_by": HOAI_UID,
            "instructions": "Uống 5 giọt trực tiếp hoặc nhỏ vào thìa nhỏ sau cữ bú sáng",
            "target_value": {"dosage": "5 giọt", "medicine": "Vitamin D3 K2"},
            "actual_value": {"dosage": "5 giọt", "medicine": "Vitamin D3 K2"},
            "status": "completed",
            "priority": "high",
            "is_recurring": True,
            "completed_at": f"{TODAY_STR}T09:05:00Z",
            "completed_by": VINH_UID,
            "completion_notes": "Đã cho bé uống 5 giọt sau cữ bú sáng, bé hợp tác rất ngoan.",
            "created_at": NOW_UTC
        },
        {
            "id": f"task_lu_2_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_type": "feeding",
            "title": "Cữ sữa trưa (150ml sữa công thức)",
            "scheduled_time": f"{TODAY_STR}T11:30:00Z",
            "assigned_to": VINH_UID,
            "assigned_name": "Bảo Mẫu Vinh",
            "created_by": HOAI_UID,
            "instructions": "Pha nước ấm 45 độ C, cho bé bú từ từ và vỗ ợ hơi kỹ",
            "target_value": {"amount": 150, "unit": "ml", "feed_type": "Formula"},
            "actual_value": {"amount": 150, "unit": "ml", "feed_type": "Formula"},
            "status": "completed",
            "priority": "medium",
            "is_recurring": True,
            "completed_at": f"{TODAY_STR}T11:35:00Z",
            "completed_by": VINH_UID,
            "completion_notes": "Bé Lu bú hết 150ml ngon lành, đã vỗ ợ hơi tốt.",
            "created_at": NOW_UTC
        },
        {
            "id": f"task_lu_3_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_type": "sleep",
            "title": "Ru bé ngủ trưa (Giấc Nap 2)",
            "scheduled_time": f"{TODAY_STR}T12:30:00Z",
            "assigned_to": VINH_UID,
            "assigned_name": "Bảo Mẫu Vinh",
            "created_by": HOAI_UID,
            "instructions": "Bật nhạc trắng dịu nhẹ, nhiệt độ phòng 24-25 độ",
            "target_value": {"duration_minutes": 90},
            "actual_value": {"duration_minutes": 105},
            "status": "completed",
            "priority": "medium",
            "is_recurring": True,
            "completed_at": f"{TODAY_STR}T12:30:00Z",
            "completed_by": VINH_UID,
            "completion_notes": "Bé ngủ sâu giấc từ 12:30 đến 14:15.",
            "created_at": NOW_UTC
        },
        {
            "id": f"task_lu_4_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_type": "custom",
            "title": "Vệ sinh & Thay tã thoáng mát",
            "scheduled_time": f"{TODAY_STR}T14:30:00Z",
            "assigned_to": VINH_UID,
            "assigned_name": "Bảo Mẫu Vinh",
            "created_by": HOAI_UID,
            "instructions": "Thay tã sau khi bé thức dậy và thoa kem dưỡng ẩm",
            "target_value": {},
            "actual_value": {},
            "status": "completed",
            "priority": "low",
            "is_recurring": False,
            "completed_at": f"{TODAY_STR}T14:35:00Z",
            "completed_by": VINH_UID,
            "completion_notes": "Tã ướt nhẹ bình thường, da bé khô thoáng sạch sẽ.",
            "created_at": NOW_UTC
        },
        {
            "id": f"task_lu_5_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_type": "feeding",
            "title": "Cữ sữa chiều & Vận động lẫy (Tummy Time)",
            "scheduled_time": f"{TODAY_STR}T16:30:00Z",
            "assigned_to": HOAI_UID,
            "assigned_name": "Mẹ Hoài",
            "created_by": HOAI_UID,
            "instructions": "Mẹ đi làm về đón tay, cho bé bú và tập nằm sấp 15 phút",
            "target_value": {"amount": 140, "unit": "ml"},
            "status": "pending",
            "priority": "medium",
            "is_recurring": True,
            "created_at": NOW_UTC
        }
    ]

    for t in tasks:
        t_id = t["id"]
        db.collection("care_tasks").document(t_id).set(t, merge=True)
    print(f" [+] Đã tạo {len(tasks)} việc cần làm (Tasks) phân công giữa Mẹ Hoài & Bảo Mẫu Vinh.")

    # 5. Dòng sự kiện chăm sóc thực tế (Care Events / Dòng hoạt động thời gian thực)
    events = [
        {
            "id": f"evt_lu_1_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_id": f"task_lu_1_{TODAY_STR}",
            "event_type": "medication",
            "occurred_at": f"{TODAY_STR}T09:05:00Z",
            "recorded_by": VINH_UID,
            "recorded_by_name": "Bảo Mẫu Vinh",
            "actual_value": {"dosage": "5 giọt", "medicine": "Vitamin D3 K2 LineaBon"},
            "notes": "Đã cho bé uống 5 giọt Vitamin D3 K2",
            "created_at": NOW_UTC
        },
        {
            "id": f"evt_lu_2_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_id": f"task_lu_2_{TODAY_STR}",
            "event_type": "feeding",
            "occurred_at": f"{TODAY_STR}T11:35:00Z",
            "recorded_by": VINH_UID,
            "recorded_by_name": "Bảo Mẫu Vinh",
            "actual_value": {"amount": 150, "unit": "ml", "feed_type": "Formula"},
            "notes": "Bé Lu bú 150ml sữa công thức",
            "created_at": NOW_UTC
        },
        {
            "id": f"evt_lu_3_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_id": f"task_lu_3_{TODAY_STR}",
            "event_type": "sleep",
            "occurred_at": f"{TODAY_STR}T12:30:00Z",
            "recorded_by": VINH_UID,
            "recorded_by_name": "Bảo Mẫu Vinh",
            "actual_value": {"duration_minutes": 105},
            "notes": "Bé ngủ trưa sâu giấc 1h45p",
            "created_at": NOW_UTC
        },
        {
            "id": f"evt_lu_4_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_id": f"task_lu_4_{TODAY_STR}",
            "event_type": "diaper",
            "occurred_at": f"{TODAY_STR}T14:35:00Z",
            "recorded_by": VINH_UID,
            "recorded_by_name": "Bảo Mẫu Vinh",
            "actual_value": {"status": "Wet"},
            "notes": "Thay tã ướt sạch sẽ",
            "created_at": NOW_UTC
        },
        {
            "id": f"evt_lu_5_{TODAY_STR}",
            "baby_id": BABY_ID,
            "task_id": None,
            "event_type": "feeding",
            "occurred_at": f"{TODAY_STR}T07:15:00Z",
            "recorded_by": HOAI_UID,
            "recorded_by_name": "Mẹ Hoài",
            "actual_value": {"amount": 120, "unit": "ml", "feed_type": "Breast"},
            "notes": "Cữ bú sáng sớm của mẹ trước khi đi làm",
            "created_at": NOW_UTC
        }
    ]

    for e in events:
        e_id = e["id"]
        db.collection("care_events").document(e_id).set(e, merge=True)
    print(f" [+] Đã tạo {len(events)} sự kiện chăm sóc trong ngày cho Dòng hoạt động thời gian thực.")

    # 6. Nhật ký cữ ăn (nutrition_feeds)
    feeds = [
        {
            "id": f"feed_lu_1_{TODAY_STR}",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "author_name": "Mẹ Hoài",
            "type": "Breast",
            "time": "07:15",
            "amount": 120,
            "unit": "ml",
            "date": TODAY_STR,
            "notes": "Cữ bú sáng mẹ trực tiếp cho bú, bé bú đều và ợ hơi tốt.",
            "created_at": NOW_UTC
        },
        {
            "id": f"feed_lu_2_{TODAY_STR}",
            "baby_id": BABY_ID,
            "user_id": VINH_UID,
            "author_name": "Bảo Mẫu Vinh",
            "type": "Formula",
            "time": "11:30",
            "amount": 150,
            "unit": "ml",
            "date": TODAY_STR,
            "notes": "Bé bú bình 150ml sữa công thức ấm, hợp tác rất tốt.",
            "created_at": NOW_UTC
        }
    ]
    for f in feeds:
        db.collection("nutrition_feeds").document(f["id"]).set(f, merge=True)
    print(f" [+] Đã tạo {len(feeds)} cữ bú trong mục Dinh dưỡng.")

    # 7. Chỉ số tăng trưởng của bé Lu (growth_measurements & babies/subcollection)
    measurements = [
        {
            "id": f"m0_lu",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "age_months": 0,
            "weight": 3.3,
            "height": 50.0,
            "head_circumference": 34.5,
            "date": "2025-10-25",
            "logged_at": "2025-10-25T08:00:00Z",
            "notes": "Bé Lu sinh thường khỏe mạnh, hồng hào.",
            "created_at": NOW_UTC
        },
        {
            "id": f"m1_lu",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "age_months": 1,
            "weight": 4.5,
            "height": 54.2,
            "head_circumference": 37.0,
            "date": "2025-11-25",
            "logged_at": "2025-11-25T09:00:00Z",
            "notes": "Tăng trưởng tháng đầu rất tốt.",
            "created_at": NOW_UTC
        },
        {
            "id": f"m2_lu",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "age_months": 2,
            "weight": 5.6,
            "height": 58.0,
            "head_circumference": 39.0,
            "date": "2025-12-25",
            "logged_at": "2025-12-25T09:00:00Z",
            "notes": "Phát triển chuẩn đường trung bình WHO.",
            "created_at": NOW_UTC
        },
        {
            "id": f"m3_lu",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "age_months": 3,
            "weight": 6.5,
            "height": 62.0,
            "head_circumference": 40.5,
            "date": "2026-01-25",
            "logged_at": "2026-01-25T09:00:00Z",
            "notes": "Bé cứng cáp, lẫy thành thạo và phản xạ nhanh nhẹn.",
            "created_at": NOW_UTC
        },
        {
            "id": f"m4_lu",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "age_months": 4,
            "weight": 7.1,
            "height": 64.5,
            "head_circumference": 41.5,
            "date": "2026-02-25",
            "logged_at": "2026-02-25T09:00:00Z",
            "notes": "Chỉ số tăng trưởng phát triển lý tưởng theo chuẩn WHO.",
            "created_at": NOW_UTC
        }
    ]
    for m in measurements:
        db.collection("growth_measurements").document(m["id"]).set(m, merge=True)
        db.collection("babies").document(BABY_ID).collection("growth_logs").document(m["id"]).set(m, merge=True)
    print(f" [+] Đã tạo {len(measurements)} mốc chỉ số tăng trưởng cho Bé Lu.")

    # 8. Lịch uống thuốc/vi chất (medication_logs)
    medications = [
        {
            "id": f"med_lu_d3",
            "baby_id": BABY_ID,
            "user_id": HOAI_UID,
            "name": "Vitamin D3 K2 LineaBon",
            "dosage": "5 giọt (400 IU)",
            "frequency": "1 lần/ngày vào buổi sáng",
            "time": "09:00",
            "prescribed_by": "BS. Nguyễn Văn An",
            "notes": "Bổ sung vi chất phát triển hệ xương và chiều cao tối ưu cho bé Lu.",
            "active": True,
            "created_at": NOW_UTC
        }
    ]
    for med in medications:
        db.collection("medication_logs").document(med["id"]).set(med, merge=True)
        db.collection("babies").document(BABY_ID).collection("medication_logs").document(med["id"]).set(med, merge=True)
    print(" [+] Đã tạo lịch bổ sung Vitamin D3 K2 cho Bé Lu.")

    print("\n🎉 HOÀN TẤT TẠO DỮ LIỆU MẪU ĐỒNG BỘ CHO MẸ HOÀI & BẢO MẪU VINH!")

if __name__ == "__main__":
    seed_data()
