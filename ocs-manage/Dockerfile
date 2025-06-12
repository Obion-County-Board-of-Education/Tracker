FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models first
COPY ocs_shared_models/ ./ocs_shared_models/

# Install shared models as package
RUN pip install -e ./ocs_shared_models/

# Copy service requirements and install dependencies
COPY ocs-manage/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY ocs-manage/ ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
