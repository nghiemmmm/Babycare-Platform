"""
Feature Engineering Module for Wake Window Prediction
======================================================
Thực hiện trích xuất và biến đổi đặc trưng từ nhật ký Firestore sleep_logs:
- Group A: Current Baby Information (age, nap_number)
- Group B: Current-Day Temporal Features (day_start, previous_night_end)
- Group C: Recent Wake-Window History (previous_wake_window, prior_wake_windows)
- Group D: Recent Nap History (previous_nap, previous_sleep_duration, previous_wake_duration)
- Group E: Recent 5-Day History (Last 5 Days Representation)
- Group F: Project-Derived Extensions
"""

import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.modules.sleep.wake_window_schemas import (
    WakeWindowFeatureVector,
    SingleDaySleepRepresentation,
    Last5DaysHistoryRepresentation,
)


def _iso_to_minutes_from_midnight(iso_str: str) -> int:
    """Chuyển đổi chuỗi thời gian ISO-8601 sang số phút tính từ 00:00 của ngày đó."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.hour * 60 + dt.minute
    except Exception:
        return 420  # Mặc định 07:00 AM (420 phút)


def _calculate_age_in_months_and_days(birthday_str: Optional[str]) -> Tuple[float, int]:
    """Tính tuổi của bé theo tháng (float) và theo ngày (int)."""
    if not birthday_str:
        return 6.0, 180  # Mặc định 6 tháng
    try:
        bday = datetime.fromisoformat(birthday_str).date()
        today = datetime.now(timezone.utc).date()
        diff_days = max(1, (today - bday).days)
        age_months = round(diff_days / 30.4375, 2)
        return age_months, diff_days
    except Exception:
        return 6.0, 180


class FeatureEngineeringEngine:
    """
    Trích xuất vector đặc trưng hoàn chỉnh từ lịch sử Firestore sleep_logs của một em bé.
    [DIRECTLY SUPPORTED BY PATENT] & [PROJECT IMPLEMENTATION]
    """

    @classmethod
    def extract_features_from_logs(
        cls,
        baby_id: str,
        birthday_str: Optional[str],
        sleep_logs: List[Any],
        current_time: Optional[datetime] = None,
    ) -> WakeWindowFeatureVector:
        now_dt = current_time or datetime.now(timezone.utc)
        age_months, age_days = _calculate_age_in_months_and_days(birthday_str)

        # 1. Chuẩn hóa và sắp xếp logs theo thời gian tăng dần
        valid_logs = []
        for log in sleep_logs:
            if hasattr(log, "dict"):
                log_data = log.dict()
            elif isinstance(log, dict):
                log_data = log
            else:
                continue

            start_t = log_data.get("start_time") or log_data.get("logged_at")
            if not start_t:
                continue
            try:
                start_dt = datetime.fromisoformat(start_t)
                end_t = log_data.get("end_time")
                end_dt = datetime.fromisoformat(end_t) if end_t else None
                dur = log_data.get("duration_minutes") or (
                    int((end_dt - start_dt).total_seconds() / 60) if end_dt else 0
                )
                valid_logs.append({
                    "action": log_data.get("action", "wake"),
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "duration_minutes": max(0, dur),
                    "start_iso": start_t,
                    "end_iso": end_t or start_t,
                })
            except Exception:
                continue

        valid_logs.sort(key=lambda x: x["start_dt"])

        # 2. Phân nhóm log theo từng ngày (Day 0 = Hôm nay, Day -1, Day -2... Day -5)
        today_date = now_dt.date()
        daily_logs: Dict[int, List[Dict[str, Any]]] = {d: [] for d in range(-5, 1)}

        for item in valid_logs:
            log_date = item["start_dt"].date()
            offset = (log_date - today_date).days
            if -5 <= offset <= 0:
                daily_logs[offset].append(item)

        # 3. Trích xuất đặc trưng Hôm nay (Day 0)
        today_items = daily_logs[0]
        day_start_min = 420  # Mặc định 07:00 (420 phút)
        night_end_min = 390  # Mặc định 06:30 (390 phút)
        prior_ww_today: List[int] = []
        naps_today: List[int] = []
        
        last_wake_dt = None
        last_sleep_dur = 0
        last_nap_dur = 0

        # Lấy mốc dậy sáng đầu tiên
        if today_items:
            first_event = today_items[0]
            day_start_min = _iso_to_minutes_from_midnight(first_event["start_iso"])
            night_end_min = day_start_min

        # Duyệt qua các giấc trong ngày để tính wake windows
        prev_end_dt = None
        for event in today_items:
            dur = event["duration_minutes"]
            st = event["start_dt"]
            et = event["end_dt"] or st

            if prev_end_dt and st > prev_end_dt:
                ww = int((st - prev_end_dt).total_seconds() / 60)
                if 10 <= ww <= 480:
                    prior_ww_today.append(ww)

            if dur > 0:
                naps_today.append(dur)
                last_sleep_dur = dur
                last_nap_dur = dur

            prev_end_dt = et
            last_wake_dt = et

        nap_number = len(naps_today) + 1
        previous_nap_min = last_nap_dur if nap_number > 1 else 0
        previous_sleep_dur_min = last_sleep_dur if last_sleep_dur > 0 else (600 if nap_number == 1 else 60)

        # Wake window ngay trước đó
        if prior_ww_today:
            prev_ww_min = prior_ww_today[-1]
        else:
            prev_ww_min = 120  # Mặc định 2 tiếng nếu là Nap 1

        # Thời gian bé thực tế đã thức đến hiện tại
        if last_wake_dt:
            wake_elapsed = max(0, int((now_dt - last_wake_dt).total_seconds() / 60))
        else:
            wake_elapsed = 0

        # 4. Trích xuất Biểu diễn Ma trận 5 Ngày Gần Nhất (Day -5 đến Day -1)
        # [DIRECTLY SUPPORTED BY PATENT]
        day_representations: List[SingleDaySleepRepresentation] = []
        all_5d_wws: List[int] = []
        all_5d_naps: List[int] = []
        all_5d_nights: List[int] = []

        days_with_data_count = 0

        for day_offset in range(-5, 0):
            day_events = daily_logs[day_offset]
            day_wws: List[int] = []
            day_naps: List[int] = []
            day_night_dur = None
            d_start = None

            if day_events:
                days_with_data_count += 1
                p_end = None
                for ev in day_events:
                    st = ev["start_dt"]
                    et = ev["end_dt"] or st
                    dur = ev["duration_minutes"]

                    if p_end and st > p_end:
                        ww = int((st - p_end).total_seconds() / 60)
                        if 15 <= ww <= 480:
                            day_wws.append(ww)
                            all_5d_wws.append(ww)

                    if dur >= 240:  # Giấc ngủ đêm > 4h
                        day_night_dur = dur
                        all_5d_nights.append(dur)
                    elif dur > 0:
                        day_naps.append(dur)
                        all_5d_naps.append(dur)

                    p_end = et

                if day_events:
                    d_start = _iso_to_minutes_from_midnight(day_events[0]["start_iso"])

            day_representations.append(
                SingleDaySleepRepresentation(
                    day_offset=day_offset,
                    wake_windows_minutes=day_wws,
                    naps_duration_minutes=day_naps,
                    night_sleep_duration_minutes=day_night_dur,
                    day_start_minutes=d_start,
                )
            )

        # Tính toán các giá trị thống kê 5 ngày [PROJECT IMPLEMENTATION]
        if all_5d_wws:
            avg_ww_5d = float(sum(all_5d_wws) / len(all_5d_wws))
            variance = sum((x - avg_ww_5d) ** 2 for x in all_5d_wws) / len(all_5d_wws)
            std_ww_5d = float(math.sqrt(variance))
        else:
            avg_ww_5d = 120.0
            std_ww_5d = 15.0

        avg_nap_dur_5d = float(sum(all_5d_naps) / len(all_5d_naps)) if all_5d_naps else 60.0
        avg_night_hours_5d = float(sum(all_5d_nights) / len(all_5d_nights) / 60.0) if all_5d_nights else 11.0
        avg_naps_count_5d = float(len(all_5d_naps) / max(1, days_with_data_count)) if days_with_data_count > 0 else 3.0

        last_5d_history = Last5DaysHistoryRepresentation(
            days=day_representations,
            avg_wake_window_minutes=round(avg_ww_5d, 1),
            std_wake_window_minutes=round(std_ww_5d, 1),
            avg_nap_duration_minutes=round(avg_nap_dur_5d, 1),
            avg_night_sleep_hours=round(avg_night_hours_5d, 1),
            avg_naps_count_per_day=round(avg_naps_count_5d, 1),
        )

        # 5. Xác định các cờ phụ trợ
        is_first = 1 if nap_number == 1 else 0
        is_bedtime = 1 if (age_months >= 6 and nap_number >= 3) or (age_months < 6 and nap_number >= 4) else 0
        is_cat = 1 if 0 < previous_nap_min < 35 else 0
        is_long = 1 if previous_nap_min >= 90 else 0

        return WakeWindowFeatureVector(
            age_months=age_months,
            age_days=age_days,
            nap_number=nap_number,
            day_start_minutes=day_start_min,
            previous_night_end_minutes=night_end_min,
            previous_wake_window_minutes=prev_ww_min,
            prior_wake_windows_today=prior_ww_today,
            previous_nap_minutes=previous_nap_min,
            previous_sleep_duration_minutes=previous_sleep_dur_min,
            previous_wake_duration_minutes=wake_elapsed,
            last_5_days_history=last_5d_history,
            is_first_nap=is_first,
            is_bedtime_nap=is_bedtime,
            is_catnap=is_cat,
            is_long_nap=is_long,
            data_days_available=days_with_data_count,
        )
