/**
 * Real-Time Visualization
 * 
 * This module connects the visualization components to real-time WebSocket
 * updates to provide live visualization of agent interactions and tasks.
 */

/**
 * Real-time Task Visualization Manager
 * 
 * Manages the real-time visualization of tasks and agent interactions.
 */
class RealTimeVisualizationManager {
    /**
     * Create a new Real-time Visualization Manager.
     * 
     * @param {string} graphContainerId - ID of the graph container element
     * @param {string} timelineContainerId - ID of the timeline container element
     * @param {string} sessionId - Session ID
     * @param {Object} options - Configuration options
     */
    constructor(graphContainerId, timelineContainerId, sessionId, options = {}) {
        this.graphContainerId = graphContainerId;
        this.timelineContainerId = timelineContainerId;
        this.sessionId = sessionId;
        
        // Configuration
        this.options = {
            wsBaseUrl: options.wsBaseUrl || `ws://${window.location.host}/api/ws`,
            debug: options.debug || false,
            token: options.token,
            autoConnect: options.autoConnect !== false,
            ...options
        };
        
        // Initialize components
        this.websocket = null;
        this.taskGraph = null;
        this.taskTimeline = null;
        
        // Data
        this.agents = [];
        this.tasks = [];
        this.messages = [];
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the visualization manager.
     */
    initialize() {
        // Initialize WebSocket client
        this.initializeWebSocket();
        
        // Initialize visualization components
        this.initializeVisualization();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Connect if auto-connect is enabled
        if (this.options.autoConnect) {
            this.connect();
        }
    }
    
    /**
     * Initialize the WebSocket client.
     */
    initializeWebSocket() {
        this.websocket = new VisualizationWebSocketClient(
            this.options.wsBaseUrl,
            this.sessionId,
            {
                token: this.options.token,
                debug: this.options.debug
            }
        );
        
        // Set up WebSocket event handlers
        this.websocket.on('connect', (data) => {
            this.log('WebSocket connected');
            
            // Fetch initial data if components are already initialized
            if (this.taskGraph && this.taskTimeline) {
                this.fetchInitialData();
            }
        });
        
        this.websocket.on('disconnect', () => {
            this.log('WebSocket disconnected');
        });
        
        this.websocket.on('error', (data) => {
            console.error('WebSocket error:', data.error);
        });
        
        // Task event handlers
        this.websocket.on('task_update', (data) => {
            this.handleTaskUpdate(data.data.task);
        });
        
        this.websocket.on('task_created', (data) => {
            this.handleTaskCreated(data.data);
        });
        
        this.websocket.on('task_started', (data) => {
            this.handleTaskStarted(data.data);
        });
        
        this.websocket.on('task_completed', (data) => {
            this.handleTaskCompleted(data.data);
        });
        
        this.websocket.on('task_failed', (data) => {
            this.handleTaskFailed(data.data);
        });
        
        // Agent status handler
        this.websocket.on('agent_status', (data) => {
            this.handleAgentStatus(data.data);
        });
        
        // Session status handler
        this.websocket.on('session_status', (data) => {
            this.handleSessionStatus(data.data);
        });
    }
    
    /**
     * Initialize the visualization components.
     */
    initializeVisualization() {
        // Initialize task graph
        this.taskGraph = new TaskGraphVisualizer(this.graphContainerId);
        
        // Initialize task timeline
        this.taskTimeline = new TaskTimelineVisualizer(this.timelineContainerId);
    }
    
    /**
     * Set up event listeners.
     */
    setupEventListeners() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.resize();
        });
        
        // Task graph node click
        document.getElementById(this.graphContainerId).addEventListener('node-click', (event) => {
            const node = event.detail.node;
            this.onNodeClick(node);
        });
        
        // Task timeline task click
        document.getElementById(this.timelineContainerId).addEventListener('task-click', (event) => {
            const task = event.detail.task;
            this.onTaskClick(task);
        });
    }
    
    /**
     * Connect to the WebSocket server.
     */
    connect() {
        this.websocket.connect().catch((error) => {
            console.error('Failed to connect to WebSocket:', error);
        });
    }
    
    /**
     * Disconnect from the WebSocket server.
     */
    disconnect() {
        this.websocket.disconnect();
    }
    
    /**
     * Fetch initial data for the visualization.
     */
    fetchInitialData() {
        // Use AJAX to fetch session data
        fetch(`/api/sessions/${this.sessionId}`)
            .then(response => response.json())
            .then(sessionData => {
                // Extract agents from session data
                const agents = [{
                    id: 'architect',
                    name: 'Architect',
                    role: 'architect',
                    status: 'active'
                }];
                
                // Add workers
                if (sessionData.config && sessionData.config.workers) {
                    sessionData.config.workers.forEach((worker, index) => {
                        agents.push({
                            id: `worker${index}`,
                            name: worker.name || `Worker ${index + 1}`,
                            role: 'worker',
                            capabilities: worker.capabilities || [],
                            status: 'idle'
                        });
                    });
                }
                
                this.agents = agents;
                
                // Fetch tasks
                return fetch(`/api/sessions/${this.sessionId}/tasks`);
            })
            .then(response => response.json())
            .then(tasksData => {
                this.tasks = tasksData.tasks || [];
                
                // Update visualizations
                this.updateVisualizations();
            })
            .catch(error => {
                console.error('Error fetching initial data:', error);
            });
    }
    
    /**
     * Update the visualizations with current data.
     */
    updateVisualizations() {
        const data = {
            agents: this.agents,
            tasks: this.tasks
        };
        
        this.taskGraph.update(data);
        this.taskTimeline.update(data);
    }
    
    /**
     * Handle task update event.
     * 
     * @param {Object} task - Updated task
     */
    handleTaskUpdate(task) {
        // Find and update existing task
        const index = this.tasks.findIndex(t => t.id === task.id);
        
        if (index >= 0) {
            this.tasks[index] = { ...this.tasks[index], ...task };
        } else {
            this.tasks.push(task);
        }
        
        // Update visualizations
        this.updateVisualizations();
    }
    
    /**
     * Handle task created event.
     * 
     * @param {Object} data - Event data
     */
    handleTaskCreated(data) {
        const taskId = data.task_id;
        
        // Check if task already exists
        if (!this.tasks.some(t => t.id === taskId)) {
            // Add new task
            const task = {
                id: taskId,
                title: data.title,
                description: data.description,
                status: 'pending',
                assigned_to: data.assigned_to,
                created_at: new Date().toISOString()
            };
            
            this.tasks.push(task);
            
            // Update visualizations
            this.updateVisualizations();
        }
    }
    
    /**
     * Handle task started event.
     * 
     * @param {Object} data - Event data
     */
    handleTaskStarted(data) {
        const taskId = data.task_id;
        
        // Find and update task
        const task = this.tasks.find(t => t.id === taskId);
        
        if (task) {
            task.status = 'in_progress';
            task.start_time = new Date().toISOString();
            
            // Update visualizations
            this.updateVisualizations();
        }
    }
    
    /**
     * Handle task completed event.
     * 
     * @param {Object} data - Event data
     */
    handleTaskCompleted(data) {
        const taskId = data.task_id;
        
        // Find and update task
        const task = this.tasks.find(t => t.id === taskId);
        
        if (task) {
            task.status = 'completed';
            task.completed_at = new Date().toISOString();
            task.result = data.result;
            
            // Update visualizations
            this.updateVisualizations();
        }
    }
    
    /**
     * Handle task failed event.
     * 
     * @param {Object} data - Event data
     */
    handleTaskFailed(data) {
        const taskId = data.task_id;
        
        // Find and update task
        const task = this.tasks.find(t => t.id === taskId);
        
        if (task) {
            task.status = 'failed';
            task.failed_at = new Date().toISOString();
            task.error = data.error;
            
            // Update visualizations
            this.updateVisualizations();
        }
    }
    
    /**
     * Handle agent status event.
     * 
     * @param {Object} data - Event data
     */
    handleAgentStatus(data) {
        const agentId = data.agent_id;
        
        // Find and update agent
        const agent = this.agents.find(a => a.id === agentId);
        
        if (agent) {
            agent.status = data.status;
            
            // Update visualizations
            this.updateVisualizations();
        }
    }
    
    /**
     * Handle session status event.
     * 
     * @param {Object} data - Event data
     */
    handleSessionStatus(data) {
        const status = data.status;
        
        // Dispatch session status event
        const event = new CustomEvent('session-status-change', {
            detail: {
                status: status,
                metadata: data.metadata || {}
            }
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * Handle node click in the task graph.
     * 
     * @param {Object} node - Node that was clicked
     */
    onNodeClick(node) {
        // Highlight node somehow?
        
        // Dispatch event
        const event = new CustomEvent('visualization-node-click', {
            detail: {
                node: node
            }
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * Handle task click in the timeline.
     * 
     * @param {Object} task - Task that was clicked
     */
    onTaskClick(task) {
        // Highlight task somehow?
        
        // Dispatch event
        const event = new CustomEvent('visualization-task-click', {
            detail: {
                task: task
            }
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * Resize the visualizations.
     */
    resize() {
        if (this.taskGraph) {
            const graphContainer = document.getElementById(this.graphContainerId);
            this.taskGraph.resize(graphContainer.clientWidth, graphContainer.clientHeight);
        }
        
        if (this.taskTimeline) {
            const timelineContainer = document.getElementById(this.timelineContainerId);
            this.taskTimeline.resize(timelineContainer.clientWidth, timelineContainer.clientHeight);
        }
    }
    
    /**
     * Log a message if debug is enabled.
     * 
     * @param {string} message - Message to log
     */
    log(message) {
        if (this.options.debug) {
            console.log(`[VisualizationManager] ${message}`);
        }
    }
}
