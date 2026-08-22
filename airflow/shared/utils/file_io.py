import json
import os
from pathlib import Path
from typing import Any

# Thư mục lưu dữ liệu trung gian giữa các Airflow Tasks
DAG_DATA_DIR = os.getenv("DAG_DATA_DIR", "/opt/airflow/data/dag_runs")


def write_data_to_file(data: Any, filename: str) -> str:
    """
    Ghi dữ liệu JSON ra file trên đĩa để chuyển tiếp giữa các Airflow Tasks (Claim-Check pattern).
    Giúp XCom chỉ cần truyền đường dẫn file, tránh làm phình to Airflow Metadata DB.

    Args:
        data: Dữ liệu (list, dict, primitive) cần serialize thành JSON.
        filename: Tên file đích.

    Returns:
        Đường dẫn tuyệt đối đến file vừa ghi.
    """
    target_dir = Path(DAG_DATA_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return str(file_path)


def read_data_from_file(file_path: str) -> Any:
    """
    Đọc dữ liệu JSON từ file trung gian do task trước tạo ra.

    Args:
        file_path: Đường dẫn tới file JSON trên đĩa.

    Returns:
        Dữ liệu đã được deserialize từ JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file trung gian tại: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
