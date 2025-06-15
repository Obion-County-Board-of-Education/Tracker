FROM python:3.11-slim
WORKDIR /app

# Install PostgreSQL client for healthcheck
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy shared models first
COPY ocs_shared_models/ ./ocs_shared_models/
# Copy service requirements and install
COPY ocs-portal-py/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy service code
COPY ocs-portal-py/ ./
# Copy healthcheck script
COPY healthcheck.sh ./
RUN chmod +x healthcheck.sh

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
