import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Thiết lập đường dẫn import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, "/opt/airflow")

from airflow.airflow_project.dags.tasks.ingestion_tasks import (
    fetch_pending_documents,
    parse_documents,
    chunk_documents,
    validate_chunks,
    mark_documents_complete,
    index_embeddings,
)

default_args = {
    "owner": "babycare_ai",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="ingest_documents_dag",
    default_args=default_args,
    description="Pipeline 6 bước tự động hóa nạp, bóc tách, phân đoạn và Vector hóa BGE-M3/FAISS cho RAG Systems",
    schedule_interval=timedelta(minutes=1),
    catchup=False,
    max_active_runs=1,
    tags=["ingestion", "documents", "rag-pipeline", "bge-m3", "faiss", "babycare"],
) as dag:

    fetch_documents_task = PythonOperator(
        task_id="fetch_documents",
        python_callable=fetch_pending_documents,
        provide_context=True,
    )

    parse_documents_task = PythonOperator(
        task_id="parse_documents",
        python_callable=parse_documents,
        provide_context=True,
    )

    chunk_documents_task = PythonOperator(
        task_id="chunk_documents",
        python_callable=chunk_documents,
        provide_context=True,
    )

    validate_chunks_task = PythonOperator(
        task_id="validate_chunks",
        python_callable=validate_chunks,
        provide_context=True,
    )

    mark_complete_task = PythonOperator(
        task_id="mark_complete",
        python_callable=mark_documents_complete,
        provide_context=True,
    )

    index_embeddings_task = PythonOperator(
        task_id="index_embeddings",
        python_callable=index_embeddings,
        provide_context=True,
    )

    # 6 Sequential Tasks Pipeline Dependency
    (
        fetch_documents_task
        >> parse_documents_task
        >> chunk_documents_task
        >> validate_chunks_task
        >> mark_complete_task
        >> index_embeddings_task
    )