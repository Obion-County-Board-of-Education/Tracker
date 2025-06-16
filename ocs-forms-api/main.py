from fastapi import FastAPI, Request, Depends, Form, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, text, and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import sys
import os

# Add the parent directory to the Python path to import shared models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ocs_shared_models import User, Building, Room
from ocs_shared_models.timezone_utils import central_now, format_central_time
from database import get_db, init_database
from auth_middleware import AuthMiddleware, get_current_user, has_permission

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Forms API")

# Add authentication middleware with excluded paths
app.add_middleware(
    AuthMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        # Allow public form submissions without auth
        "/time/entries/public",
        "/fuel/entries/public"
    ]
)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "healthy", "service": "forms-api"}

# Pydantic models for Time Forms
class TimeEntryCreate(BaseModel):
    """Model for creating a new time entry"""
    employee_name: str
    date: str  # Format: YYYY-MM-DD
    hours_worked: float
    description: str
    building_id: Optional[int] = None

class TimeEntryResponse(BaseModel):
    """Model for time entry response"""
    id: int
    employee_name: str
    date: str
    hours_worked: float
    description: str
    building_name: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Pydantic models for Fuel Forms
class FuelEntryCreate(BaseModel):
    """Model for creating a new fuel entry"""
    vehicle_id: str
    driver_name: str
    date: str  # Format: YYYY-MM-DD
    miles_driven: float
    gallons_used: float
    fuel_cost: float
    purpose: str
    building_id: Optional[int] = None

class FuelEntryResponse(BaseModel):
    """Model for fuel entry response"""
    id: int
    vehicle_id: str
    driver_name: str
    date: str
    miles_driven: float
    gallons_used: float
    fuel_cost: float
    mpg: float  # Calculated field
    purpose: str
    building_name: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Mock data for development - In production, these would come from database tables
time_entries_db = []
fuel_entries_db = []
next_time_id = 1
next_fuel_id = 1

# Time Forms Endpoints
@app.get("/time/entries", response_model=List[TimeEntryResponse])
async def get_time_entries(
    db: Session = Depends(get_db),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    employee: Optional[str] = Query(None, description="Employee name filter")
):
    """Get all time entries with optional filtering"""
    # For now, return mock data. In production, query database tables
    entries = time_entries_db.copy()
    
    # Apply filters
    if employee:
        entries = [e for e in entries if employee.lower() in e["employee_name"].lower()]
    
    if date_from:
        entries = [e for e in entries if e["date"] >= date_from]
    
    if date_to:
        entries = [e for e in entries if e["date"] <= date_to]
    
    return entries

@app.post("/time/entries", response_model=TimeEntryResponse)
async def create_time_entry(entry: TimeEntryCreate, db: Session = Depends(get_db)):
    """Create a new time entry"""
    global next_time_id
    
    # Get building name if building_id provided
    building_name = None
    if entry.building_id:
        building = db.query(Building).filter(Building.id == entry.building_id).first()
        building_name = building.name if building else None
    
    # Create new entry
    new_entry = {
        "id": next_time_id,
        "employee_name": entry.employee_name,
        "date": entry.date,
        "hours_worked": entry.hours_worked,
        "description": entry.description,
        "building_name": building_name,
        "created_at": central_now().isoformat(),
        "updated_at": None
    }
    
    time_entries_db.append(new_entry)
    next_time_id += 1
    
    return new_entry

@app.get("/time/entries/{entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(entry_id: int):
    """Get a specific time entry by ID"""
    entry = next((e for e in time_entries_db if e["id"] == entry_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry

@app.put("/time/entries/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(entry_id: int, entry: TimeEntryCreate, db: Session = Depends(get_db)):
    """Update an existing time entry"""
    existing_entry = next((e for e in time_entries_db if e["id"] == entry_id), None)
    if not existing_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Get building name if building_id provided
    building_name = None
    if entry.building_id:
        building = db.query(Building).filter(Building.id == entry.building_id).first()
        building_name = building.name if building else None
    
    # Update entry
    existing_entry.update({
        "employee_name": entry.employee_name,
        "date": entry.date,
        "hours_worked": entry.hours_worked,
        "description": entry.description,
        "building_name": building_name,
        "updated_at": central_now().isoformat()
    })
    
    return existing_entry

@app.delete("/time/entries/{entry_id}")
async def delete_time_entry(entry_id: int):
    """Delete a time entry"""
    global time_entries_db
    time_entries_db = [e for e in time_entries_db if e["id"] != entry_id]
    return {"message": "Time entry deleted successfully"}

# Fuel Forms Endpoints
@app.get("/fuel/entries", response_model=List[FuelEntryResponse])
async def get_fuel_entries(
    db: Session = Depends(get_db),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vehicle: Optional[str] = Query(None, description="Vehicle ID filter"),
    driver: Optional[str] = Query(None, description="Driver name filter")
):
    """Get all fuel entries with optional filtering"""
    # For now, return mock data. In production, query database tables
    entries = fuel_entries_db.copy()
    
    # Apply filters
    if vehicle:
        entries = [e for e in entries if vehicle.lower() in e["vehicle_id"].lower()]
    
    if driver:
        entries = [e for e in entries if driver.lower() in e["driver_name"].lower()]
    
    if date_from:
        entries = [e for e in entries if e["date"] >= date_from]
    
    if date_to:
        entries = [e for e in entries if e["date"] <= date_to]
    
    return entries

@app.post("/fuel/entries", response_model=FuelEntryResponse)
async def create_fuel_entry(entry: FuelEntryCreate, db: Session = Depends(get_db)):
    """Create a new fuel entry"""
    global next_fuel_id
    
    # Get building name if building_id provided
    building_name = None
    if entry.building_id:
        building = db.query(Building).filter(Building.id == entry.building_id).first()
        building_name = building.name if building else None
    
    # Calculate MPG
    mpg = round(entry.miles_driven / entry.gallons_used, 2) if entry.gallons_used > 0 else 0
    
    # Create new entry
    new_entry = {
        "id": next_fuel_id,
        "vehicle_id": entry.vehicle_id,
        "driver_name": entry.driver_name,
        "date": entry.date,
        "miles_driven": entry.miles_driven,
        "gallons_used": entry.gallons_used,
        "fuel_cost": entry.fuel_cost,
        "mpg": mpg,
        "purpose": entry.purpose,
        "building_name": building_name,
        "created_at": central_now().isoformat(),
        "updated_at": None
    }
    
    fuel_entries_db.append(new_entry)
    next_fuel_id += 1
    
    return new_entry

@app.get("/fuel/entries/{entry_id}", response_model=FuelEntryResponse)
async def get_fuel_entry(entry_id: int):
    """Get a specific fuel entry by ID"""
    entry = next((e for e in fuel_entries_db if e["id"] == entry_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Fuel entry not found")
    return entry

@app.put("/fuel/entries/{entry_id}", response_model=FuelEntryResponse)
async def update_fuel_entry(entry_id: int, entry: FuelEntryCreate, db: Session = Depends(get_db)):
    """Update an existing fuel entry"""
    existing_entry = next((e for e in fuel_entries_db if e["id"] == entry_id), None)
    if not existing_entry:
        raise HTTPException(status_code=404, detail="Fuel entry not found")
    
    # Get building name if building_id provided
    building_name = None
    if entry.building_id:
        building = db.query(Building).filter(Building.id == entry.building_id).first()
        building_name = building.name if building else None
    
    # Calculate MPG
    mpg = round(entry.miles_driven / entry.gallons_used, 2) if entry.gallons_used > 0 else 0
    
    # Update entry
    existing_entry.update({
        "vehicle_id": entry.vehicle_id,
        "driver_name": entry.driver_name,
        "date": entry.date,
        "miles_driven": entry.miles_driven,
        "gallons_used": entry.gallons_used,
        "fuel_cost": entry.fuel_cost,
        "mpg": mpg,
        "purpose": entry.purpose,
        "building_name": building_name,
        "updated_at": central_now().isoformat()
    })
    
    return existing_entry

@app.delete("/fuel/entries/{entry_id}")
async def delete_fuel_entry(entry_id: int):
    """Delete a fuel entry"""
    global fuel_entries_db
    fuel_entries_db = [e for e in fuel_entries_db if e["id"] != entry_id]
    return {"message": "Fuel entry deleted successfully"}

# Summary/Report Endpoints
@app.get("/time/summary")
async def get_time_summary(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get time sheet summary statistics"""
    entries = time_entries_db.copy()
    
    # Apply date filters
    if date_from:
        entries = [e for e in entries if e["date"] >= date_from]
    if date_to:
        entries = [e for e in entries if e["date"] <= date_to]
    
    total_hours = sum(e["hours_worked"] for e in entries)
    total_entries = len(entries)
    unique_employees = len(set(e["employee_name"] for e in entries))
    
    return {
        "total_hours": total_hours,
        "total_entries": total_entries,
        "unique_employees": unique_employees,
        "average_hours_per_entry": round(total_hours / total_entries, 2) if total_entries > 0 else 0
    }

@app.get("/fuel/summary")
async def get_fuel_summary(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get fuel sheet summary statistics"""
    entries = fuel_entries_db.copy()
    
    # Apply date filters
    if date_from:
        entries = [e for e in entries if e["date"] >= date_from]
    if date_to:
        entries = [e for e in entries if e["date"] <= date_to]
    
    total_miles = sum(e["miles_driven"] for e in entries)
    total_gallons = sum(e["gallons_used"] for e in entries)
    total_cost = sum(e["fuel_cost"] for e in entries)
    total_entries = len(entries)
    unique_vehicles = len(set(e["vehicle_id"] for e in entries))
    
    average_mpg = round(total_miles / total_gallons, 2) if total_gallons > 0 else 0
    
    return {
        "total_miles": total_miles,
        "total_gallons": total_gallons,
        "total_cost": total_cost,
        "total_entries": total_entries,
        "unique_vehicles": unique_vehicles,
        "average_mpg": average_mpg,
        "cost_per_mile": round(total_cost / total_miles, 3) if total_miles > 0 else 0
    }

# Buildings endpoint for dropdowns
@app.get("/buildings")
async def get_buildings(db: Session = Depends(get_db)):
    """Get all buildings for form dropdowns"""
    buildings = db.query(Building).order_by(Building.name).all()
    return [{"id": building.id, "name": building.name} for building in buildings]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
