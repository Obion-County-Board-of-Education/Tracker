"""
WebSocket endpoints for real-time notifications
"""
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect, Depends, Request
from typing import List
from auth_middleware import get_current_user
from ocs_shared_models.notifications import notification_manager

logger = logging.getLogger(__name__)

def setup_notification_routes(app):
    """Setup WebSocket routes for notifications"""
    
    @app.websocket("/ws/notifications")
    async def websocket_notifications(websocket: WebSocket):
        """WebSocket endpoint for real-time notifications"""
        try:
            # Accept the connection first
            await websocket.accept()
            
            # Wait for authentication message
            auth_data = await websocket.receive_text()
            auth_info = json.loads(auth_data)
            
            # Extract user info from token or session
            user_id = auth_info.get('user_id')
            user_roles = auth_info.get('user_roles', [])
            
            if not user_id:
                await websocket.send_text(json.dumps({
                    "error": "Authentication required",
                    "type": "auth_error"
                }))
                await websocket.close()
                return
            
            # Register the connection
            await notification_manager.connect(websocket, user_id, user_roles)
            
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connected",
                "message": "Notifications connected",
                "user_id": user_id
            }))
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for messages (heartbeat, etc.)
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    # Handle heartbeat
                    if data.get('type') == 'heartbeat':
                        await websocket.send_text(json.dumps({
                            "type": "heartbeat_response",
                            "timestamp": data.get('timestamp')
                        }))
                    
                    # Handle mark as read
                    elif data.get('type') == 'mark_read':
                        notification_id = data.get('notification_id')
                        # TODO: Mark notification as read in database
                        logger.info(f"User {user_id} marked notification {notification_id} as read")
                        
                except WebSocketDisconnect:
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up connection
            if 'user_id' in locals():
                await notification_manager.disconnect(user_id)
            
    @app.post("/api/notifications/test")
    async def test_notification(request: Request):
        """Test endpoint to send a notification"""
        from ocs_shared_models.notifications import notify_system_maintenance
        
        try:
            current_user = get_current_user(request)
            if not current_user.get('roles') or 'admin' not in current_user.get('roles', []):
                return {"error": "Admin access required"}
                
            await notify_system_maintenance(
                "This is a test notification from the portal.",
                ["portal"]
            )
            
            return {"success": True, "message": "Test notification sent"}
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return {"error": str(e)}
            
    @app.get("/api/notifications/status")
    async def notification_status():
        """Get notification system status"""
        return {
            "connected_users": len(notification_manager.connections),
            "pending_notifications": sum(len(notifications) for notifications in notification_manager.pending_notifications.values()),
            "status": "active"
        }
        
    print("✅ Notification WebSocket routes registered")
