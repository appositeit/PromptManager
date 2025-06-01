/**
 * WebSocket functionality for real-time session updates
 */

/**
 * Create a session WebSocket manager
 * @param {string} sessionId - The ID of the session
 * @returns {object} WebSocket manager for session
 */
function createSessionWebSocket(sessionId) {
    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/sessions/${sessionId}`;
    
    // Track message cache and connection state
    let messageCache = [];
    let lastMessageId = null;
    let connected = false;
    let connecting = false;
    let reconnectAttempts = 0;
    let pingInterval = null;
    
    // Create WebSocket object
    let socket = null;
    
    // Event callbacks
    const callbacks = {
        onOpen: [],
        onMessage: [],
        onClose: [],
        onError: [],
        onReconnect: [],
        onStatusChange: [],
        onTyping: [],
        onTasks: []
    };
    
    function connect() {
        if (connected || connecting) {return;}
        
        connecting = true;
        updateStatus('connecting');
        
        // Create WebSocket
        socket = new WebSocket(wsUrl);
        
        socket.onopen = event => {
            console.log('WebSocket connected');
            connected = true;
            connecting = false;
            reconnectAttempts = 0;
            updateStatus('connected');
            
            // Start ping interval to keep connection alive
            if (pingInterval) {clearInterval(pingInterval);}
            pingInterval = setInterval(sendPing, 30000);
            
            // Get initial messages
            requestMessages();
            
            // Trigger callbacks
            triggerCallbacks('onOpen', event);
        };
        
        socket.onmessage = event => {
            // Parse message data
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
                
                // Trigger callbacks
                triggerCallbacks('onMessage', data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        socket.onclose = event => {
            console.log('WebSocket closed:', event.code, event.reason);
            connected = false;
            connecting = false;
            updateStatus('disconnected');
            
            // Clear ping interval
            if (pingInterval) {
                clearInterval(pingInterval);
                pingInterval = null;
            }
            
            // Attempt to reconnect if not a clean close
            if (!event.wasClean && reconnectAttempts < 5) {
                const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), 10000);
                reconnectAttempts++;
                updateStatus('reconnecting', { attempts: reconnectAttempts });
                
                // Trigger reconnect callbacks
                triggerCallbacks('onReconnect', { attempts: reconnectAttempts, delay });
                
                console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})...`);
                setTimeout(connect, delay);
            }
            
            // Trigger callbacks
            triggerCallbacks('onClose', event);
        };
        
        socket.onerror = event => {
            console.error('WebSocket error:', event);
            
            // Trigger callbacks
            triggerCallbacks('onError', event);
        };
    }
    
    function disconnect() {
        if (!connected && !connecting) {return;}
        
        if (socket) {
            socket.close();
        }
        
        connected = false;
        connecting = false;
        
        // Clear ping interval
        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }
        
        updateStatus('disconnected');
    }
    
    function sendPing() {
        if (!connected) {return;}
        
        try {
            socket.send(JSON.stringify({ type: 'ping' }));
        } catch (error) {
            console.error('Error sending ping:', error);
        }
    }
    
    function requestMessages() {
        if (!connected) {return;}
        
        try {
            socket.send(JSON.stringify({ 
                type: 'get_messages',
                last_message_id: lastMessageId
            }));
        } catch (error) {
            console.error('Error requesting messages:', error);
        }
    }
    
    function handleMessage(data) {
        // Handle different message types
        switch (data.type) {
            case 'messages':
                handleMessages(data.data);
                break;
                
            case 'pong':
                // Server responded to ping, connection is alive
                break;
                
            case 'status':
                updateStatus(data.status, data.data);
                break;
                
            case 'typing':
                handleTypingIndicator(data.agent_id, data.is_typing);
                break;
                
            case 'tasks':
                handleTasksUpdate(data.data);
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    function handleTasksUpdate(tasks) {
        // Trigger tasks update callbacks
        triggerCallbacks('onTasks', { tasks });
    }
    
    function handleTypingIndicator(agentId, isTyping) {
        // Trigger typing indicator callbacks
        triggerCallbacks('onTyping', { agentId, isTyping });
    }
    
    function handleMessages(messages) {
        if (!Array.isArray(messages) || messages.length === 0) {return;}
        
        // Update last message ID
        lastMessageId = messages[messages.length - 1].id;
        
        // Add messages to cache
        messageCache = [...messageCache, ...messages];
        
        // Sort by timestamp
        messageCache.sort((a, b) => {
            return new Date(a.timestamp) - new Date(b.timestamp);
        });
    }
    
    function updateStatus(status, data = {}) {
        // Trigger status change callbacks
        triggerCallbacks('onStatusChange', { status, data });
    }
    
    function triggerCallbacks(type, data) {
        if (callbacks[type]) {
            callbacks[type].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${type} callback:`, error);
                }
            });
        }
    }
    
    function on(event, callback) {
        if (callbacks[event]) {
            callbacks[event].push(callback);
        }
        return this; // Allow chaining
    }
    
    function off(event, callback) {
        if (callbacks[event]) {
            callbacks[event] = callbacks[event].filter(cb => cb !== callback);
        }
        return this; // Allow chaining
    }
    
    // Return public API
    return {
        connect,
        disconnect,
        send: (data) => {
            if (!connected) {return false;}
            
            try {
                if (typeof data === 'object') {
                    socket.send(JSON.stringify(data));
                } else {
                    socket.send(data);
                }
                return true;
            } catch (error) {
                console.error('Error sending message:', error);
                return false;
            }
        },
        isConnected: () => connected,
        getMessages: () => [...messageCache],
        getStatus: () => ({ connected, connecting, reconnectAttempts }),
        on,
        off
    };
}

/**
 * Initialize the session interface and connect to WebSocket
 * @param {string} sessionId - The ID of the session
 */
function initSessionInterface(sessionId) {
    const messagesContainer = document.getElementById('messages');
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const conversationArea = document.getElementById('conversationArea');
    const sessionStatusElement = document.getElementById('session-status');
    const tasksContainer = document.getElementById('tasks-container');
    const noTasksMessage = document.getElementById('no-tasks-message');
    
    let isAtBottom = true;
    let lastMessageId = null;
    const typingIndicators = {};
    let currentTasks = {};
    
    // Create WebSocket connection
    const ws = createSessionWebSocket(sessionId);
    
    // Create or get typing indicator element
    function getTypingIndicatorElement(agentId) {
        const id = `typing-${agentId}`;
        let element = document.getElementById(id);
        
        if (!element) {
            element = document.createElement('div');
            element.id = id;
            element.className = 'typing-indicator message';
            element.classList.add(`message-${agentId}`);
            
            // Add typing animation
            element.innerHTML = `
                <div class="message-header">
                    <span class="message-sender">${formatAgentName(agentId)}</span>
                </div>
                <div class="message-content">
                    <div class="typing-dots">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
            `;
            
            // Hide initially
            element.style.display = 'none';
            
            // Add to messages container
            messagesContainer.appendChild(element);
        }
        
        return element;
    }
    
    // Set up event handlers
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });
    }
    
    // Detect if the user has scrolled away from the bottom
    if (conversationArea) {
        conversationArea.addEventListener('scroll', function() {
            isAtBottom = (conversationArea.scrollHeight - conversationArea.scrollTop - conversationArea.clientHeight < 10);
        });
    }
    
    // Register WebSocket event handlers
    ws.on('onOpen', function() {
        // Enable message input
        if (messageInput) {messageInput.disabled = false;}
        if (sendButton) {sendButton.disabled = false;}
        
        // Update UI status
        if (sessionStatusElement) {
            sessionStatusElement.textContent = 'Connected';
            sessionStatusElement.className = 'badge bg-success';
        }
    });
    
    ws.on('onClose', function() {
        // Disable message input
        if (messageInput) {messageInput.disabled = true;}
        if (sendButton) {sendButton.disabled = true;}
        
        // Update UI status
        if (sessionStatusElement) {
            sessionStatusElement.textContent = 'Disconnected';
            sessionStatusElement.className = 'badge bg-danger';
        }
    });
    
    ws.on('onReconnect', function({ attempts }) {
        // Update UI status
        if (sessionStatusElement) {
            sessionStatusElement.textContent = `Reconnecting (${attempts})`;
            sessionStatusElement.className = 'badge bg-warning';
        }
    });
    
    ws.on('onMessage', function(data) {
        if (data.type === 'messages') {
            renderMessages(data.data);
        }
    });
    
    ws.on('onTyping', function({ agentId, isTyping }) {
        const typingElement = getTypingIndicatorElement(agentId);
        
        if (isTyping) {
            // Show typing indicator
            typingElement.style.display = 'block';
            
            // Store typing state
            typingIndicators[agentId] = true;
            
            // Scroll to bottom if was at bottom
            if (isAtBottom && conversationArea) {
                scrollToBottom(conversationArea);
            }
        } else {
            // Hide typing indicator
            typingElement.style.display = 'none';
            
            // Clear typing state
            delete typingIndicators[agentId];
        }
    });
    
    ws.on('onTasks', function({ tasks }) {
        if (!tasksContainer) {return;}
        
        // Update tasks display
        renderTasks(tasks);
    });
    
    /**
     * Render tasks in the UI
     * @param {Array} tasks - Array of task objects
     */
    function renderTasks(tasks) {
        if (!tasksContainer || !noTasksMessage) {return;}
        
        // Clear current tasks
        currentTasks = {};
        
        if (!tasks || tasks.length === 0) {
            // Show no tasks message
            noTasksMessage.style.display = 'block';
            
            // Clear any existing task elements
            const taskElements = tasksContainer.querySelectorAll('.task-item');
            taskElements.forEach(element => element.remove());
            
            return;
        }
        
        // Hide no tasks message
        noTasksMessage.style.display = 'none';
        
        // Process each task
        tasks.forEach(task => {
            // Store in current tasks
            currentTasks[task.id] = task;
            
            // Check if task element already exists
            let taskElement = document.getElementById(`task-${task.id}`);
            
            if (!taskElement) {
                // Create new task element
                taskElement = document.createElement('div');
                taskElement.id = `task-${task.id}`;
                taskElement.className = 'task-item';
                
                // Add to container
                tasksContainer.appendChild(taskElement);
            }
            
            // Determine task status class
            let statusClass = '';
            let progressValue = 0;
            
            switch (task.status) {
                case 'completed':
                    statusClass = 'completed';
                    progressValue = 100;
                    break;
                case 'in_progress':
                    statusClass = 'in-progress';
                    progressValue = 66;
                    break;
                case 'assigned':
                    statusClass = 'in-progress';
                    progressValue = 33;
                    break;
                case 'failed':
                    statusClass = 'failed';
                    progressValue = 100;
                    break;
                default:
                    statusClass = 'pending';
                    progressValue = 0;
            }
            
            // Add status class
            taskElement.className = `task-item ${statusClass}`;
            
            // Format assigned information
            const assignedText = task.assigned_to ? 
                `Assigned to: ${formatAgentName(task.assigned_to)}` : 
                'Unassigned';
                
            // Format timestamps
            let timeInfo = '';
            if (task.completed_at) {
                timeInfo = `Completed: ${formatDateTime(task.completed_at)}`;
            } else if (task.started_at) {
                timeInfo = `Started: ${formatDateTime(task.started_at)}`;
            } else {
                timeInfo = `Created: ${formatDateTime(task.created_at)}`;
            }
            
            // Update content
            taskElement.innerHTML = `
                <div class="task-title">${task.title}</div>
                <div class="task-description text-muted small">${task.description}</div>
                <div class="d-flex justify-content-between mt-2">
                    <span class="task-assigned small">${assignedText}</span>
                    <span class="task-time small">${timeInfo}</span>
                </div>
                <div class="progress task-progress">
                    <div class="progress-bar bg-${statusClass === 'failed' ? 'danger' : 'primary'}" 
                         role="progressbar" 
                         style="width: ${progressValue}%" 
                         aria-valuenow="${progressValue}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
            `;
        });
        
        // Remove task elements that are no longer in the tasks list
        const taskElements = tasksContainer.querySelectorAll('.task-item');
        taskElements.forEach(element => {
            const taskId = element.id.replace('task-', '');
            if (!currentTasks[taskId]) {
                element.remove();
            }
        });
    }
    
    /**
     * Format a datetime string
     * @param {string} datetimeStr - ISO datetime string
     * @returns {string} Formatted datetime
     */
    function formatDateTime(datetimeStr) {
        if (!datetimeStr) {return '';}
        
        try {
            return new Date(datetimeStr).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit'
            });
        } catch (e) {
            return datetimeStr;
        }
    }
    
    // Connect to WebSocket
    ws.connect();
    
    /**
     * Send a message to the session
     */
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) {return;}
        
        // Disable form while sending
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Create message request
        const message = {
            from_agent: 'user',
            to_agent: 'architect',
            message_type: 'user_input',
            content: {
                text: text
            }
        };
        
        // Send message to API
        fetch(`/api/sessions/${sessionId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(message)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Clear input
            messageInput.value = '';
            
            // Request latest messages
            ws.send({ type: 'get_messages', last_message_id: lastMessageId });
        })
        .catch(error => {
            console.error('Error sending message:', error);
            
            // Show error
            const errorToast = document.createElement('div');
            errorToast.className = 'alert alert-danger';
            errorToast.textContent = `Error sending message: ${error.message}`;
            messagesContainer.appendChild(errorToast);
            
            // Remove after 5 seconds
            setTimeout(() => errorToast.remove(), 5000);
        })
        .finally(() => {
            // Re-enable form
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        });
    }
    
    /**
     * Render messages in the UI
     * @param {Array} messages - Array of message objects
     */
    function renderMessages(messages) {
        if (!Array.isArray(messages) || messages.length === 0 || !messagesContainer) {return;}
        
        messages.forEach(message => {
            const messageId = message.id;
            
            // Skip if already rendered
            if (document.getElementById(`message-${messageId}`)) {return;}
            
            // Update last message ID
            lastMessageId = messageId;
            
            // Create message element
            const messageElement = document.createElement('div');
            messageElement.id = `message-${messageId}`;
            messageElement.className = `message message-${message.from_agent}`;
            
            // Extract message content
            let content = '';
            if (message.content && message.content.text) {
                content = message.content.text;
            } else {
                content = JSON.stringify(message.content);
            }
            
            // Format the message
            const timestamp = new Date(message.timestamp).toLocaleTimeString();
            
            messageElement.innerHTML = `
                <div class="message-header">
                    <span class="message-sender">${formatAgentName(message.from_agent)}</span>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-content">${formatMessageContent(content)}</div>
            `;
            
            // Add to container
            messagesContainer.appendChild(messageElement);
        });
        
        // Scroll to bottom if was at bottom before
        if (isAtBottom && conversationArea) {
            scrollToBottom(conversationArea);
        }
    }
    
    /**
     * Format agent name for display
     * @param {string} agentId - Agent ID
     * @returns {string} Formatted agent name
     */
    function formatAgentName(agentId) {
        switch (agentId) {
            case 'architect': return 'Architect';
            case 'user': return 'You';
            case 'system': return 'System';
            default:
                if (agentId && agentId.startsWith('worker')) {
                    return `Worker ${agentId.replace('worker', '')}`;
                }
                return agentId || 'Unknown';
        }
    }
    
    /**
     * Format message content with basic markdown
     * @param {string} content - Message content
     * @returns {string} Formatted HTML
     */
    function formatMessageContent(content) {
        if (!content) {return '';}
        
        // Convert code blocks
        content = content.replace(/```([a-z]*)\n([\s\S]*?)\n```/g, '<pre><code class="language-$1">$2</code></pre>');
        
        // Convert inline code
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Convert bold text
        content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Convert italic text
        content = content.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    /**
     * Scroll element to the bottom
     * @param {HTMLElement} element - Element to scroll
     */
    function scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }
    
    // Return the WebSocket connection so it can be used elsewhere
    return {
        ws,
        sendMessage
    };
}
