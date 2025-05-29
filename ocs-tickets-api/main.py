from fastapi import FastAPI

app = FastAPI(title="OCS Tickets API")

@app.get("/")
def root():
    return {"message": "OCS Tickets API is running."}
