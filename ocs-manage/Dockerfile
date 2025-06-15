FROM python:3.11-slim
WORKDIR /app

# Install PostgreSQL client for healthcheck
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY ocs_shared_models/ ./ocs_shared_models/
COPY ocs-manage/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ocs-manage/ .
# Copy healthcheck script
COPY healthcheck.sh ./
RUN chmod +x healthcheck.sh

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
