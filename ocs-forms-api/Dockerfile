FROM python:3.11-slim
WORKDIR /app

# Install PostgreSQL client and curl for healthcheck
RUN apt-get update && apt-get install -y postgresql-client curl && rm -rf /var/lib/apt/lists/*

# Copy shared models first
COPY ocs_shared_models/ ./ocs_shared_models/
# Copy service requirements and install
COPY ocs-forms-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy service code
COPY ocs-forms-api/ ./
# Copy healthcheck script and ensure proper line endings
COPY ocs-forms-api/healthcheck.sh ./
RUN chmod +x healthcheck.sh && \
    # Convert any remaining Windows line endings to Unix
    sed -i 's/\r$//' healthcheck.sh && \
    # Verify the script is executable and syntax is correct
    ls -la healthcheck.sh && \
    bash -n healthcheck.sh && \
    echo "✓ Healthcheck script validated"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
