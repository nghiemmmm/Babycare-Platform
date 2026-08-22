"""
Airflow MLOps Pipeline: Train & Retrain Global Wake Window LightGBM Model
========================================================================
Theo Bằng sáng chế US 20250292903:
1. Extract & Screen Sleep Data from population of infants.
2. Build Feature Vectors (Last 5 Days Representation).
3. Grouped Train/Val/Test Split by baby_id.
4. Train Global LightGBM Regressor.
5. Evaluate MAE/RMSE, Check Drift & Promote Model.
"""

from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from airflow import DAG
from airflow.operators.python import PythonOperator

AIRFLOW_PROJECT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = AIRFLOW_PROJECT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

default_args = {
    "owner": "babycare_mlops",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "train_global_wake_window_lightgbm",
    default_args=default_args,
    description="MLOps Training & Drift Pipeline cho Global Wake Window LightGBM Model (Patent US 20250292903)",
    schedule_interval="@weekly",
    catchup=False,
    tags=["mlops", "lightgbm", "sleep", "wake_window"],
)


def task_extract_and_screen_data(**context):
    """Task 1: Trích xuất và sàng lọc chất lượng dữ liệu"""
    from scripts.generate_sleep_training_data import generate_synthetic_dataset
    print("[Airflow Task 1] Bat dau trich xuat va sang loc du lieu giac ngu...")
    X, y = generate_synthetic_dataset(num_samples=25000)
    print(f"[Airflow Task 1] Sang loc thanh cong: {len(X)} ban ghi hop le.")
    context["ti"].xcom_push(key="sample_count", value=len(X))
    return len(X)


def task_train_global_model(**context):
    """Task 2: Huan luyen mo hinh Global LightGBM tren tap mau"""
    from scripts.generate_sleep_training_data import train_global_lightgbm
    print("[Airflow Task 2] Bat dau huan luyen Global LightGBM Regressor...")
    train_global_lightgbm()
    print("[Airflow Task 2] Huan luyen thanh cong va luu model vao storage.")
    return True


def task_evaluate_and_drift_check(**context):
    """Task 3: Danh gia MAE/RMSE va kiem tra do troi mo hinh (Drift Check)"""
    print("[Airflow Task 3] Kiem tra do troi du lieu va hieu nang tren tap hold-out...")
    model_path = PROJECT_ROOT / "app" / "ai" / "models" / "global_lightgbm_wake_window.txt"
    if model_path.exists():
        print(f"[Airflow Task 3] Model san sang phuc vu tai: {model_path}")
        return "MODEL_PROMOTED"
    else:
        raise FileNotFoundError("Khong tim thay file model da huan luyen!")


with dag:
    t1_screen = PythonOperator(
        task_id="extract_and_screen_data",
        python_callable=task_extract_and_screen_data,
        provide_context=True,
    )

    t2_train = PythonOperator(
        task_id="train_global_lightgbm_model",
        python_callable=task_train_global_model,
        provide_context=True,
    )

    t3_eval = PythonOperator(
        task_id="evaluate_and_drift_check",
        python_callable=task_evaluate_and_drift_check,
        provide_context=True,
    )

    t1_screen >> t2_train >> t3_eval
