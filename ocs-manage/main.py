from fastapi import FastAPI
from ocs_shared_models import models  # Import shared SQLAlchemy models
from .database import engine

# Create tables if they don't exist (optional, for dev)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "OCS Manage API is running."}
