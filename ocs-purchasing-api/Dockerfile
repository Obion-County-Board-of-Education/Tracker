FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models first
COPY ocs_shared_models/ ./ocs_shared_models/

# Install shared models as package
RUN pip install -e ./ocs_shared_models/

# Copy service requirements and install dependencies
COPY ocs-purchasing-api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY ocs-purchasing-api/ ./

# Copy healthcheck script and ensure proper line endings
COPY ocs-purchasing-api/healthcheck.sh ./
RUN chmod +x healthcheck.sh && \
    # Convert any remaining Windows line endings to Unix
    sed -i 's/\r$//' healthcheck.sh && \
    # Verify the script is executable and syntax is correct
    ls -la healthcheck.sh && \
    bash -n healthcheck.sh && \
    echo "✓ Healthcheck script validated"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
