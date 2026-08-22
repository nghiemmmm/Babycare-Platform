"""
Synthetic Pediatric Sleep Dataset Generator & LightGBM Global Trainer
=====================================================================
Sinh tập dữ liệu mẫu chuẩn Y khoa (AASM/WHO) mô phỏng 10,000+ trẻ em
và huấn luyện mô hình Global LightGBM Regressor theo Patent US 20250292903.
"""

import os
import random
import math
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "app" / "ai" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_OUT_PATH = MODELS_DIR / "global_lightgbm_wake_window.txt"


def generate_synthetic_dataset(num_samples: int = 15000):
    """
    Sinh dataset dạng bảng phẳng cho Global Training:
    - X_t: [age_months, nap_number, day_start_min, prev_night_end_min, prev_ww_min, prev_nap_min, prev_sleep_dur_min, avg_ww_5d, std_ww_5d, is_first, is_bedtime, is_catnap, is_long_nap]
    - y_t: wake_window_actual (phút)
    """
    random.seed(42)
    np.random.seed(42)

    X = []
    y = []

    # Các nhóm tuổi (tháng)
    age_groups = [
        (0.5, 1.5, 50, 15),   # 1 tháng: ~50p
        (1.5, 3.0, 80, 20),   # 2-3 tháng: ~80p
        (3.0, 5.0, 110, 25),  # 4-5 tháng: ~110p
        (5.0, 7.0, 140, 30),  # 6-7 tháng: ~140p
        (7.0, 10.0, 170, 35), # 8-9 tháng: ~170p
        (10.0, 14.0, 215, 40),# 10-13 tháng: ~215p
        (14.0, 24.0, 280, 45),# 14-24 tháng: ~280p
    ]

    for _ in range(num_samples):
        # 1. Chọn ngẫu nhiên nhóm tuổi
        min_a, max_a, exp_ww, std_dev = random.choice(age_groups)
        age = round(random.uniform(min_a, max_a), 2)

        # 2. Đặc điểm sinh học cá nhân của bé (Individual Baby Biotype: ±15%)
        baby_biotype_factor = random.uniform(0.85, 1.15)
        personal_avg_ww = exp_ww * baby_biotype_factor

        # 3. Thứ tự giấc nap
        if age < 4.0:
            nap_num = random.choice([1, 2, 3, 4])
            is_bedtime = 1 if nap_num >= 4 else 0
        elif age < 9.0:
            nap_num = random.choice([1, 2, 3])
            is_bedtime = 1 if nap_num >= 3 else 0
        elif age < 14.0:
            nap_num = random.choice([1, 2])
            is_bedtime = 1 if nap_num >= 2 else 0
        else:
            nap_num = 1
            is_bedtime = 1

        is_first = 1 if nap_num == 1 else 0

        # 4. Mốc thời gian
        day_start = random.randint(360, 480) # 06:00 - 08:00
        prev_night_end = day_start - random.randint(0, 30)

        # 5. Lịch sử 5 ngày gần nhất
        avg_ww_5d = personal_avg_ww + random.gauss(0, 5)
        std_ww_5d = max(5.0, random.gauss(12, 3))

        # 6. Giấc ngủ liền trước
        if is_first:
            prev_nap = 0
            prev_sleep_dur = random.randint(540, 720) # 9-12h đêm
            prev_ww = int(personal_avg_ww)
        else:
            prev_nap = random.choice([30, 45, 60, 75, 90, 120])
            prev_sleep_dur = prev_nap
            prev_ww = int(personal_avg_ww + random.gauss(0, 10))

        is_catnap = 1 if 0 < prev_nap < 35 else 0
        is_long_nap = 1 if prev_nap >= 90 else 0

        # 7. Tính target y_t (Actual Wake Window)
        target = personal_avg_ww
        if is_first:
            target -= 15
        if is_bedtime:
            target += 25
        if is_catnap:
            target -= 20
        elif is_long_nap:
            target += 15

        # Nhiễu sinh học ngẫu nhiên
        target += random.gauss(0, 8)
        target = max(30.0, target)

        features = [
            age,
            nap_num,
            day_start,
            prev_night_end,
            prev_ww,
            prev_nap,
            prev_sleep_dur,
            avg_ww_5d,
            std_ww_5d,
            is_first,
            is_bedtime,
            is_catnap,
            is_long_nap,
        ]

        X.append(features)
        y.append(target)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_global_lightgbm():
    """Huấn luyện mô hình Global LightGBM và lưu tệp binary/txt."""
    print("[INFO] Dang sinh 20,000 mau du lieu giac ngu chuan Nhi khoa AASM/WHO...")
    X, y = generate_synthetic_dataset(num_samples=20000)

    # Chia Train (80%) và Validation (20%)
    split_idx = int(0.8 * len(X))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    try:
        import lightgbm as lgb
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        params = {
            "objective": "regression_l1",  # MAE Loss chống outliers
            "metric": ["mae", "rmse"],
            "boosting_type": "gbdt",
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_data_in_leaf": 20,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 1,
            "verbose": -1,
        }

        print("[INFO] Dang huan luyen Global LightGBM Regressor...")
        booster = lgb.train(
            params,
            train_data,
            num_boost_round=300,
            valid_sets=[train_data, val_data],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)],
        )

        # Đánh giá trên Validation Set
        preds = booster.predict(X_val)
        mae = float(np.mean(np.abs(preds - y_val)))
        rmse = float(np.sqrt(np.mean((preds - y_val) ** 2)))
        within_10m = float(np.mean(np.abs(preds - y_val) <= 10.0) * 100)

        print(f"\n[REPORT] KET QUA DANH GIA MO HINH GLOBAL LIGHTGBM:")
        print(f"   * MAE (Sai so tuyet doi trung binh): {mae:.2f} phut")
        print(f"   * RMSE: {rmse:.2f} phut")
        print(f"   * Ty le du doan chinh xac trong +-10 phut: {within_10m:.1f}%")

        # Lưu model
        booster.save_model(str(MODEL_OUT_PATH))
        print(f"[SUCCESS] Da luu file mo hinh tai: {MODEL_OUT_PATH}")

    except Exception as e:
        print(f"[ERROR] Loi khi huan luyen LightGBM: {e}")


if __name__ == "__main__":
    train_global_lightgbm()
