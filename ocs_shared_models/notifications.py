"""
Real-time notifications system for OCS services
Provides role-based notifications using WebSockets
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Types of notifications that can be sent"""
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_ASSIGNED = "ticket_assigned"
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"
    APPROVAL_REQUEST = "approval_request"
    MAINTENANCE_ALERT = "maintenance_alert"
    INVENTORY_UPDATE = "inventory_update"
    PURCHASING_UPDATE = "purchasing_update"

class NotificationLevel(str, Enum):
    """Notification priority levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class Notification(BaseModel):
    """Notification data model"""
    id: str
    type: NotificationType
    level: NotificationLevel
    title: str
    message: str
    target_roles: List[str] = []
    target_users: List[str] = []
    data: Dict = {}
    timestamp: datetime
    read: bool = False
    expires_at: Optional[datetime] = None

class WebSocketConnection:
    """Represents a WebSocket connection with user context"""
    def __init__(self, websocket: WebSocket, user_id: str, user_roles: List[str]):
        self.websocket = websocket
        self.user_id = user_id
        self.user_roles = user_roles
        self.connected_at = datetime.now()

class NotificationManager:
    """Manages real-time notifications via WebSocket connections"""
    
    def __init__(self):
        # Active WebSocket connections: {user_id: WebSocketConnection}
        self.connections: Dict[str, WebSocketConnection] = {}
        # Recent notifications for users who aren't connected
        self.pending_notifications: Dict[str, List[Notification]] = {}
        # Maximum pending notifications per user
        self.max_pending = 50
        
    async def connect(self, websocket: WebSocket, user_id: str, user_roles: List[str]):
        """Add a new WebSocket connection"""
        await websocket.accept()
        connection = WebSocketConnection(websocket, user_id, user_roles)
        self.connections[user_id] = connection
        
        # Send any pending notifications to the newly connected user
        if user_id in self.pending_notifications:
            for notification in self.pending_notifications[user_id]:
                await self._send_to_connection(connection, notification)
            # Clear pending notifications after sending
            del self.pending_notifications[user_id]
            
        logger.info(f"User {user_id} connected to notifications")
        
    async def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.connections:
            del self.connections[user_id]
            logger.info(f"User {user_id} disconnected from notifications")
            
    async def send_notification(self, notification: Notification):
        """Send a notification to appropriate users"""
        target_user_ids = set()
        
        # Add users by ID
        target_user_ids.update(notification.target_users)
        
        # Add users by role
        for user_id, connection in self.connections.items():
            user_roles = set(connection.user_roles)
            target_roles = set(notification.target_roles)
            if user_roles.intersection(target_roles):
                target_user_ids.add(user_id)
        
        # Send to connected users
        disconnected_users = []
        for user_id in target_user_ids:
            if user_id in self.connections:
                try:
                    await self._send_to_connection(self.connections[user_id], notification)
                except WebSocketDisconnect:
                    disconnected_users.append(user_id)
            else:
                # Store for when user connects
                self._store_pending_notification(user_id, notification)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)
            
    async def _send_to_connection(self, connection: WebSocketConnection, notification: Notification):
        """Send notification to a specific connection"""
        try:
            message = {
                "id": notification.id,
                "type": notification.type,
                "level": notification.level,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "timestamp": notification.timestamp.isoformat(),
                "read": notification.read
            }
            await connection.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending notification to user {connection.user_id}: {e}")
            raise WebSocketDisconnect()
            
    def _store_pending_notification(self, user_id: str, notification: Notification):
        """Store notification for offline user"""
        if user_id not in self.pending_notifications:
            self.pending_notifications[user_id] = []
            
        self.pending_notifications[user_id].append(notification)
        
        # Limit pending notifications
        if len(self.pending_notifications[user_id]) > self.max_pending:
            self.pending_notifications[user_id] = self.pending_notifications[user_id][-self.max_pending:]
            
    async def broadcast_to_role(self, roles: List[str], notification: Notification):
        """Broadcast notification to all users with specific roles"""
        notification.target_roles = roles
        await self.send_notification(notification)
        
    async def send_to_user(self, user_id: str, notification: Notification):
        """Send notification to a specific user"""
        notification.target_users = [user_id]
        await self.send_notification(notification)
        
    async def send_system_alert(self, message: str, level: NotificationLevel = NotificationLevel.INFO, target_roles: List[str] = None):
        """Send a system-wide alert"""
        if target_roles is None:
            target_roles = ["admin", "super_admin"]
            
        notification = Notification(
            id=f"system_{datetime.now().timestamp()}",
            type=NotificationType.SYSTEM_ALERT,
            level=level,
            title="System Alert",
            message=message,
            target_roles=target_roles,
            timestamp=datetime.now()
        )
        await self.send_notification(notification)

# Global notification manager instance
notification_manager = NotificationManager()

# Convenience functions for common notifications
async def notify_ticket_created(ticket_id: int, ticket_type: str, requester: str, priority: str = "normal"):
    """Notify relevant users about a new ticket"""
    target_roles = ["admin", "technician"]
    if priority in ["high", "urgent"]:
        target_roles.append("super_admin")
        
    notification = Notification(
        id=f"ticket_created_{ticket_id}_{datetime.now().timestamp()}",
        type=NotificationType.TICKET_CREATED,
        level=NotificationLevel.INFO if priority == "normal" else NotificationLevel.WARNING,
        title=f"New {ticket_type.title()} Ticket",
        message=f"New {priority} priority ticket created by {requester}",
        target_roles=target_roles,
        data={"ticket_id": ticket_id, "ticket_type": ticket_type, "priority": priority},
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_ticket_updated(ticket_id: int, ticket_type: str, updated_by: str, status: str):
    """Notify relevant users about ticket updates"""
    notification = Notification(
        id=f"ticket_updated_{ticket_id}_{datetime.now().timestamp()}",
        type=NotificationType.TICKET_UPDATED,
        level=NotificationLevel.SUCCESS if status == "closed" else NotificationLevel.INFO,
        title=f"{ticket_type.title()} Ticket Updated",
        message=f"Ticket #{ticket_id} status changed to {status} by {updated_by}",
        target_roles=["admin", "technician"],
        data={"ticket_id": ticket_id, "ticket_type": ticket_type, "status": status},
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_approval_request(request_type: str, request_id: int, requester: str, amount: float = None):
    """Notify admins about approval requests"""
    message = f"New {request_type} approval request from {requester}"
    if amount:
        message += f" (${amount:,.2f})"
        
    notification = Notification(
        id=f"approval_{request_type}_{request_id}_{datetime.now().timestamp()}",
        type=NotificationType.APPROVAL_REQUEST,
        level=NotificationLevel.WARNING,
        title="Approval Required",
        message=message,
        target_roles=["admin", "super_admin"],
        data={"request_type": request_type, "request_id": request_id, "amount": amount},
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_system_maintenance(message: str, affected_services: List[str] = None):
    """Notify users about system maintenance"""
    notification = Notification(
        id=f"maintenance_{datetime.now().timestamp()}",
        type=NotificationType.MAINTENANCE_ALERT,
        level=NotificationLevel.WARNING,
        title="System Maintenance",
        message=message,
        target_roles=["admin", "super_admin", "technician"],
        data={"affected_services": affected_services or []},
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_inventory_update(item_name: str, action: str, updated_by: str, location: str = None):
    """Notify relevant users about inventory changes"""
    message = f"Inventory item '{item_name}' was {action}"
    if location:
        message += f" at {location}"
    message += f" by {updated_by}"
        
    notification = Notification(
        id=f"inventory_{action}_{datetime.now().timestamp()}",
        type=NotificationType.INVENTORY_UPDATE,
        level=NotificationLevel.INFO,
        title="Inventory Update",
        message=message,
        target_roles=["admin", "technician"],
        data={"item_name": item_name, "action": action, "location": location},
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_requisition_created(requisition_id: int, requester: str, department: str, amount: str = None):
    """Send notification when a new requisition is created"""
    notification = Notification(
        id=f"req_created_{requisition_id}_{datetime.now().timestamp()}",
        type=NotificationType.PURCHASING_UPDATE,
        level=NotificationLevel.INFO,
        title="New Requisition Created",
        message=f"New requisition created by {requester} for {department}",
        target_roles=["purchasing_admin", "admin", "super_admin"],
        data={
            "requisition_id": requisition_id,
            "requester": requester,
            "department": department,
            "amount": amount,
            "action": "created"
        },
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_requisition_approved(requisition_id: int, approved_by: str, department: str):
    """Send notification when a requisition is approved"""
    notification = Notification(
        id=f"req_approved_{requisition_id}_{datetime.now().timestamp()}",
        type=NotificationType.PURCHASING_UPDATE,
        level=NotificationLevel.SUCCESS,
        title="Requisition Approved",
        message=f"Requisition for {department} approved by {approved_by}",
        target_roles=["purchasing_admin", "admin", "super_admin"],
        data={
            "requisition_id": requisition_id,
            "approved_by": approved_by,
            "department": department,
            "action": "approved"
        },
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

async def notify_po_created(po_id: int, po_number: str, vendor: str, created_by: str, amount: str = None):
    """Send notification when a new purchase order is created"""
    notification = Notification(
        id=f"po_created_{po_id}_{datetime.now().timestamp()}",
        type=NotificationType.PURCHASING_UPDATE,
        level=NotificationLevel.INFO,
        title="New Purchase Order Created",
        message=f"Purchase Order {po_number} created for {vendor}",
        target_roles=["purchasing_admin", "admin", "super_admin"],
        data={
            "po_id": po_id,
            "po_number": po_number,
            "vendor": vendor,
            "created_by": created_by,
            "amount": amount,
            "action": "created"
        },
        timestamp=datetime.now()
    )
    await notification_manager.send_notification(notification)

def notify_requisition_created_sync(requisition_id: int, requester: str, department: str, amount: str = None):
    """Sync wrapper for requisition creation notification"""
    try:
        asyncio.create_task(notify_requisition_created(requisition_id, requester, department, amount))
    except Exception as e:
        logger.error(f"Failed to send requisition created notification: {e}")

def notify_requisition_approved_sync(requisition_id: int, approved_by: str, department: str):
    """Sync wrapper for requisition approval notification"""
    try:
        asyncio.create_task(notify_requisition_approved(requisition_id, approved_by, department))
    except Exception as e:
        logger.error(f"Failed to send requisition approved notification: {e}")

def notify_po_created_sync(po_id: int, po_number: str, vendor: str, created_by: str, amount: str = None):
    """Sync wrapper for purchase order creation notification"""
    try:
        asyncio.create_task(notify_po_created(po_id, po_number, vendor, created_by, amount))
    except Exception as e:
        logger.error(f"Failed to send purchase order created notification: {e}")
