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

@app.get("/tickets/success")
def ticket_success(request: Request):
    return templates.TemplateResponse("ticket_success.html", {"request": request})

@app.get("/users/list")
def users_list(request: Request):
    # TODO: Replace with real data from the database
    users = [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "role": "Admin"},
        {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "role": "Technician"},
        {"id": 3, "name": "Carol Lee", "email": "carol@example.com", "role": "User"},
    ]
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@app.get("/users/add")
def add_user_form(request: Request):
    return templates.TemplateResponse("add_user.html", {"request": request})

@app.post("/users/add")
def add_user_submit(request: Request, name: str = Form(...), email: str = Form(...), role: str = Form(...)):
    # TODO: Save user to the database
    return RedirectResponse("/users/list", status_code=303)

@app.get("/users/edit/{user_id}")
def edit_user_form(request: Request, user_id: int):
    # TODO: Fetch user from the database
    user = {"id": user_id, "name": "Sample User", "email": "sample@example.com", "role": "User"}
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})

@app.post("/users/edit/{user_id}")
def edit_user_submit(request: Request, user_id: int, name: str = Form(...), email: str = Form(...), role: str = Form(...)):
    # TODO: Update user in the database
    return RedirectResponse("/users/list", status_code=303)

@app.post("/users/delete/{user_id}")
def delete_user(request: Request, user_id: int):
    # TODO: Delete user from the database
    return RedirectResponse("/users/list", status_code=303)

@app.get("/users/roles")
def manage_roles(request: Request):
    # TODO: Replace with real data from the database
    roles = [
        {"id": 1, "name": "Admin", "permissions": ["manage_users", "manage_tickets"]},
        {"id": 2, "name": "Technician", "permissions": ["view_tickets"]},
        {"id": 3, "name": "User", "permissions": ["submit_ticket"]},
    ]
    return templates.TemplateResponse("manage_roles.html", {"request": request, "roles": roles})

@app.get("/inventory/view")
def view_inventory(request: Request):
    # TODO: Replace with real data from the database
    inventory = [
        {"tag": "1001", "type": "Computer", "brand": "Dell", "model": "OptiPlex 3080", "serial": "SN12345", "school": "Black Oak", "room": "101"},
        {"tag": "1002", "type": "Printer", "brand": "HP", "model": "LaserJet Pro", "serial": "SN67890", "school": "Hillcrest", "room": "202"},
    ]
    return templates.TemplateResponse("view_inventory.html", {"request": request, "inventory": inventory})

@app.get("/inventory/remove")
def remove_inventory_form(request: Request):
    return templates.TemplateResponse("remove_inventory.html", {"request": request, "item_found": False, "searched": False})

@app.post("/inventory/remove")
def remove_inventory_search(request: Request):
    # TODO: Implement search logic
    return templates.TemplateResponse("remove_inventory.html", {"request": request, "item_found": False, "searched": True})

@app.post("/inventory/remove/confirm")
def remove_inventory_confirm(request: Request):
    # TODO: Implement removal logic
    return templates.TemplateResponse("inventory_success.html", {"request": request})
