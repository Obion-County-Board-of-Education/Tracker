from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Text, Boolean, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum
try:
    from .timezone_utils import central_now
except ImportError:
    from timezone_utils import central_now

Base = declarative_base()

class UserRole(enum.Enum):
    BASIC = "basic"
    ADMIN = "admin"
    TECHNICIAN = "technician"

class AccessLevel(enum.Enum):
    STUDENT = "student"
    STAFF = "staff" 
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
class CheckoutType(enum.Enum):
    LOCATION = "location"
    USER = "user"

user_buildings = Table(
    "user_buildings", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("building_id", Integer, ForeignKey("buildings.id"))
)

user_rooms = Table(
    "user_rooms", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("room_id", Integer, ForeignKey("rooms.id"))
)

class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)
    rooms = relationship("Room", back_populates="building")
    users = relationship("User", secondary=user_buildings, back_populates="buildings")

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'))
    building = relationship("Building", back_populates="rooms")
    users = relationship("User", secondary=user_rooms, back_populates="rooms")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String)
    roles = Column(String, default='basic')  # Comma-separated roles
    buildings = relationship("Building", secondary=user_buildings, back_populates="users")
    rooms = relationship("Room", secondary=user_rooms, back_populates="users")

class TechTicket(Base):
    __tablename__ = 'tech_tickets'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default='new')
    school = Column(String)
    room = Column(String)
    tag = Column(String)
    issue_type = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class MaintenanceTicket(Base):
    __tablename__ = 'maintenance_tickets'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default='new')
    school = Column(String)
    room = Column(String)
    tag = Column(String)
    issue_type = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class TicketUpdate(Base):
    __tablename__ = 'ticket_updates'
    id = Column(Integer, primary_key=True, index=True)
    ticket_type = Column(String, nullable=False)  # 'tech' or 'maintenance'
    ticket_id = Column(Integer, nullable=False)
    status_from = Column(String)  # Previous status
    status_to = Column(String)    # New status
    update_message = Column(String)  # Update description
    updated_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=central_now)

class SystemMessage(Base):
    __tablename__ = 'system_messages'
    id = Column(Integer, primary_key=True, index=True)
    message_type = Column(String, nullable=False)  # 'homepage', 'announcement', etc.
    content = Column(String, nullable=False)
    created_by = Column(String, default='System Admin')
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class Requisition(Base):
    __tablename__ = 'requisitions'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    department = Column(String)
    requested_by = Column(String, nullable=False)
    status = Column(String, default='pending')  # pending, approved, rejected, ordered
    estimated_cost = Column(String)  # Store as string to avoid decimal issues
    justification = Column(String)
    priority = Column(String, default='normal')  # low, normal, high, urgent
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True, nullable=False)
    requisition_id = Column(Integer, ForeignKey('requisitions.id'), nullable=True)
    vendor_name = Column(String, nullable=False)
    vendor_contact = Column(String)
    total_amount = Column(String)  # Store as string to avoid decimal issues
    status = Column(String, default='draft')  # draft, sent, received, completed, cancelled
    description = Column(String)
    delivery_address = Column(String)
    created_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    sent_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    id = Column(Integer, primary_key=True, index=True)
    tag_number = Column(String, unique=True, nullable=False)
    item_type = Column(String, nullable=False)  # Computer, Printer, Projector, etc.
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    serial_number = Column(String, unique=True, nullable=False)
    purchase_order = Column(String)
    price = Column(String)
    purchase_date = Column(DateTime)
    vendor = Column(String)
    funds = Column(String)
    description = Column(Text)
    condition = Column(String, default='excellent')  # excellent, good, fair, poor
    status = Column(String, default='available')  # available, checked_out, retired, maintenance
    # Default location (when not checked out)
    default_building_id = Column(Integer, ForeignKey('buildings.id'))
    default_room_id = Column(Integer, ForeignKey('rooms.id'))
    default_building = relationship("Building", foreign_keys=[default_building_id])
    default_room = relationship("Room", foreign_keys=[default_room_id])
    # Relationships
    checkouts = relationship("InventoryCheckout", back_populates="item")
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class InventoryCheckout(Base):
    __tablename__ = 'inventory_checkouts'
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)
    checkout_type = Column(String, nullable=False)  # 'location' or 'user'
    
    # Location-based checkout fields
    location_building_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    location_room_id = Column(Integer, ForeignKey('rooms.id'), nullable=True)
    
    # User-based checkout fields  
    user_building_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Common fields
    checked_out_by = Column(String, nullable=False)  # Who performed the checkout
    checked_out_at = Column(DateTime, default=central_now, nullable=False)
    expected_return_date = Column(DateTime, nullable=True)
    notes = Column(Text)
    
    # Return fields
    returned_at = Column(DateTime, nullable=True)
    returned_by = Column(String, nullable=True)
    return_condition = Column(String, nullable=True)
    return_notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    item = relationship("InventoryItem", back_populates="checkouts")
    location_building = relationship("Building", foreign_keys=[location_building_id])
    location_room = relationship("Room", foreign_keys=[location_room_id])
    user_building = relationship("Building", foreign_keys=[user_building_id])
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

# Authentication and Authorization Tables
class GroupRole(Base):
    __tablename__ = 'group_roles'
    id = Column(Integer, primary_key=True, index=True)
    azure_group_id = Column(String, unique=True, nullable=True)  # Azure AD Group Object ID
    azure_user_attribute = Column(String, nullable=True)  # For extensionAttribute mappings
    azure_user_attribute_value = Column(String, nullable=True)  # Value to match
    group_name = Column(String, nullable=False)  # Display Name
    access_level = Column(String, nullable=False)  # student, staff, admin, super_admin
    
    # Service-specific permissions
    tickets_access = Column(String, default='none')  # none, read, write, admin
    inventory_access = Column(String, default='none')
    purchasing_access = Column(String, default='none')
    forms_access = Column(String, default='none')
    
    allowed_departments = Column(JSON, nullable=True)  # JSON array of department names
    created_at = Column(DateTime, default=central_now)
    updated_at = Column(DateTime, default=central_now, onupdate=central_now)

class UserSession(Base):
    __tablename__ = 'user_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Azure AD User ID
    email = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    access_level = Column(String, nullable=False)
    azure_groups = Column(JSON, nullable=True)  # JSON array of Azure AD groups
    effective_permissions = Column(JSON, nullable=True)  # JSON object with computed permissions
    session_token = Column(String, nullable=False, index=True)  # JWT token
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=central_now)
    last_activity = Column(DateTime, default=central_now, onupdate=central_now)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Azure AD User ID
    action_type = Column(String, nullable=False)  # create, read, update, delete, login, logout
    resource_type = Column(String, nullable=False)  # ticket, inventory, user, etc.
    resource_id = Column(String, nullable=True)  # ID of the affected resource
    details = Column(JSON, nullable=True)  # JSON object with action details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=central_now, nullable=False)
