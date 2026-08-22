"""
Safety Guardrails & Expert Baseline Module
===========================================
Triển khai cơ chế kiểm tra giới hạn an toàn theo Bằng sáng chế US 20250292903:
- Bảng tham chiếu Expert Baseline theo tháng tuổi và thứ tự giấc.
- Kiểm tra độ lệch |ML_Pred - Expert_Baseline| <= Max_Deviation.
- Nếu Hợp lý -> Giữ nguyên kết quả ML.
- Nếu Bất thường -> Kích hoạt Fallback về Expert Value.
- Kẹp biên an toàn (Clamping [Min_Safe, Max_Safe]).
"""

from typing import Dict, Any, Tuple


# ---------------------------------------------------------------------------
# Bảng Cấu hình Biên An toàn Chuyên gia (Expert Safety Table)
# [PROJECT IMPLEMENTATION - Based on Pediatric Sleep Standards]
# ---------------------------------------------------------------------------
EXPERT_SAFETY_CONFIG = {
    # (min_age_months, max_age_months): {
    #     nap_number_map: {nap_num: (expert_ww, min_safe, max_safe, max_dev)}
    # }
    (0.0, 1.0): {
        "default": (45, 30, 60, 15),
    },
    (1.0, 2.0): {
        "default": (75, 45, 90, 20),
    },
    (2.0, 4.0): {
        1: (90, 60, 120, 25),
        2: (100, 60, 125, 25),
        3: (100, 60, 125, 25),
        "bedtime": (115, 75, 140, 25),
        "default": (100, 60, 125, 25),
    },
    (4.0, 6.0): {
        1: (120, 90, 150, 30),
        2: (135, 90, 165, 30),
        3: (135, 90, 165, 30),
        "bedtime": (150, 105, 180, 30),
        "default": (135, 90, 165, 30),
    },
    (6.0, 9.0): {
        1: (150, 120, 180, 35),
        2: (165, 120, 200, 35),
        3: (165, 120, 200, 35),
        "bedtime": (195, 135, 230, 35),
        "default": (165, 120, 200, 35),
    },
    (9.0, 12.0): {
        1: (180, 150, 225, 45),
        2: (210, 150, 255, 45),
        "bedtime": (240, 165, 285, 45),
        "default": (210, 150, 255, 45),
    },
    (12.0, 18.0): {
        1: (240, 180, 300, 45),
        2: (270, 210, 330, 45),
        "bedtime": (285, 210, 345, 45),
        "default": (270, 210, 330, 45),
    },
    (18.0, 36.0): {
        "default": (330, 240, 390, 60),
    },
}


def get_expert_baseline_config(
    age_months: float, 
    nap_number: int = 1, 
    is_bedtime: bool = False
) -> Dict[str, int]:
    """
    Tra cứu cấu hình Expert Baseline cho độ tuổi và thứ tự giấc.
    """
    for (min_age, max_age), age_dict in EXPERT_SAFETY_CONFIG.items():
        if min_age <= age_months < max_age:
            if is_bedtime and "bedtime" in age_dict:
                vals = age_dict["bedtime"]
            elif nap_number in age_dict:
                vals = age_dict[nap_number]
            else:
                vals = age_dict.get("default", (135, 90, 165, 30))
            return {
                "expert_ww": vals[0],
                "min_safe": vals[1],
                "max_safe": vals[2],
                "max_dev": vals[3],
            }

    # Default fallback nếu tuổi > 36 tháng
    return {"expert_ww": 330, "min_safe": 240, "max_safe": 420, "max_dev": 60}


class SafetyGuardrailEngine:
    """
    Bộ chốt chặn an toàn kiểm định đầu ra của Machine Learning:
    - [DIRECTLY SUPPORTED BY PATENT]: So sánh ML prediction với Expert Baseline.
    - Nếu hợp lý -> Dùng ML.
    - Nếu bất thường -> Báo cờ is_anomaly_case = True để kích hoạt Expert Value + LLM.
    """

    @classmethod
    def evaluate(
        cls,
        raw_ml_prediction: float,
        age_months: float,
        nap_number: int = 1,
        is_bedtime: bool = False,
    ) -> Dict[str, Any]:
        config = get_expert_baseline_config(age_months, nap_number, is_bedtime)
        expert_ww = config["expert_ww"]
        max_dev = config["max_dev"]
        min_safe = config["min_safe"]
        max_safe = config["max_safe"]

        deviation = abs(raw_ml_prediction - expert_ww)
        is_outside_bounds = (raw_ml_prediction < min_safe) or (raw_ml_prediction > max_safe)
        is_excessive_deviation = (deviation > max_dev)

        is_anomaly = is_outside_bounds or is_excessive_deviation

        if is_anomaly:
            # Rơi vào nhánh BẤT THƯỜNG -> Kích hoạt Expert Value + Báo cờ gọi LLM
            fallback_ww = expert_ww
            return {
                "is_anomaly": True,
                "safe_base_ww": fallback_ww,
                "expert_baseline": expert_ww,
                "max_allowed_deviation": max_dev,
                "min_safe": min_safe,
                "max_safe": max_safe,
                "raw_prediction": raw_ml_prediction,
                "source": "EXPERT_VALUE_PLUS_LLM",
                "reason": (
                    f"Dự đoán ML ({int(raw_ml_prediction)}p) lệch quá xa mốc chuyên gia ({expert_ww}p ± {max_dev}p) "
                    f"hoặc vượt biên an toàn [{min_safe}p - {max_safe}p]."
                )
            }

        # Rơi vào nhánh HỢP LÝ -> Dùng thuần ML
        clamped_ww = max(min_safe, min(max_safe, raw_ml_prediction))
        return {
            "is_anomaly": False,
            "safe_base_ww": int(round(clamped_ww)),
            "expert_baseline": expert_ww,
            "max_allowed_deviation": max_dev,
            "min_safe": min_safe,
            "max_safe": max_safe,
            "raw_prediction": raw_ml_prediction,
            "source": "LIGHTGBM_NORMAL",
            "reason": "Dự đoán ML nằm trong khoảng dung sai an toàn y khoa."
        }
