#!/bin/bash
set -e

# Script khởi tạo cơ sở dữ liệu PostgreSQL cho Airflow và RAG Metadata
echo "[Init DB] Khởi tạo database và phân quyền..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOSQL

echo "[Init DB] Hoàn tất khởi tạo PostgreSQL extensions!"
