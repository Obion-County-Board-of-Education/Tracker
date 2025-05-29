from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="OCS Portal (Python)")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tickets/tech/new")
def new_tech_ticket(request: Request):
    return templates.TemplateResponse("new_tech_ticket.html", {"request": request})

@app.get("/tickets/maintenance/new")
def new_maintenance_ticket(request: Request):
    return templates.TemplateResponse("new_maintenance_ticket.html", {"request": request})

@app.get("/inventory/add")
def add_inventory_form(request: Request):
    return templates.TemplateResponse("add_inventory.html", {"request": request})

@app.post("/inventory/add")
def add_inventory_submit(request: Request):
    # TODO: Process form data and save to database
    # For now, just redirect to home or show a success message
    return RedirectResponse("/", status_code=303)
