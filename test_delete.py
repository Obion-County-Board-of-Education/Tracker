from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ocs_tickets_api.database import get_db

app = FastAPI()

@app.get("/test")
def test_get():
    return {"method": "GET works"}

@app.delete("/test")
def test_delete():
    return {"method": "DELETE works"}

@app.delete("/api/tickets/tech/archives/{archive_name}")
def delete_tech_archive_test(
    archive_name: str,
    db: Session = Depends(get_db)
):
    """Delete a tech ticket archive table - test version"""
    return {
        "success": True,
        "message": f"Archive '{archive_name}' would be deleted",
        "archive_name": archive_name
    }
