FROM python:3.11-slim
WORKDIR /app
# Copy shared models first
COPY ocs_shared_models/ ./ocs_shared_models/
# Copy service requirements and install
COPY ocs-portal-py/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy service code
COPY ocs-portal-py/ ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
