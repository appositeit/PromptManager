/**
 * Utility functions for the Coordinator UI
 */

/**
 * Toggle sidebar and save state to localStorage
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebar && mainContent) {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        
        // Save state to localStorage
        localStorage.setItem('sidebar_collapsed', isCollapsed ? 'true' : 'false');
    }
}

/**
 * Initialize sidebar state from localStorage
 */
function initSidebarState() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebar && mainContent) {
        const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
        
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    }
}

/**
 * Initialize dayjs with all required plugins
 */
function initializeDayjs() {
    if (window.dayjs) {
        // Initialize the relative time plugin if loaded
        if (window.dayjs_plugin_relativeTime) {
            window.dayjs.extend(window.dayjs_plugin_relativeTime);
        }
    }
}

// Run the initialization
initializeDayjs();

/**
 * Format a timestamp relative to now
 * 
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted time string
 */
function formatRelativeTime(timestamp) {
    if (!timestamp) return '';
    if (typeof window.dayjs().fromNow !== 'function') {
        // Fallback if fromNow is not available
        return new Date(timestamp).toLocaleString();
    }
    return window.dayjs(timestamp).fromNow();
}

/**
 * Format a timestamp as absolute time
 * 
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted time string
 */
function formatAbsoluteTime(timestamp) {
    if (!timestamp) return '';
    return dayjs(timestamp).format('MMM D, YYYY HH:mm:ss');
}

/**
 * Create a WebSocket connection with automatic reconnection
 * 
 * @param {string} url - WebSocket URL
 * @param {object} options - Configuration options
 * @returns {object} WebSocket connection manager
 */
function createWebSocketManager(url, options = {}) {
    const defaultOptions = {
        reconnectInterval: 2000,
        maxReconnectAttempts: 10,
        onOpen: () => {},
        onMessage: () => {},
        onClose: () => {},
        onError: () => {},
        onReconnect: () => {}
    };
    
    const config = { ...defaultOptions, ...options };
    let socket = null;
    let reconnectAttempts = 0;
    let reconnectInterval = null;
    
    function connect() {
        socket = new WebSocket(url);
        
        socket.onopen = event => {
            reconnectAttempts = 0;
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
            config.onOpen(event);
        };
        
        socket.onmessage = event => {
            config.onMessage(event);
        };
        
        socket.onclose = event => {
            config.onClose(event);
            
            if (!event.wasClean && reconnectAttempts < config.maxReconnectAttempts) {
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(() => {
                        reconnectAttempts++;
                        config.onReconnect(reconnectAttempts);
                        connect();
                    }, config.reconnectInterval);
                }
            }
        };
        
        socket.onerror = event => {
            config.onError(event);
        };
    }
    
    function send(data) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            if (typeof data === 'object') {
                socket.send(JSON.stringify(data));
            } else {
                socket.send(data);
            }
            return true;
        }
        return false;
    }
    
    function close() {
        if (socket) {
            socket.close();
        }
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    }
    
    // Return API
    return {
        connect,
        send,
        close,
        isConnected: () => socket && socket.readyState === WebSocket.OPEN
    };
}

/**
 * Format message content with basic markdown support
 * 
 * @param {string} content - Message content
 * @returns {string} Formatted HTML
 */
function formatMessageContent(content) {
    if (!content) return '';
    
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
 * Convert markdown text to HTML using the marked library
 * 
 * @param {string} markdown - Markdown content
 * @returns {string} HTML content
 */
function markdownToHtml(markdown) {
    if (!markdown) return '';
    
    // Use the marked library to convert markdown to HTML
    try {
        return marked.parse(markdown);
    } catch (e) {
        console.error('Error parsing markdown:', e);
        return '<p>Error parsing markdown content</p>';
    }
}

/**
 * Format an agent name for display
 * 
 * @param {string} agentId - Agent ID
 * @returns {string} Formatted agent name
 */
function formatAgentName(agentId) {
    if (!agentId) return 'Unknown';
    
    switch (agentId) {
        case 'architect': return 'Architect';
        case 'user': return 'You';
        case 'system': return 'System';
        default:
            if (agentId.startsWith('worker')) {
                return `Worker ${agentId.replace('worker', '')}`;
            }
            return agentId;
    }
}

/**
 * Scroll an element to the bottom
 * 
 * @param {HTMLElement} element - Element to scroll
 */
function scrollToBottom(element) {
    if (element) {
        element.scrollTop = element.scrollHeight;
    }
}

/**
 * Show a toast notification
 * 
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds
 */
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type} text-white`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.id = toastId;
    
    // Create toast content
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">Coordinator</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Close button event
    toast.querySelector('.btn-close').addEventListener('click', () => {
        toast.remove();
    });
    
    // Auto-remove after duration
    setTimeout(() => {
        toast.remove();
    }, duration);
}
