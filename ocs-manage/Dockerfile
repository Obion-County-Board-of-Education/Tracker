FROM python:3.11-slim
WORKDIR /app
COPY ocs_shared_models/ ./ocs_shared_models/
COPY ocs-manage/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ocs-manage/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
