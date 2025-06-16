/**
 * Real-time notifications client for OCS Portal
 * Manages WebSocket connection and displays notifications
 */

class NotificationClient {
    constructor(options = {}) {
        this.wsUrl = options.wsUrl || this.getWebSocketURL();
        this.userId = options.userId || null;
        this.userRoles = options.userRoles || [];
        this.token = options.token || null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = 30000;
        this.ws = null;
        this.heartbeatTimer = null;
        this.notifications = [];
        this.onNotification = options.onNotification || this.defaultNotificationHandler.bind(this);
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        this.onError = options.onError || console.error;
    }

    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/notifications`;
    }

    async connect(userId, userRoles = [], token = null) {
        this.userId = userId;
        this.userRoles = userRoles;
        this.token = token;

        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('🔔 Notifications WebSocket connected');
                this.reconnectAttempts = 0;
                
                // Send authentication
                this.ws.send(JSON.stringify({
                    user_id: this.userId,
                    user_roles: this.userRoles,
                    token: this.token
                }));
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing notification message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('🔔 Notifications WebSocket disconnected');
                this.stopHeartbeat();
                this.onDisconnect();
                this.scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.onError(error);
            };

        } catch (error) {
            console.error('Failed to connect to notifications:', error);
            this.onError(error);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'connected':
                console.log('🔔 Notifications connected for user:', data.user_id);
                this.startHeartbeat();
                this.onConnect();
                break;
                
            case 'heartbeat_response':
                // Heartbeat acknowledged
                break;
                
            case 'auth_error':
                console.error('Notification authentication error:', data.error);
                this.onError(new Error(data.error));
                break;
                
            default:
                // Regular notification
                this.handleNotification(data);
                break;
        }
    }

    handleNotification(notification) {
        // Add to notifications list
        this.notifications.unshift(notification);
        
        // Limit stored notifications
        if (this.notifications.length > 100) {
            this.notifications = this.notifications.slice(0, 100);
        }
        
        // Call notification handler
        this.onNotification(notification);
        
        // Update notification badge
        this.updateNotificationBadge();
    }

    defaultNotificationHandler(notification) {
        // Create toast notification
        this.showToast(notification);
        
        // Update notification center
        this.addToNotificationCenter(notification);
        
        // Play sound for important notifications
        if (notification.level === 'warning' || notification.level === 'error') {
            this.playNotificationSound();
        }
        
        // Show browser notification if supported and permission granted
        this.showBrowserNotification(notification);
    }

    showToast(notification) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${notification.level}`;
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fa ${this.getNotificationIcon(notification.type)}"></i>
                <strong>${notification.title}</strong>
                <small>${this.formatTime(notification.timestamp)}</small>
                <button type="button" class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="toast-body">
                ${notification.message}
            </div>
        `;
        
        // Add to toast container
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    addToNotificationCenter(notification) {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification-item notification-${notification.level}`;
        notificationElement.dataset.notificationId = notification.id;
        notificationElement.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <i class="fa ${this.getNotificationIcon(notification.type)}"></i>
                    <span class="notification-title">${notification.title}</span>
                    <span class="notification-time">${this.formatTime(notification.timestamp)}</span>
                </div>
                <div class="notification-message">${notification.message}</div>
            </div>
            <button class="notification-dismiss" onclick="notificationClient.markAsRead('${notification.id}')">
                <i class="fa fa-times"></i>
            </button>
        `;
        
        notificationsList.insertBefore(notificationElement, notificationsList.firstChild);
    }

    showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/favicon.ico',
                tag: notification.id
            });
        }
    }

    getNotificationIcon(type) {
        const iconMap = {
            'ticket_created': 'fa-ticket',
            'ticket_updated': 'fa-edit',
            'system_alert': 'fa-exclamation-triangle',
            'approval_request': 'fa-check-circle',
            'maintenance_alert': 'fa-tools',
            'inventory_update': 'fa-boxes',
            'purchasing_update': 'fa-shopping-cart'
        };
        return iconMap[type] || 'fa-bell';
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    playNotificationSound() {
        // Create audio element and play notification sound
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(() => {
            // Ignore errors if sound can't play
        });
    }

    updateNotificationBadge() {
        const unreadCount = this.notifications.filter(n => !n.read).length;
        const badge = document.getElementById('notification-badge');
        
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount.toString();
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    markAsRead(notificationId) {
        // Mark notification as read
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.read = true;
        }
        
        // Remove from UI
        const element = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (element) {
            element.remove();
        }
        
        // Send to server
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'mark_read',
                notification_id: notificationId
            }));
        }
        
        this.updateNotificationBadge();
    }

    clearAllNotifications() {
        this.notifications.forEach(n => n.read = true);
        
        const notificationsList = document.getElementById('notifications-list');
        if (notificationsList) {
            notificationsList.innerHTML = '';
        }
        
        this.updateNotificationBadge();
    }

    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'heartbeat',
                    timestamp: Date.now()
                }));
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect(this.userId, this.userRoles, this.token);
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    // Request browser notification permission
    static async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return Notification.permission === 'granted';
    }
}

// Global instance
let notificationClient = null;

// Initialize notifications when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if user is logged in
    const userElement = document.querySelector('[data-user-id]');
    if (userElement) {
        const userId = userElement.dataset.userId;
        const userRoles = JSON.parse(userElement.dataset.userRoles || '[]');
        
        notificationClient = new NotificationClient({
            onConnect: () => {
                console.log('🔔 Notifications connected');
                // Show connection status
                const statusElement = document.getElementById('notification-status');
                if (statusElement) {
                    statusElement.className = 'notification-status connected';
                    statusElement.title = 'Notifications connected';
                }
            },
            onDisconnect: () => {
                console.log('🔔 Notifications disconnected');
                // Show disconnection status
                const statusElement = document.getElementById('notification-status');
                if (statusElement) {
                    statusElement.className = 'notification-status disconnected';
                    statusElement.title = 'Notifications disconnected';
                }
            }
        });
        
        notificationClient.connect(userId, userRoles);
        
        // Request notification permission
        NotificationClient.requestNotificationPermission();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (notificationClient) {
        notificationClient.disconnect();
    }
});
