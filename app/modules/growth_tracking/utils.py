"""
Growth Tracking Utilities Module

Contains WHO Growth Standards data tables and helper functions to evaluate baby growth.
"""
import random

# Tiêu chuẩn WHO cho Bé Trai (Boy)
BOY_STANDARDS = {
    # month: {"weight": (sd-2, median, sd+2), "height": (sd-2, median, sd+2), "head": (sd-2, median, sd+2)}
    0: {"weight": (2.5, 3.3, 4.4), "height": (46.3, 49.9, 53.4), "head": (32.1, 34.5, 36.9)},
    1: {"weight": (3.4, 4.5, 5.8), "height": (51.1, 54.7, 58.4), "head": (35.1, 37.3, 39.5)},
    2: {"weight": (4.3, 5.6, 7.1), "height": (54.7, 58.4, 62.2), "head": (36.9, 39.1, 41.3)},
    3: {"weight": (5.0, 6.4, 8.0), "height": (57.6, 61.4, 65.3), "head": (38.3, 40.5, 42.7)},
    6: {"weight": (6.4, 7.9, 9.8), "height": (63.6, 67.6, 71.6), "head": (41.0, 43.3, 45.6)},
    9: {"weight": (7.1, 8.9, 11.0), "height": (67.5, 72.0, 76.5), "head": (42.5, 45.0, 47.5)},
    12: {"weight": (7.7, 9.6, 12.0), "height": (71.0, 75.7, 80.5), "head": (43.6, 46.1, 48.6)},
    18: {"weight": (8.6, 10.9, 13.5), "height": (76.9, 82.3, 87.7), "head": (44.9, 47.4, 49.9)},
    24: {"weight": (9.7, 12.2, 15.3), "height": (82.1, 87.8, 93.5), "head": (45.7, 48.3, 50.9)},
}

# Tiêu chuẩn WHO cho Bé Gái (Girl)
GIRL_STANDARDS = {
    0: {"weight": (2.4, 3.2, 4.2), "height": (45.6, 49.1, 52.7), "head": (31.7, 33.9, 36.1)},
    1: {"weight": (3.2, 4.2, 5.5), "height": (50.0, 53.7, 57.4), "head": (34.3, 36.5, 38.7)},
    2: {"weight": (3.9, 5.1, 6.6), "height": (53.2, 57.1, 60.9), "head": (36.0, 38.2, 40.4)},
    3: {"weight": (4.5, 5.8, 7.5), "height": (55.8, 59.8, 63.8), "head": (37.2, 39.5, 41.8)},
    6: {"weight": (5.7, 7.3, 9.3), "height": (61.2, 65.7, 70.3), "head": (39.7, 42.1, 44.5)},
    9: {"weight": (6.5, 8.2, 10.4), "height": (65.3, 69.9, 74.5), "head": (41.2, 43.5, 45.8)},
    12: {"weight": (7.0, 8.9, 11.5), "height": (68.9, 74.0, 79.2), "head": (42.2, 44.6, 47.0)},
    18: {"weight": (8.1, 10.2, 12.9), "height": (74.9, 80.7, 86.5), "head": (43.7, 46.0, 48.3)},
    24: {"weight": (9.0, 11.5, 14.8), "height": (80.0, 86.4, 92.9), "head": (44.6, 46.9, 49.2)},
}

def get_closest_standard(gender: str, age_months: float) -> dict:
    """
    Tìm mốc tháng tuổi gần nhất trong chuẩn WHO tương ứng với giới tính của bé.
    """
    standards = BOY_STANDARDS if gender.lower() == "boy" else GIRL_STANDARDS
    closest_month = min(standards.keys(), key=lambda x: abs(x - age_months))
    return standards[closest_month]

def evaluate_metric(value: float, limits: tuple[float, float, float], low_label: str, high_label: str) -> str:
    """
    So sánh giá trị đo đạc với giới hạn của WHO để phân loại.
    """
    sd_low, median, sd_high = limits
    if value < sd_low:
        return low_label
    elif value > sd_high:
        return high_label
    return "normal"
