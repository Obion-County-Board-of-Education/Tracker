from fastapi import FastAPI

app = FastAPI(title="OCS Requisition API")

@app.get("/")
def root():
    return {"message": "OCS Requisition API is running."}
