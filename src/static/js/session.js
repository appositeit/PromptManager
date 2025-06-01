/**
 * Session management functionality for the Coordinator system
 */

/**
 * Initialize the session management functionality
 */
function initSessionManagement() {
    // Load the session form with available data
    loadSessionFormData();
    
    // Set up event handlers - support both naming conventions
    const createSessionBtnCamel = document.getElementById('createSessionBtn');
    const createSessionBtnHyphen = document.getElementById('create-session-btn');
    
    if (createSessionBtnCamel) {
        createSessionBtnCamel.addEventListener('click', createSession);
    }
    
    if (createSessionBtnHyphen) {
        createSessionBtnHyphen.addEventListener('click', createSession);
    }
    
    // Load active sessions
    loadActiveSessions();
    
    // Set up periodic refresh of active sessions
    setInterval(loadActiveSessions, 10000); // Refresh every 10 seconds
}

/**
 * Load data for the session form (prompts, API keys, etc.)
 */
function loadSessionFormData() {
    // Load available prompts
    loadAvailablePrompts();
    
    // Load API keys (mock for now - would be replaced with actual API call)
    loadApiKeys();
}

/**
 * Load available prompts into the session prompt dropdown
 */
function loadAvailablePrompts() {
    const promptSelect = document.getElementById('sessionPrompt');
    if (!promptSelect) {return;}
    
    // Clear existing options (except the first one)
    const firstOption = promptSelect.querySelector('option:first-child');
    promptSelect.innerHTML = '';
    promptSelect.appendChild(firstOption);
    
    // Fetch prompts from the API
    fetch('/api/prompts/all')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load prompts: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(prompts => {
            // Group prompts by type
            const promptsByType = {
                'system': [],
                'user': [],
                'standard': [],
                'composite': []
            };
            
            prompts.forEach(prompt => {
                if (prompt.is_composite) {
                    promptsByType.composite.push(prompt);
                } else {
                    promptsByType.standard.push(prompt);
                }
            });
            
            // Add prompts to select element, grouped by type
            const types = {
                'system': 'System Prompts',
                'user': 'User Prompts',
                'composite': 'Composite Prompts',
                'standard': 'Standard Prompts'
            };
            
            Object.keys(types).forEach(type => {
                if (promptsByType[type].length > 0) {
                    // Add optgroup for this type
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = types[type];
                    
                    // Sort prompts by ID
                    promptsByType[type].sort((a, b) => a.id.localeCompare(b.id));
                    
                    // Add options for each prompt
                    promptsByType[type].forEach(prompt => {
                        const option = document.createElement('option');
                        option.value = prompt.id;
                        option.textContent = prompt.id;
                        if (prompt.description) {
                            option.title = prompt.description;
                        }
                        optgroup.appendChild(option);
                    });
                    
                    promptSelect.appendChild(optgroup);
                }
            });
        })
        .catch(error => {
            console.error('Error loading prompts:', error);
            
            // Add an error option
            const option = document.createElement('option');
            option.disabled = true;
            option.textContent = 'Error loading prompts';
            promptSelect.appendChild(option);
        });
}

/**
 * Load API keys (mock implementation for now)
 */
function loadApiKeys() {
    const architectApiKey = document.getElementById('architectApiKey');
    const workerApiKeys = document.querySelectorAll('.worker-api-key');
    
    // Mock API keys for demonstration
    const mockApiKeys = [
        { id: 'default', name: 'Default API Key' },
        { id: 'anthropic-1', name: 'Anthropic API Key' },
        { id: 'openai-1', name: 'OpenAI API Key' },
        { id: 'google-1', name: 'Google API Key' }
    ];
    
    // Populate architect API key select
    if (architectApiKey) {
        architectApiKey.innerHTML = '';
        
        mockApiKeys.forEach(key => {
            const option = document.createElement('option');
            option.value = key.id;
            option.textContent = key.name;
            architectApiKey.appendChild(option);
        });
    }
    
    // Populate worker API key selects
    workerApiKeys.forEach(select => {
        select.innerHTML = '';
        
        mockApiKeys.forEach(key => {
            const option = document.createElement('option');
            option.value = key.id;
            option.textContent = key.name;
            select.appendChild(option);
        });
    });
}

/**
 * Create a new session with the provided configuration
 */
// Flag to use mock mode only if real API fails
const USE_MOCK_MODE = false;

function createSession() {
    // Get form values - handling both hyphenated and camelCase IDs for backwards compatibility
    const sessionNameElement = document.getElementById('sessionName') || document.getElementById('session-name');
    const sessionName = sessionNameElement ? sessionNameElement.value.trim() : '';
    
    const sessionPromptElement = document.getElementById('sessionPrompt') || document.getElementById('session-prompt');
    const sessionPrompt = sessionPromptElement ? sessionPromptElement.value : '';
    
    const architectModelElement = document.getElementById('architectModel') || document.getElementById('architect-model');
    const architectModel = architectModelElement ? architectModelElement.value : 'claude-3-sonnet-20240229';
    
    const architectApiKeyElement = document.getElementById('architectApiKey') || document.getElementById('architect-api-key');
    const architectApiKey = architectApiKeyElement?.value;
    
    const workerCountElement = document.getElementById('workerCount') || document.getElementById('worker-count');
    const workerCount = parseInt(workerCountElement?.value || 0);
    
    // Get session description if available (checking both ID formats)
    let sessionDescription = '';
    const sessionDescElement = document.getElementById('sessionDescription') || document.getElementById('session-description');
    if (sessionDescElement) {
        sessionDescription = sessionDescElement.value.trim();
    }
    
    // Get session directory if available (checking both ID formats)
    let sessionDirectory = '';
    const directoryElement = document.getElementById('sessionDirectory') || document.getElementById('session-directory');
    if (directoryElement) {
        sessionDirectory = directoryElement.value.trim();
    }
    
    // Get MCP servers if available
    const mcpServers = [];
    const mcpServerElements = document.querySelectorAll('input[name="mcp-server"]:checked');
    mcpServerElements.forEach(element => {
        mcpServers.push(element.value);
    });
    
    // Validate session name
    if (!sessionName) {
        alert('Please enter a session name');
        return;
    }
    
    // If we couldn't find critical elements, show an error and abort
    if (!sessionNameElement || !architectModelElement) {
        console.error('Critical form elements are missing on this page');
        alert('Error: Could not find all required form elements. Please reload the page.');
        return;
    }
    
    // Collect worker configurations
    const workers = [];
    
    // Handle different session creation forms (modal vs full page)
    if (document.getElementById('workers-container')) {
        // Full form with detailed worker configuration
        document.querySelectorAll('.worker-item').forEach(item => {
            const workerName = item.querySelector('.worker-name')?.value.trim() || '';
            const workerModel = item.querySelector('.worker-model')?.value || 'claude-3-haiku-20240307';
            
            // Get worker capabilities if available
            const capabilities = [];
            const capabilitiesSelect = item.querySelector('.worker-capabilities');
            if (capabilitiesSelect) {
                Array.from(capabilitiesSelect.selectedOptions).forEach(option => {
                    capabilities.push(option.value);
                });
            }
            
            // Get system prompt if available
            const systemPrompt = item.querySelector('.worker-prompt')?.value.trim() || '';
            
            workers.push({
                name: workerName,
                model: workerModel,
                system_prompt: systemPrompt || null,
                capabilities: capabilities
            });
        });
    } else if (workerCount > 0) {
        // Simple modal form
        for (let i = 0; i < workerCount; i++) {
            const workerModel = document.getElementById(`workerModel${i}`)?.value || 'claude-3-haiku-20240307';
            const workerApiKey = document.getElementById(`workerApiKey${i}`)?.value;
            
            workers.push({
                name: `Worker ${i + 1}`,
                model: workerModel,
                api_key: workerApiKey
            });
        }
    }
    
    // Create session configuration
    const sessionConfig = {
        name: sessionName,
        description: sessionDescription || null,
        directory: sessionDirectory || null,
        architect: {
            model: architectModel,
            system_prompt: null,
            api_key: architectApiKey
        },
        workers: workers,
        mcp_servers: mcpServers.length > 0 ? mcpServers : null,
        intervention_enabled: true
    };
    
    // Show loading state - trying both naming conventions for compatibility
    const createButton = document.getElementById('createSessionBtn') || document.getElementById('create-session-btn');
    if (createButton) {
        createButton.disabled = true;
        createButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
    }
    
    console.log('Creating session with config:', sessionConfig);
    
    // Create the session using the API
    fetch('/api/sessions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(sessionConfig)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        showToast('Session created: ' + sessionName, 'success');
        
        // Close the modal
        const modalElement = document.getElementById('newSessionModal') || document.getElementById('new-session-modal');
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }
        
        // Start the session
        return fetch(`/api/sessions/${data.id}/start`, {
            method: 'POST'
        });
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to start session: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Redirect to the session page
        window.location.href = `/sessions/${data.id}`;
    })
    .catch(error => {
        console.error('Error creating/starting session:', error);
        showToast('Error: ' + error.message, 'danger');
        
        // Reset button
        if (createButton) {
            createButton.disabled = false;
            createButton.innerHTML = 'Create Session';
        }
        
        // If real API fails, try mock mode as fallback
        if (USE_MOCK_MODE) {
            createMockSession(sessionConfig);
        }
    });
}

// Function to create a mock session for demonstration
function createMockSession(sessionConfig) {
    // Generate a random session ID
    const sessionId = 'mock-' + Math.random().toString(36).substring(2, 10);
    
    // Create a mock session in localStorage
    const mockSession = {
        id: sessionId,
        name: sessionConfig.name,
        description: sessionConfig.description || '',
        status: 'running',
        config: sessionConfig,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: []
    };
    
    // Store in localStorage
    const storedSessions = JSON.parse(localStorage.getItem('mockSessions') || '{}');
    storedSessions[sessionId] = mockSession;
    localStorage.setItem('mockSessions', JSON.stringify(storedSessions));
    
    // Show success message
    showToast('Mock session created: ' + sessionConfig.name, 'success');
    
    // Close the modal
    const modalElement = document.getElementById('newSessionModal') || document.getElementById('new-session-modal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
    
    // Reset any create button
    const createButton = document.getElementById('createSessionBtn') || document.getElementById('create-session-btn');
    if (createButton) {
        createButton.disabled = false;
        createButton.innerHTML = 'Create Session';
    }
    
    // Redirect to session page
    window.location.href = `/sessions/${sessionId}`;
}

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, danger, warning, info)
 */
function showToast(message, type = 'info') {
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
    toast.className = `toast bg-${type} text-white`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Toast header
    const header = document.createElement('div');
    header.className = 'toast-header bg-transparent text-white';
    
    const title = document.createElement('strong');
    title.className = 'me-auto';
    title.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn-close btn-close-white';
    closeBtn.setAttribute('type', 'button');
    closeBtn.setAttribute('data-bs-dismiss', 'toast');
    closeBtn.setAttribute('aria-label', 'Close');
    
    header.appendChild(title);
    header.appendChild(closeBtn);
    
    // Toast body
    const body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = message;
    
    // Assemble toast
    toast.appendChild(header);
    toast.appendChild(body);
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
    
    // Remove after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Load active sessions and display them
 */
function loadActiveSessions() {
    // In mock mode, load from localStorage
    if (USE_MOCK_MODE) {
        const storedSessions = JSON.parse(localStorage.getItem('mockSessions') || '{}');
        const sessions = Object.values(storedSessions).filter(s => s.status === 'running');
        
        // Update sidebar
        updateSidebarSessions(sessions);
        
        // Update dashboard if on home page
        const dashboardActiveSessionsElement = document.getElementById('dashboard-active-sessions');
        if (dashboardActiveSessionsElement) {
            updateDashboardSessions(sessions);
        }
        
        return;
    }

    // Regular API mode
    fetch('/api/sessions/active')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load sessions: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(sessions => {
            // Update sidebar
            updateSidebarSessions(sessions);
            
            // Update dashboard if on home page
            const dashboardActiveSessionsElement = document.getElementById('dashboard-active-sessions');
            if (dashboardActiveSessionsElement) {
                updateDashboardSessions(sessions);
            }
        })
        .catch(error => {
            console.error('Error loading active sessions:', error);
        });
}

/**
 * Update the sidebar with active sessions
 */
function updateSidebarSessions(sessions) {
    const container = document.getElementById('active-sessions');
    if (!container) {return;}
    
    if (sessions.length === 0) {
        container.innerHTML = '<div class="text-muted sidebar-no-sessions">No active sessions</div>';
        return;
    }
    
    let html = '';
    sessions.forEach(session => {
        const sessionUrl = USE_MOCK_MODE ? 
            `/static/session_demo.html?id=${session.id}` : 
            `/sessions/${session.id}`;
            
        html += `
            <li class="sidebar-item">
                <a href="${sessionUrl}" class="sidebar-link">
                    <i class="bi bi-chat-dots"></i>
                    <span>${session.name}</span>
                </a>
            </li>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Update the dashboard with active sessions
 */
function updateDashboardSessions(sessions) {
    const container = document.getElementById('dashboard-active-sessions');
    if (!container) {return;}
    
    if (sessions.length === 0) {
        container.innerHTML = '<p class="text-muted mb-0">No active sessions.</p>';
        return;
    }
    
    let html = '<ul class="list-group">';
    sessions.forEach(session => {
        const sessionUrl = USE_MOCK_MODE ? 
            `/static/session_demo.html?id=${session.id}` : 
            `/sessions/${session.id}`;
            
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <a href="${sessionUrl}">${session.name}</a>
                <div>
                    <span class="badge bg-success rounded-pill">Active</span>
                    <button class="btn btn-sm btn-outline-danger ms-2 session-stop-btn" data-session-id="${session.id}">
                        <i class="bi bi-stop-fill"></i>
                    </button>
                </div>
            </li>
        `;
    });
    html += '</ul>';
    
    container.innerHTML = html;
    
    // Add event listeners for stop buttons
    container.querySelectorAll('.session-stop-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const sessionId = this.getAttribute('data-session-id');
            stopSession(sessionId);
        });
    });
}

/**
 * Stop a session
 */
function stopSession(sessionId) {
    if (!confirm('Are you sure you want to stop this session?')) {
        return;
    }
    
    // In mock mode, update localStorage
    if (USE_MOCK_MODE) {
        const storedSessions = JSON.parse(localStorage.getItem('mockSessions') || '{}');
        if (storedSessions[sessionId]) {
            storedSessions[sessionId].status = 'paused';
            localStorage.setItem('mockSessions', JSON.stringify(storedSessions));
            showToast('Session stopped', 'info');
            loadActiveSessions();
        }
        return;
    }
    
    // Regular API mode
    fetch(`/api/sessions/${sessionId}/stop`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to stop session: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        showToast('Session stopped', 'info');
        loadActiveSessions();
    })
    .catch(error => {
        console.error('Error stopping session:', error);
        showToast('Error: ' + error.message, 'danger');
    });
}

// Initialize session management when the DOM is loaded
document.addEventListener('DOMContentLoaded', initSessionManagement);
