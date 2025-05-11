/**
 * Enhanced WebSocket Client
 * 
 * This module provides a robust WebSocket client for connecting to the Coordinator
 * WebSocket API. It handles connection lifecycle, authentication, reconnection,
 * and event subscription.
 */

class EnhancedWebSocketClient {
    /**
     * Create a new WebSocket client.
     * 
     * @param {string} baseUrl - Base URL for WebSocket connections
     * @param {string} sessionId - Session ID
     * @param {Object} options - Configuration options
     * @param {string} options.clientId - Optional client ID
     * @param {string} options.token - Optional authentication token
     * @param {string[]} options.subscriptions - Optional array of event types to subscribe to
     * @param {number} options.reconnectDelay - Delay between reconnection attempts in ms (default: 2000)
     * @param {number} options.maxReconnectAttempts - Maximum number of reconnection attempts (default: 5)
     * @param {boolean} options.debug - Enable debug logging (default: false)
     */
    constructor(baseUrl, sessionId, options = {}) {
        this.baseUrl = baseUrl;
        this.sessionId = sessionId;
        this.clientId = options.clientId;
        this.token = options.token;
        this.subscriptions = options.subscriptions || [];
        this.reconnectDelay = options.reconnectDelay || 2000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.debug = options.debug || false;
        
        // State
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.pingInterval = null;
        
        // Event handlers
        this.eventHandlers = {};
        
        // Connection URL
        this.url = `${baseUrl}/session/${sessionId}`;
        if (this.clientId) {
            this.url += `?client_id=${this.clientId}`;
        }
        if (this.token) {
            this.url += `${this.clientId ? '&' : '?'}token=${this.token}`;
        }
    }
    
    /**
     * Connect to the WebSocket.
     * 
     * @returns {Promise<boolean>} True if connection succeeded, false otherwise
     */
    connect() {
        return new Promise((resolve, reject) => {
            // Close existing connection if any
            if (this.socket) {
                this.disconnect();
            }
            
            // Create new WebSocket
            this.socket = new WebSocket(this.url);
            
            // Set up event handlers
            this.socket.onopen = () => {
                this.log('WebSocket connection established');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // Start ping interval
                this.startPingInterval();
                
                // Subscribe to events if any
                if (this.subscriptions.length > 0) {
                    this.subscribe(this.subscriptions);
                }
                
                resolve(true);
            };
            
            this.socket.onclose = (event) => {
                this.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
                this.isConnected = false;
                
                // Stop ping interval
                this.stopPingInterval();
                
                // Trigger onDisconnect event
                this.triggerEvent('disconnect', { code: event.code, reason: event.reason });
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectTimer = setTimeout(() => {
                        this.reconnectAttempts++;
                        this.log(`Reconnecting attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                        this.connect().catch(() => {
                            // Reject only on the last attempt
                            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                                reject(new Error(`Failed to reconnect after ${this.maxReconnectAttempts} attempts`));
                            }
                        });
                    }, this.reconnectDelay);
                } else {
                    reject(new Error(`Failed to reconnect after ${this.maxReconnectAttempts} attempts`));
                }
            };
            
            this.socket.onerror = (error) => {
                this.log(`WebSocket error: ${error}`);
                this.triggerEvent('error', { error });
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    this.log(`Error parsing message: ${error}`);
                }
            };
        });
    }
    
    /**
     * Disconnect from the WebSocket.
     */
    disconnect() {
        if (this.socket) {
            // Clear timers
            this.stopPingInterval();
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
            
            // Close socket
            if (this.isConnected) {
                this.socket.close();
            }
            
            this.socket = null;
            this.isConnected = false;
        }
    }
    
    /**
     * Start the ping interval to keep the connection alive.
     */
    startPingInterval() {
        this.pingInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
            }
        }, 30000); // 30 seconds
    }
    
    /**
     * Stop the ping interval.
     */
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    /**
     * Handle incoming messages.
     * 
     * @param {Object} message - Message object
     */
    handleMessage(message) {
        const messageType = message.type;
        
        // Handle system messages
        if (messageType === 'pong') {
            this.log('Received pong');
            return;
        }
        
        if (messageType === 'error') {
            this.log(`Received error: ${message.error}`);
            this.triggerEvent('error', message);
            return;
        }
        
        if (messageType === 'connection_established') {
            this.clientId = message.client_id;
            this.triggerEvent('connect', message);
            return;
        }
        
        // Handle event messages
        this.triggerEvent(messageType, message);
        this.triggerEvent('message', message);
    }
    
    /**
     * Send a message to the WebSocket server.
     * 
     * @param {Object} message - Message to send
     * @returns {boolean} True if message was sent, false otherwise
     */
    send(message) {
        if (!this.isConnected) {
            this.log('Cannot send message: Not connected');
            return false;
        }
        
        try {
            this.socket.send(JSON.stringify(message));
            return true;
        } catch (error) {
            this.log(`Error sending message: ${error}`);
            return false;
        }
    }
    
    /**
     * Subscribe to event types.
     * 
     * @param {string[]} eventTypes - Array of event types to subscribe to
     */
    subscribe(eventTypes) {
        if (!Array.isArray(eventTypes) || eventTypes.length === 0) {
            return;
        }
        
        // Update subscriptions
        this.subscriptions = [...new Set([...this.subscriptions, ...eventTypes])];
        
        // Send subscription message
        if (this.isConnected) {
            this.send({
                type: 'subscribe',
                event_types: eventTypes
            });
        }
    }
    
    /**
     * Unsubscribe from event types.
     * 
     * @param {string[]} eventTypes - Array of event types to unsubscribe from
     */
    unsubscribe(eventTypes) {
        if (!Array.isArray(eventTypes) || eventTypes.length === 0) {
            return;
        }
        
        // Update subscriptions
        this.subscriptions = this.subscriptions.filter(type => !eventTypes.includes(type));
        
        // Send unsubscription message
        if (this.isConnected) {
            this.send({
                type: 'unsubscribe',
                event_types: eventTypes
            });
        }
    }
    
    /**
     * Register an event handler.
     * 
     * @param {string} eventType - Event type to listen for
     * @param {Function} handler - Handler function
     */
    on(eventType, handler) {
        if (!this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = [];
        }
        
        this.eventHandlers[eventType].push(handler);
    }
    
    /**
     * Unregister an event handler.
     * 
     * @param {string} eventType - Event type
     * @param {Function} handler - Handler function to remove (optional, removes all if not provided)
     */
    off(eventType, handler) {
        if (!this.eventHandlers[eventType]) {
            return;
        }
        
        if (handler) {
            this.eventHandlers[eventType] = this.eventHandlers[eventType].filter(h => h !== handler);
        } else {
            this.eventHandlers[eventType] = [];
        }
    }
    
    /**
     * Trigger an event.
     * 
     * @param {string} eventType - Event type
     * @param {Object} data - Event data
     */
    triggerEvent(eventType, data) {
        if (!this.eventHandlers[eventType]) {
            return;
        }
        
        for (const handler of this.eventHandlers[eventType]) {
            try {
                handler(data);
            } catch (error) {
                this.log(`Error in event handler for ${eventType}: ${error}`);
            }
        }
    }
    
    /**
     * Log a message if debug is enabled.
     * 
     * @param {string} message - Message to log
     */
    log(message) {
        if (this.debug) {
            console.log(`[WebSocketClient] ${message}`);
        }
    }
}

/**
 * WebSocket visualization client.
 * 
 * This specialized client is optimized for visualization use cases and
 * auto-subscribes to visualization-relevant events.
 */
class VisualizationWebSocketClient extends EnhancedWebSocketClient {
    /**
     * Create a new visualization WebSocket client.
     * 
     * @param {string} baseUrl - Base URL for WebSocket connections
     * @param {string} sessionId - Session ID
     * @param {Object} options - Configuration options
     */
    constructor(baseUrl, sessionId, options = {}) {
        // Add visualization-specific subscriptions
        const vizSubscriptions = [
            'task_update',
            'task_created',
            'task_started',
            'task_completed',
            'task_failed',
            'agent_status',
            'session_status'
        ];
        
        options.subscriptions = [...new Set([
            ...(options.subscriptions || []),
            ...vizSubscriptions
        ])];
        
        super(baseUrl, sessionId, options);
        
        // Use visualization-specific endpoint
        this.url = `${baseUrl}/visualization/${sessionId}`;
        if (this.clientId) {
            this.url += `?client_id=${this.clientId}`;
        }
        if (this.token) {
            this.url += `${this.clientId ? '&' : '?'}token=${this.token}`;
        }
    }
}

/**
 * WebSocket agent client.
 * 
 * This specialized client is for monitoring a specific agent.
 */
class AgentWebSocketClient extends EnhancedWebSocketClient {
    /**
     * Create a new agent WebSocket client.
     * 
     * @param {string} baseUrl - Base URL for WebSocket connections
     * @param {string} sessionId - Session ID
     * @param {string} agentId - Agent ID
     * @param {Object} options - Configuration options
     */
    constructor(baseUrl, sessionId, agentId, options = {}) {
        // Add agent-specific subscriptions
        const agentSubscriptions = [
            'agent_thinking',
            'agent_typing',
            'agent_status',
            'tool_execution'
        ];
        
        options.subscriptions = [...new Set([
            ...(options.subscriptions || []),
            ...agentSubscriptions
        ])];
        
        super(baseUrl, sessionId, options);
        
        this.agentId = agentId;
        
        // Use agent-specific endpoint
        this.url = `${baseUrl}/agent/${sessionId}/${agentId}`;
        if (this.clientId) {
            this.url += `?client_id=${this.clientId}`;
        }
        if (this.token) {
            this.url += `${this.clientId ? '&' : '?'}token=${this.token}`;
        }
    }
}
