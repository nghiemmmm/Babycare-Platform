"""
Master Seed Script for Bé Lu - Health & Medication Module
Baby: Lu (bEofmoFl3Sc1rhbwzvqi)
Parents: Hoài (pemvc0gMaEdGcAN1YTNdLtuMinF3), Vinh (yWsbRdWEgeMOrEUexShSMhXio1F3)
"""
import os
import sys
from datetime import datetime, timezone

# Ensure project root in sys.path
sys.path.insert(0, r"d:\ViT\BABYCARE\babycare-ai")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.infrastructure.database.connection import get_firestore_db
from app.modules.health_records.schemas import HealthEpisodeCreate, HealthEventCreate
from app.modules.health_records.service import HealthRecordService
from app.modules.medication.schemas import MedicationPlanCreate
from app.modules.medication.service import MedicationService

BABY_ID = "bEofmoFl3Sc1rhbwzvqi"
MOM_ID = "pemvc0gMaEdGcAN1YTNdLtuMinF3"
MOM_NAME = "Mẹ Hoài"
DAD_ID = "yWsbRdWEgeMOrEUexShSMhXio1F3"
DAD_NAME = "Ba Vinh"

def run_seed():
    db = get_firestore_db()
    health_service = HealthRecordService()
    med_service = MedicationService()

    print("==========================================================")
    print("🚀 BẮT ĐẦU NẠP DỮ LIỆU SỨC KHỎE & TỦ THUỐC CHO BÉ LU")
    print("==========================================================")

    # -------------------------------------------------------------------------
    # 1. CẬP NHẬT THÔNG TIN CƠ BẢN VÀ DỊ ỨNG CỦA BÉ LU
    # -------------------------------------------------------------------------
    print("\n1. Cập nhật hồ sơ dị ứng & ngày sinh bé Lu...")
    baby_ref = db.collection("babies").document(BABY_ID)
    baby_ref.update({
        "birthdate": "2025-10-25",
        "allergies": ["Đậu phộng nhẹ"],
        "medication_allergies": ["Amoxicillin", "Kháng sinh nhóm Penicillin"]
    })
    print("✅ Đã cập nhật dị ứng thuốc: Amoxicillin, Kháng sinh nhóm Penicillin")

    # -------------------------------------------------------------------------
    # 2. LÀM SẠCH CÁC HEALTH EPISODES CŨ ĐỂ KHÔNG BỊ TRÙNG LẶP
    # -------------------------------------------------------------------------
    print("\n2. Dọn dẹp các đợt theo dõi cũ của bé Lu...")
    episodes_col = baby_ref.collection("health_episodes")
    existing_eps = episodes_col.stream()
    for ep in existing_eps:
        # Delete subcollection events first
        evs = episodes_col.document(ep.id).collection("events").stream()
        for ev in evs:
            episodes_col.document(ep.id).collection("events").document(ev.id).delete()
        episodes_col.document(ep.id).delete()
    print("✅ Đã làm sạch subcollection health_episodes")

    # -------------------------------------------------------------------------
    # 3. TẠO ACTIVE HEALTH EPISODE (ĐỢT ĐANG THEO DÕI: HÔ HẤP)
    # -------------------------------------------------------------------------
    print("\n3. Tạo Đợt theo dõi đang hoạt động (Hô hấp & Cảm cúm)...")
    active_ep_in = HealthEpisodeCreate(
        category="respiratory",
        title="Đợt Viêm đường hô hấp trên & Sổ mũi (Ngày thứ 2)",
        initial_symptoms=["Ho khan từng cơn", "Nghẹt mũi khò khè khi ngủ", "Chảy nước mũi trong"],
        initial_temp=37.8,
        initial_severity="moderate",
        initial_descriptor="Bé húng hắng ho nhiều về đêm và sáng sớm, có nước mũi trong, bú hơi ngắt quãng",
        treatment="Vệ sinh mũi bằng nước muối sinh lý 0.9% trước khi ăn và trước khi ngủ (3 lần/ngày). Uống siro ho thảo dược Prospan 2.5ml sau ăn sáng và tối. Cho bé bú cữ nhỏ chia đều, kê cao gối khi ngủ và giữ nhiệt độ phòng 25-26°C, độ ẩm 55-60%.",
        doctor_name="BS. Nguyễn Văn An - Nhi khoa",
        notes="Theo dõi sát tiếng ho và nhịp thở của bé. Nếu sốt trên 38.5°C hoặc thở rút lõm lồng ngực cần đưa bé đi khám lại ngay."
    )
    active_ep = health_service.create_episode(BABY_ID, active_ep_in, MOM_ID, MOM_NAME)
    active_ep_id = active_ep.id
    print(f"✅ Đã tạo Active Episode ID: {active_ep_id}")

    # Nạp các mốc diễn biến (Events) trải dài từ hôm qua đến hôm nay
    events_data = [
        {
            "event_type": "symptom_check",
            "symptom_name": "Hô hấp",
            "severity": "moderate",
            "descriptor": "Bé nghẹt mũi, thở khò khè và húng hắng ho khan khi nằm ngủ. Thân nhiệt 37.8°C",
            "notes": "Mẹ nhỏ nước muối và vỗ lưng ru bé ngủ",
            "recorded_by_id": MOM_ID,
            "recorded_by_name": MOM_NAME,
            "recorded_at": "2026-09-06T21:30:00+07:00"
        },
        {
            "event_type": "care_action",
            "action_or_med_name": "Vệ sinh đường thở & Rửa mũi nước muối sinh lý",
            "descriptor": "Mẹ nhỏ nước muối 0.9%, hút nhẹ dịch mũi trong, vệ sinh thông thoáng trước cữ bú sáng",
            "notes": "Dịch mũi trong loãng, đường thở thông thoáng hơn",
            "recorded_by_id": MOM_ID,
            "recorded_by_name": MOM_NAME,
            "recorded_at": "2026-09-07T07:45:00+07:00"
        },
        {
            "event_type": "medication",
            "action_or_med_name": "Vitamin D3 K2 LineaBon (3 giọt)",
            "descriptor": "Bổ sung vi chất buổi sáng cùng cữ bú đầu tiên",
            "notes": "Bé hợp tác uống ngoan",
            "recorded_by_id": MOM_ID,
            "recorded_by_name": MOM_NAME,
            "recorded_at": "2026-09-07T08:30:00+07:00"
        },
        {
            "event_type": "medication",
            "action_or_med_name": "Siro ho thảo dược Prospan (2.5 mL)",
            "descriptor": "Uống sau bữa ăn sáng 30 phút giúp dịu rát họng và loãng đờm",
            "notes": "Bé uống hết liều, không có hiện tượng nôn trớ",
            "recorded_by_id": MOM_ID,
            "recorded_by_name": MOM_NAME,
            "recorded_at": "2026-09-07T09:15:00+07:00"
        },
        {
            "event_type": "measurement",
            "metric_value": 37.1,
            "descriptor": "Thân nhiệt mát dịu 37.1°C, bé chơi ngoan và vui vẻ",
            "notes": "Nhiệt độ đã về mức an toàn hoàn toàn bình thường",
            "recorded_by_id": DAD_ID,
            "recorded_by_name": DAD_NAME,
            "recorded_at": "2026-09-07T11:30:00+07:00"
        },
        {
            "event_type": "care_action",
            "action_or_med_name": "Vệ sinh mũi trước cữ ngủ trưa",
            "descriptor": "Nhỏ 1 ống nước muối sinh lý Gifrer làm sạch bụi bẩn và dịch nhầy",
            "notes": "Mũi bé khô thoáng",
            "recorded_by_id": DAD_ID,
            "recorded_by_name": DAD_NAME,
            "recorded_at": "2026-09-07T13:10:00+07:00"
        },
        {
            "event_type": "symptom_check",
            "symptom_name": "Hô hấp",
            "severity": "mild",
            "descriptor": "Bé ngủ trưa yên giấc 1.5 tiếng, tiếng thở êm, không bị cơn ho đánh thức",
            "notes": "Tiến triển rất tích cực, bé đỡ ho rõ rệt",
            "recorded_by_id": MOM_ID,
            "recorded_by_name": MOM_NAME,
            "recorded_at": "2026-09-07T14:45:00+07:00"
        }
    ]

    for ev in events_data:
        episodes_col.document(active_ep_id).collection("events").add(ev)

    # Cập nhật lại status & trend cho active episode
    episodes_col.document(active_ep_id).update({
        "progress_status": "improving",
        "progress_summary": "Thân nhiệt đã hạ về 37.1°C mát dịu, bé ngủ sâu giấc và tiếng thở êm dịu hơn rất nhiều.",
        "events_count": len(events_data)
    })
    print(f"✅ Đã nạp {len(events_data)} mốc timeline diễn biến cho Active Episode")

    # -------------------------------------------------------------------------
    # 4. TẠO 2 RESOLVED EPISODES (LỊCH SỬ CÁC ĐỢT ĐÃ KHỎI)
    # -------------------------------------------------------------------------
    print("\n4. Tạo Lịch sử các đợt theo dõi đã khỏi (Resolved History)...")
    
    # Resolved 1: Sốt sau tiêm vaccine
    res1_ref = episodes_col.document()
    res1_ref.set({
        "baby_id": BABY_ID,
        "category": "fever",
        "title": "Sốt nhẹ sau tiêm vắc-xin 6 trong 1 (Mũi tháng thứ 4)",
        "status": "resolved",
        "progress_status": "improving",
        "started_at": "2026-08-15T09:00:00+07:00",
        "resolved_at": "2026-08-17T10:00:00+07:00",
        "initial_symptoms": ["Sốt cao (>38.5°C)", "Quấy khóc mệt mỏi"],
        "initial_temp": 38.5,
        "initial_severity": "moderate",
        "initial_descriptor": "Bé sốt ấm sau tiêm chủng buổi sáng, vết tiêm hơi ửng hồng",
        "treatment": "Chườm ấm trán nách bẹn, cho bé bú tăng cường cữ sữa mẹ để bù nước, theo dõi sát thân nhiệt mỗi 2 giờ. Uống Hapacol 150mg khi sốt trên 38.5°C.",
        "doctor_name": "BS. Lê Thị Mai - Tiêm chủng",
        "resolution_notes": "Bé hạ sốt hoàn toàn sau 24 giờ, vết tiêm mềm không sưng đỏ, ăn ngủ ngoan trở lại bình thường.",
        "progress_summary": "Bé đã hết sốt, vui vẻ và khỏe mạnh hoàn toàn.",
        "events_count": 4,
        "created_at": "2026-08-15T09:00:00+07:00",
        "updated_at": "2026-08-17T10:00:00+07:00"
    })
    res1_evs = [
        {"event_type": "measurement", "metric_value": 38.5, "descriptor": "Bé sốt 38.5°C sau tiêm 4 tiếng", "notes": "Bé quấy khóc, mẹ chườm ấm nách bẹn", "recorded_by_name": MOM_NAME, "recorded_at": "2026-08-15T13:30:00+07:00"},
        {"event_type": "medication", "action_or_med_name": "Hapacol 150mg Trẻ Em", "descriptor": "Uống 1 gói hạ sốt hòa tan 10ml nước ấm", "notes": "Bé uống ngoan", "recorded_by_name": MOM_NAME, "recorded_at": "2026-08-15T14:00:00+07:00"},
        {"event_type": "measurement", "metric_value": 37.4, "descriptor": "Thân nhiệt hạ về 37.4°C sau 1.5 giờ", "notes": "Bé dễ chịu và thiếp ngủ", "recorded_by_name": DAD_NAME, "recorded_at": "2026-08-15T15:30:00+07:00"},
        {"event_type": "measurement", "metric_value": 36.8, "descriptor": "Thân nhiệt hoàn toàn bình thường 36.8°C", "notes": "Vết tiêm mềm không tấy đỏ, bé khỏe mạnh", "recorded_by_name": MOM_NAME, "recorded_at": "2026-08-16T08:00:00+07:00"}
    ]
    for ev in res1_evs:
        res1_ref.collection("events").add(ev)

    # Resolved 2: Rối loạn tiêu hóa khi tập dặm
    res2_ref = episodes_col.document()
    res2_ref.set({
        "baby_id": BABY_ID,
        "category": "digestive",
        "title": "Rối loạn tiêu hóa nhẹ khi tập dặm cữ đầu",
        "status": "resolved",
        "progress_status": "improving",
        "started_at": "2026-07-20T08:00:00+07:00",
        "resolved_at": "2026-07-23T16:00:00+07:00",
        "initial_symptoms": ["Tiêu chảy", "Bụng sôi quấy khóc"],
        "initial_temp": 36.9,
        "initial_severity": "mild",
        "initial_descriptor": "Bé đi ngoài phân lỏng hoa cà hoa cải 3-4 lần trong ngày, bụng sôi nhẹ",
        "treatment": "Bổ sung men vi sinh BioGaia 5 giọt/ngày, tạm ngừng thức ăn dặm thô chuyển về cháo loãng rây mịn, xoa bụng nhẹ nhàng theo chiều kim đồng hồ.",
        "doctor_name": "BS. Trần Hoàng Nam - Tiêu hóa nhi",
        "resolution_notes": "Phân bé sệt đẹp sau 3 ngày bổ sung men vi sinh BioGaia, bụng mềm không chướng, ăn ngon miệng.",
        "progress_summary": "Hệ vi sinh đường ruột đã ổn định hoàn toàn.",
        "events_count": 3,
        "created_at": "2026-07-20T08:00:00+07:00",
        "updated_at": "2026-07-23T16:00:00+07:00"
    })
    res2_evs = [
        {"event_type": "symptom_check", "symptom_name": "Tiêu hóa", "severity": "mild", "descriptor": "Bé đi phân lỏng 3 lần/ngày, bụng sôi nhẹ", "recorded_by_name": MOM_NAME, "recorded_at": "2026-07-20T10:00:00+07:00"},
        {"event_type": "medication", "action_or_med_name": "Men Vi Sinh BioGaia (5 giọt)", "descriptor": "Bổ sung lợi khuẩn L. reuteri Protectis vào cữ sáng", "recorded_by_name": MOM_NAME, "recorded_at": "2026-07-20T10:30:00+07:00"},
        {"event_type": "symptom_check", "symptom_name": "Tiêu hóa", "severity": "none", "descriptor": "Phân bé sệt vàng đẹp, bụng mềm, bú ngủ bình thường", "recorded_by_name": MOM_NAME, "recorded_at": "2026-07-23T15:00:00+07:00"}
    ]
    for ev in res2_evs:
        res2_ref.collection("events").add(ev)

    print("✅ Đã nạp 2 đợt lịch sử đã khỏi hoàn toàn (Sốt tiêm chủng & Tiêu hóa)")

    # -------------------------------------------------------------------------
    # 5. CẬP NHẬT TỦ THUỐC (MEDICATION PLANS)
    # -------------------------------------------------------------------------
    print("\n5. Chuẩn hóa Tủ thuốc & Đơn thuốc (Medication Plans)...")
    plans_col = baby_ref.collection("medication_plans")

    # Dọn dẹp plans cũ
    old_plans = plans_col.stream()
    for p in old_plans:
        plans_col.document(p.id).delete()

    plans_data = [
        {
            "id": "plan_prospan_lu",
            "name": "Siro Ho Thảo Dược Prospan",
            "alternative_name": "Cao lá thường xuân khô",
            "strength": "35mg / 5mL",
            "dose": "2.5",
            "unit": "mL",
            "route": "Oral (Đường uống)",
            "frequency": "2 lần/ngày (Sáng 08:00, Tối 20:00)",
            "schedule_times": ["08:00", "20:00"],
            "meal_timing": "after_food",
            "start_date": "2026-09-06",
            "duration_days": 5,
            "purpose": "Giảm ho, long đờm, làm ấm và dịu rát họng",
            "instructions": "Lắc kỹ chai trước khi rót vào cốc chia liều, cho bé uống sau ăn 30 phút",
            "prescribed_by": "BS. Nguyễn Văn An - Nhi khoa",
            "status": "active"
        },
        {
            "id": "plan_d3k2_lu",
            "name": "Vitamin D3 K2 LineaBon Drops",
            "alternative_name": "D3 + K2 Olive Oil",
            "strength": "400 IU D3 + 22.5mcg K2",
            "dose": "3",
            "unit": "giọt",
            "route": "Oral (Đường uống)",
            "frequency": "1 lần/ngày (Sáng 08:00)",
            "schedule_times": ["08:00"],
            "meal_timing": "after_food",
            "start_date": "2026-09-01",
            "duration_days": 30,
            "purpose": "Bổ sung vi chất phát triển hệ xương răng và chiều cao",
            "instructions": "Nhỏ trực tiếp vào miệng bé hoặc thìa nhỏ vào buổi sáng cùng cữ sữa",
            "prescribed_by": "BS. Nguyễn Văn An - Nhi khoa",
            "status": "active"
        },
        {
            "id": "plan_gifrer_lu",
            "name": "Nước Muối Sinh Lý Tép Hồng Gifrer",
            "alternative_name": "Physiodose 5ml",
            "strength": "0.9% NaCl vô trùng",
            "dose": "1",
            "unit": "ống",
            "route": "Nhỏ mũi",
            "frequency": "3 lần/ngày (Sáng, Trưa, Tối)",
            "schedule_times": ["07:30", "13:00", "20:30"],
            "meal_timing": "before_food",
            "start_date": "2026-09-06",
            "duration_days": 7,
            "purpose": "Vệ sinh đường thở, làm sạch dịch nhầy mũi và kháng viêm nhẹ",
            "instructions": "Nghiêng đầu bé nhẹ nhàng, nhỏ 2-3 giọt mỗi bên mũi rồi lau sạch dịch chảy ra",
            "prescribed_by": "Phụ huynh chuẩn bị sẵn",
            "status": "active"
        },
        {
            "id": "plan_hapacol_lu",
            "name": "Hapacol 150mg Trẻ Em",
            "alternative_name": "Paracetamol 150mg",
            "strength": "150mg / gói",
            "dose": "1",
            "unit": "gói",
            "route": "Oral (Đường uống)",
            "frequency": "Khi sốt > 38.5°C (Cách 4-6h)",
            "schedule_times": ["12:00"],
            "meal_timing": "when_fever",
            "start_date": "2026-09-01",
            "duration_days": 30,
            "purpose": "Hạ sốt, giảm đau sau tiêm hoặc khi sốt cấp",
            "instructions": "Hòa tan 1 gói với 10ml nước ấm nguội, chỉ uống khi sốt từ 38.5°C trở lên. Cách tối thiểu 4 tiếng giữa 2 lần.",
            "prescribed_by": "BS. Nguyễn Văn An - Nhi khoa",
            "status": "active"
        },
        {
            "id": "plan_amox_allergy_lu",
            "name": "Amoxicillin",
            "alternative_name": "Augmentin",
            "strength": "250 mg / 5 mL",
            "dose": "5",
            "unit": "mL",
            "route": "Oral (Đường uống)",
            "frequency": "Đã ngưng (Bé dị ứng)",
            "schedule_times": ["08:00"],
            "meal_timing": "after_food",
            "start_date": "2026-08-01",
            "duration_days": 0,
            "purpose": "Kháng sinh (Đã dừng do phát hiện phản ứng dị ứng)",
            "instructions": "KHÔNG SỬ DỤNG - Bé có tiền sử mẩn ngứa khi dùng nhóm Penicillin",
            "prescribed_by": "Cảnh báo dị ứng",
            "status": "paused"
        }
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    for p in plans_data:
        p_id = p.pop("id")
        p["baby_id"] = BABY_ID
        p["created_at"] = now_iso
        p["updated_at"] = now_iso
        plans_col.document(p_id).set(p)

    print("✅ Đã thiết lập 5 đơn thuốc trong tủ thuốc (4 active + 1 paused dị ứng)")

    # -------------------------------------------------------------------------
    # 6. GHI NHẬN CÁC LIỀU ĐÃ UỐNG HÔM NAY (MEDICATION DOSE LOGS)
    # -------------------------------------------------------------------------
    print("\n6. Ghi nhận cữ thuốc hôm nay (2026-09-07)...")
    logs_col = baby_ref.collection("medication_dose_logs")

    # Xóa logs cũ
    old_logs = logs_col.stream()
    for l in old_logs:
        logs_col.document(l.id).delete()

    today_logs = [
        {
            "baby_id": BABY_ID,
            "plan_id": "plan_gifrer_lu",
            "medication_name": "Nước Muối Sinh Lý Tép Hồng Gifrer",
            "scheduled_date": "2026-09-07",
            "scheduled_time": "07:30",
            "status": "taken",
            "taken_at": "2026-09-07T07:45:00+07:00",
            "dose_taken": "1 ống",
            "administered_by": MOM_NAME,
            "notes": "Nhỏ mũi trước cữ bú sáng",
            "created_at": now_iso
        },
        {
            "baby_id": BABY_ID,
            "plan_id": "plan_d3k2_lu",
            "medication_name": "Vitamin D3 K2 LineaBon Drops",
            "scheduled_date": "2026-09-07",
            "scheduled_time": "08:00",
            "status": "taken",
            "taken_at": "2026-09-07T08:30:00+07:00",
            "dose_taken": "3 giọt",
            "administered_by": MOM_NAME,
            "notes": "3 giọt D3K2 cùng cữ sữa",
            "created_at": now_iso
        },
        {
            "baby_id": BABY_ID,
            "plan_id": "plan_prospan_lu",
            "medication_name": "Siro Ho Thảo Dược Prospan",
            "scheduled_date": "2026-09-07",
            "scheduled_time": "08:00",
            "status": "taken",
            "taken_at": "2026-09-07T09:15:00+07:00",
            "dose_taken": "2.5 mL",
            "administered_by": MOM_NAME,
            "notes": "2.5ml Prospan sau ăn 30 phút",
            "created_at": now_iso
        },
        {
            "baby_id": BABY_ID,
            "plan_id": "plan_gifrer_lu",
            "medication_name": "Nước Muối Sinh Lý Tép Hồng Gifrer",
            "scheduled_date": "2026-09-07",
            "scheduled_time": "13:00",
            "status": "taken",
            "taken_at": "2026-09-07T13:10:00+07:00",
            "dose_taken": "1 ống",
            "administered_by": DAD_NAME,
            "notes": "Vệ sinh mũi trước cữ ngủ trưa",
            "created_at": now_iso
        },
        # Lịch sử ngày hôm qua 2026-09-06
        {
            "baby_id": BABY_ID,
            "plan_id": "plan_d3k2_lu",
            "medication_name": "Vitamin D3 K2 LineaBon Drops",
            "scheduled_date": "2026-09-06",
            "scheduled_time": "08:00",
            "status": "taken",
            "taken_at": "2026-09-06T08:20:00+07:00",
            "dose_taken": "3 giọt",
            "administered_by": MOM_NAME,
            "notes": "Cữ sáng",
            "created_at": now_iso
        },
        {
            "baby_id": BABY_ID,
            "plan_id": "plan_gifrer_lu",
            "medication_name": "Nước Muối Sinh Lý Tép Hồng Gifrer",
            "scheduled_date": "2026-09-06",
            "scheduled_time": "20:30",
            "status": "taken",
            "taken_at": "2026-09-06T20:35:00+07:00",
            "dose_taken": "1 ống",
            "administered_by": MOM_NAME,
            "notes": "Nhỏ mũi trước khi đi ngủ",
            "created_at": now_iso
        }
    ]

    for log in today_logs:
        logs_col.add(log)

    print("✅ Đã nạp đầy đủ lịch uống hôm nay và lịch sử hôm qua")
    print("\n🎉 HOÀN TẤT NẠP TOÀN BỘ DỮ LIỆU SỨC KHỎE CHO BÉ LU THÀNH CÔNG!")
    print("==========================================================")

if __name__ == "__main__":
    run_seed()
