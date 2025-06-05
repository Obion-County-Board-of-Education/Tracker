from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    BASIC = "basic"
    ADMIN = "admin"
    TECHNICIAN = "technician"

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemMessage(Base):
    __tablename__ = 'system_messages'
    id = Column(Integer, primary_key=True, index=True)
    message_type = Column(String, nullable=False)  # 'homepage', 'announcement', etc.
    content = Column(String, nullable=False)
    created_by = Column(String, default='System Admin')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
