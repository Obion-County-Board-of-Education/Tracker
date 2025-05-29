from fastapi import FastAPI

app = FastAPI(title="OCS Inventory API")

@app.get("/")
def root():
    return {"message": "OCS Inventory API is running."}
