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
    return templates.TemplateResponse("inventory_success.html", {"request": request})

@app.get("/inventory/remove")
def remove_inventory_form(request: Request):
    return templates.TemplateResponse("remove_inventory.html", {"request": request, "item_found": False, "searched": False})

@app.post("/inventory/remove")
def remove_inventory_search(request: Request):
    # TODO: Search logic for inventory item based on form fields
    # For now, simulate not found
    return templates.TemplateResponse("remove_inventory.html", {"request": request, "item_found": False, "searched": True})

@app.post("/inventory/remove/confirm")
def remove_inventory_confirm(request: Request):
    # TODO: Remove item from inventory
    return templates.TemplateResponse("inventory_success.html", {"request": request})

@app.get("/inventory/view")
def view_inventory(request: Request):
    # Placeholder inventory data for demonstration
    inventory = [
        {"tag": "1001", "type": "Computer", "brand": "Dell", "model": "OptiPlex 3080", "serial": "SN12345", "po_number": "PO123", "price": "$800", "purchase_date": "2024-08-01", "school": "Black Oak", "room": "101"},
        {"tag": "1002", "type": "Printer", "brand": "HP", "model": "LaserJet Pro", "serial": "SN67890", "po_number": "PO124", "price": "$200", "purchase_date": "2024-09-15", "school": "Hillcrest", "room": "202"},
    ]
    return templates.TemplateResponse("view_inventory.html", {"request": request, "inventory": inventory})
