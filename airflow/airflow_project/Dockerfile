FROM apache/airflow:2.8.1-python3.10

USER root

# Cài đặt các công cụ hệ thống nếu cần
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Cài đặt shared package requirements
COPY --chown=airflow:root shared/requirements.txt /tmp/shared_requirements.txt
RUN pip install --no-cache-dir -r /tmp/shared_requirements.txt

# Sao chép shared package vào PYTHONPATH
COPY --chown=airflow:root shared /opt/airflow/airflow/shared
ENV PYTHONPATH="/opt/airflow:${PYTHONPATH}"
