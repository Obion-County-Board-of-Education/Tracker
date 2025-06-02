from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building, Room
from database import get_db, init_database

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Tickets API")
templates = Jinja2Templates(directory="../ocs-portal-py/templates")

@app.get("/")
def root():
    return {"message": "OCS Tickets API is running."}

@app.get("/tickets/success")
def ticket_success(request: Request):
    return templates.TemplateResponse("ticket_success.html", {"request": request})

@app.get("/tickets/tech/new")
def new_tech_ticket(request: Request):
    return templates.TemplateResponse("new_tech_ticket.html", {"request": request})

@app.get("/tickets/maintenance/new")
def new_maintenance_ticket(request: Request):
    return templates.TemplateResponse("new_maintenance_ticket.html", {"request": request})
