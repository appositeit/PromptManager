/**
 * Task management functionality for the Coordinator system
 */

window.TaskManager = (function() {
    /**
     * Initialize task management functionality
     * @param {string} sessionId - The session ID
     * @returns {object} Task manager interface
     */
    function initTaskManager(sessionId) {
    // UI Elements
    const taskCreateBtn = document.getElementById('create-task-btn');
    const taskListContainer = document.getElementById('tasks-container');
    const taskDetailContainer = document.getElementById('task-detail-container');
    
    // Task data
    let tasks = [];
    let selectedTaskId = null;
    
    // Event handlers
    if (taskCreateBtn) {
        taskCreateBtn.addEventListener('click', showCreateTaskModal);
    }
    
    /**
     * Load tasks from the API
     */
    async function loadTasks() {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/tasks`);
            if (!response.ok) {
                throw new Error(`Failed to load tasks: ${response.status}`);
            }
            
            const data = await response.json();
            tasks = data;
            
            renderTaskList();
            
            // If a task is selected, refresh its details
            if (selectedTaskId) {
                const selectedTask = tasks.find(t => t.id === selectedTaskId);
                if (selectedTask) {
                    renderTaskDetail(selectedTask);
                } else {
                    // Task no longer exists, clear selection
                    selectedTaskId = null;
                    clearTaskDetail();
                }
            }
            
            return tasks;
        } catch (error) {
            console.error('Error loading tasks:', error);
            showToast('Error loading tasks', 'danger');
            return [];
        }
    }
    
    /**
     * Render the task list
     */
    function renderTaskList() {
        if (!taskListContainer) {return;}
        
        // Clear no tasks message if it exists
        const noTasksMsg = document.getElementById('no-tasks-message');
        if (noTasksMsg) {
            noTasksMsg.style.display = tasks.length === 0 ? 'block' : 'none';
        }
        
        // Group tasks by status
        const tasksByStatus = {
            'pending': [],
            'assigned': [],
            'in_progress': [],
            'completed': [],
            'failed': [],
            'cancelled': []
        };
        
        // Add tasks to appropriate status group
        tasks.forEach(task => {
            if (tasksByStatus[task.status]) {
                tasksByStatus[task.status].push(task);
            } else {
                tasksByStatus.pending.push(task);
            }
        });
        
        // Create sections for each status
        const sections = [
            { status: 'in_progress', title: 'In Progress', class: 'in-progress' },
            { status: 'assigned', title: 'Assigned', class: 'assigned' },
            { status: 'pending', title: 'Pending', class: 'pending' },
            { status: 'completed', title: 'Completed', class: 'completed' },
            { status: 'failed', title: 'Failed', class: 'failed' }
        ];
        
        // Clear existing task elements
        const existingTasks = taskListContainer.querySelectorAll('.task-item');
        existingTasks.forEach(el => el.remove());
        
        // Create task sections
        sections.forEach(section => {
            const sectionTasks = tasksByStatus[section.status];
            
            if (sectionTasks.length > 0) {
                // Create section header if it doesn't exist
                let sectionHeader = taskListContainer.querySelector(`.task-section-${section.status}`);
                if (!sectionHeader) {
                    sectionHeader = document.createElement('div');
                    sectionHeader.className = `task-section task-section-${section.status}`;
                    sectionHeader.innerHTML = `
                        <h6 class="task-section-title">${section.title} (${sectionTasks.length})</h6>
                    `;
                    taskListContainer.appendChild(sectionHeader);
                } else {
                    // Update count in title
                    const titleEl = sectionHeader.querySelector('.task-section-title');
                    if (titleEl) {
                        titleEl.textContent = `${section.title} (${sectionTasks.length})`;
                    }
                }
                
                // Create task items
                sectionTasks.forEach(task => {
                    renderTaskItem(task, section.class);
                });
            }
        });
    }
    
    /**
     * Render a task item in the list
     * @param {object} task - Task data
     * @param {string} statusClass - Status CSS class
     */
    function renderTaskItem(task, statusClass) {
        if (!taskListContainer) {return;}
        
        // Check if task item already exists
        let taskEl = document.getElementById(`task-item-${task.id}`);
        
        if (!taskEl) {
            // Create new task element
            taskEl = document.createElement('div');
            taskEl.id = `task-item-${task.id}`;
            taskEl.className = `task-item ${statusClass}`;
            taskListContainer.appendChild(taskEl);
            
            // Add click handler
            taskEl.addEventListener('click', () => {
                selectTask(task.id);
            });
        } else {
            // Update existing element's class
            taskEl.className = `task-item ${statusClass}`;
        }
        
        // Calculate progress percentage
        let progressValue = 0;
        switch (task.status) {
            case 'completed': progressValue = 100; break;
            case 'in_progress': progressValue = 66; break;
            case 'assigned': progressValue = 33; break;
            case 'failed': progressValue = 100; break;
            default: progressValue = 0;
        }
        
        // Format assigned information
        const assignedText = task.assigned_to ? 
            `${formatAgentName(task.assigned_to)}` : 
            'Unassigned';
        
        // Check if task is selected
        const isSelected = task.id === selectedTaskId;
        if (isSelected) {
            taskEl.classList.add('selected');
        } else {
            taskEl.classList.remove('selected');
        }
        
        // Set task item content
        taskEl.innerHTML = `
            <div class="task-item-header">
                <span class="task-item-title">${task.title}</span>
                <span class="task-item-badge ${statusClass}">${task.status}</span>
            </div>
            <div class="progress task-progress mt-2 mb-1">
                <div class="progress-bar bg-${task.status === 'failed' ? 'danger' : 'primary'}" 
                     role="progressbar" 
                     style="width: ${progressValue}%" 
                     aria-valuenow="${progressValue}" 
                     aria-valuemin="0" 
                     aria-valuemax="100"></div>
            </div>
            <div class="task-item-footer">
                <small class="task-item-assigned">${assignedText}</small>
                <small class="task-item-id">#${task.id.substring(0, 8)}</small>
            </div>
        `;
    }
    
    /**
     * Select a task and show its details
     * @param {string} taskId - Task ID
     */
    function selectTask(taskId) {
        selectedTaskId = taskId;
        
        // Update selected status in task list
        const taskItems = taskListContainer?.querySelectorAll('.task-item');
        if (taskItems) {
            taskItems.forEach(el => {
                if (el.id === `task-item-${taskId}`) {
                    el.classList.add('selected');
                } else {
                    el.classList.remove('selected');
                }
            });
        }
        
        // Find the selected task
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            renderTaskDetail(task);
        }
    }
    
    /**
     * Render detailed view of a task
     * @param {object} task - Task data
     */
    function renderTaskDetail(task) {
        if (!taskDetailContainer) {return;}
        
        // Show the detail container
        taskDetailContainer.style.display = 'block';
        
        // Format timestamps
        const createdAt = formatDateTime(task.created_at);
        const updatedAt = formatDateTime(task.updated_at);
        const startedAt = task.started_at ? formatDateTime(task.started_at) : 'Not started';
        const completedAt = task.completed_at ? formatDateTime(task.completed_at) : 'Not completed';
        
        // Format status badge
        let statusBadgeClass = '';
        switch (task.status) {
            case 'completed': statusBadgeClass = 'bg-success'; break;
            case 'in_progress': statusBadgeClass = 'bg-primary'; break;
            case 'assigned': statusBadgeClass = 'bg-info'; break;
            case 'failed': statusBadgeClass = 'bg-danger'; break;
            case 'pending': statusBadgeClass = 'bg-secondary'; break;
            default: statusBadgeClass = 'bg-secondary';
        }
        
        // Format result or error
        let resultHtml = '';
        if (task.result) {
            if (typeof task.result === 'object' && task.result.text) {
                resultHtml = `
                    <div class="task-result">
                        <h6>Result</h6>
                        <div class="task-result-content">
                            ${formatContent(task.result.text)}
                        </div>
                    </div>
                `;
            } else {
                resultHtml = `
                    <div class="task-result">
                        <h6>Result</h6>
                        <div class="task-result-content">
                            <pre>${JSON.stringify(task.result, null, 2)}</pre>
                        </div>
                    </div>
                `;
            }
        } else if (task.error) {
            resultHtml = `
                <div class="task-error">
                    <h6>Error</h6>
                    <div class="alert alert-danger">
                        ${task.error}
                    </div>
                </div>
            `;
        }
        
        // Check for subtasks
        let subtasksHtml = '';
        if (task.subtasks && task.subtasks.length > 0) {
            // Find the subtask objects by ID
            const subtaskList = task.subtasks.map(subtaskId => {
                return tasks.find(t => t.id === subtaskId);
            }).filter(t => t); // Remove undefined
            
            if (subtaskList.length > 0) {
                const subtasksItems = subtaskList.map(subtask => `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <span class="subtask-title">${subtask.title}</span>
                            <small class="text-muted d-block">${subtask.status}</small>
                        </div>
                        <span class="badge ${getStatusBadgeClass(subtask.status)}">${subtask.assigned_to || 'Unassigned'}</span>
                    </li>
                `).join('');
                
                subtasksHtml = `
                    <div class="task-subtasks mt-3">
                        <h6>Subtasks</h6>
                        <ul class="list-group">
                            ${subtasksItems}
                        </ul>
                    </div>
                `;
            }
        }
        
        // Task action buttons
        let actionButtonsHtml = '';
        
        if (task.status === 'pending') {
            actionButtonsHtml = `
                <button class="btn btn-sm btn-primary task-execute-btn" data-task-id="${task.id}">
                    <i class="bi bi-play-fill"></i> Execute Task
                </button>
                <button class="btn btn-sm btn-outline-danger task-cancel-btn" data-task-id="${task.id}">
                    <i class="bi bi-x"></i> Cancel
                </button>
            `;
        } else if (task.status === 'in_progress' || task.status === 'assigned') {
            actionButtonsHtml = `
                <button class="btn btn-sm btn-warning task-pause-btn" data-task-id="${task.id}">
                    <i class="bi bi-pause-fill"></i> Pause
                </button>
                <button class="btn btn-sm btn-outline-danger task-cancel-btn" data-task-id="${task.id}">
                    <i class="bi bi-x"></i> Cancel
                </button>
            `;
        } else if (task.status === 'completed' || task.status === 'failed') {
            actionButtonsHtml = `
                <button class="btn btn-sm btn-primary task-rerun-btn" data-task-id="${task.id}">
                    <i class="bi bi-arrow-clockwise"></i> Re-Run
                </button>
                <button class="btn btn-sm btn-outline-secondary task-archive-btn" data-task-id="${task.id}">
                    <i class="bi bi-archive"></i> Archive
                </button>
            `;
        }
        
        // Set task detail content
        taskDetailContainer.innerHTML = `
            <div class="task-detail-header">
                <h5 class="task-detail-title">${task.title}</h5>
                <span class="badge ${statusBadgeClass}">${task.status}</span>
            </div>
            
            <div class="task-detail-description mt-3">
                <h6>Description</h6>
                <p>${task.description}</p>
            </div>
            
            <div class="task-detail-info mt-3">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Assignment</h6>
                        <p>${task.assigned_to ? formatAgentName(task.assigned_to) : 'Unassigned'}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Priority</h6>
                        <p>${formatPriority(task.priority)}</p>
                    </div>
                </div>
                
                <div class="row mt-2">
                    <div class="col-md-6">
                        <h6>Created</h6>
                        <p>${createdAt}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Last Updated</h6>
                        <p>${updatedAt}</p>
                    </div>
                </div>
                
                <div class="row mt-2">
                    <div class="col-md-6">
                        <h6>Started</h6>
                        <p>${startedAt}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Completed</h6>
                        <p>${completedAt}</p>
                    </div>
                </div>
            </div>
            
            ${subtasksHtml}
            
            ${resultHtml}
            
            <div class="task-detail-actions mt-4">
                ${actionButtonsHtml}
            </div>
        `;
        
        // Add event handlers for action buttons
        const executeBtn = taskDetailContainer.querySelector('.task-execute-btn');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => executeTask(task.id));
        }
        
        const cancelBtn = taskDetailContainer.querySelector('.task-cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => cancelTask(task.id));
        }
        
        const pauseBtn = taskDetailContainer.querySelector('.task-pause-btn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => pauseTask(task.id));
        }
        
        const rerunBtn = taskDetailContainer.querySelector('.task-rerun-btn');
        if (rerunBtn) {
            rerunBtn.addEventListener('click', () => rerunTask(task.id));
        }
        
        const archiveBtn = taskDetailContainer.querySelector('.task-archive-btn');
        if (archiveBtn) {
            archiveBtn.addEventListener('click', () => archiveTask(task.id));
        }
    }
    
    /**
     * Clear the task detail view
     */
    function clearTaskDetail() {
        if (!taskDetailContainer) {return;}
        
        // Hide the detail container
        taskDetailContainer.style.display = 'none';
        taskDetailContainer.innerHTML = '';
    }
    
    /**
     * Show the create task modal
     */
    function showCreateTaskModal() {
        // Create modal if it doesn't exist
        let modal = document.getElementById('create-task-modal');
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'create-task-modal';
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('aria-labelledby', 'create-task-modal-label');
            modal.setAttribute('aria-hidden', 'true');
            
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="create-task-modal-label">Create New Task</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="create-task-form">
                                <div class="mb-3">
                                    <label for="task-title" class="form-label">Task Title</label>
                                    <input type="text" class="form-control" id="task-title" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="task-description" class="form-label">Description</label>
                                    <textarea class="form-control" id="task-description" rows="3" required></textarea>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="task-priority" class="form-label">Priority</label>
                                    <select class="form-select" id="task-priority">
                                        <option value="1">Low</option>
                                        <option value="2">Medium-Low</option>
                                        <option value="3" selected>Medium</option>
                                        <option value="4">Medium-High</option>
                                        <option value="5">High</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="task-assigned-to" class="form-label">Assign To (Optional)</label>
                                    <select class="form-select" id="task-assigned-to">
                                        <option value="">Unassigned</option>
                                        <option value="architect">Architect</option>
                                        <!-- Worker options will be added dynamically -->
                                    </select>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="create-task-submit-btn">Create Task</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Add worker options
            getSessionWorkers().then(workers => {
                const assignSelect = document.getElementById('task-assigned-to');
                if (assignSelect && workers.length > 0) {
                    workers.forEach(worker => {
                        const option = document.createElement('option');
                        option.value = worker.name;
                        option.textContent = worker.name;
                        assignSelect.appendChild(option);
                    });
                }
            });
            
            // Add submit handler
            const submitBtn = document.getElementById('create-task-submit-btn');
            if (submitBtn) {
                submitBtn.addEventListener('click', createTask);
            }
        }
        
        // Show the modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
    
    /**
     * Get workers for the current session
     * @returns {Promise<Array>} Array of worker objects
     */
    async function getSessionWorkers() {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            if (!response.ok) {
                throw new Error(`Failed to get session details: ${response.status}`);
            }
            
            const sessionData = await response.json();
            return sessionData.config.workers || [];
        } catch (error) {
            console.error('Error getting session workers:', error);
            return [];
        }
    }
    
    /**
     * Create a new task
     */
    async function createTask() {
        const titleInput = document.getElementById('task-title');
        const descriptionInput = document.getElementById('task-description');
        const prioritySelect = document.getElementById('task-priority');
        const assignedToSelect = document.getElementById('task-assigned-to');
        
        if (!titleInput || !descriptionInput || !prioritySelect) {
            showToast('Form elements not found', 'danger');
            return;
        }
        
        const title = titleInput.value.trim();
        const description = descriptionInput.value.trim();
        const priority = parseInt(prioritySelect.value);
        const assignedTo = assignedToSelect?.value || null;
        
        if (!title || !description) {
            showToast('Please fill in all required fields', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/sessions/${sessionId}/tasks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    description,
                    priority,
                    assigned_to: assignedTo
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to create task: ${response.status}`);
            }
            
            const task = await response.json();
            
            // Close the modal
            const modal = document.getElementById('create-task-modal');
            if (modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
            
            // Reload tasks
            await loadTasks();
            
            // Select the new task
            selectTask(task.id);
            
            showToast('Task created successfully', 'success');
        } catch (error) {
            console.error('Error creating task:', error);
            showToast(`Error creating task: ${error.message}`, 'danger');
        }
    }
    
    /**
     * Execute a task
     * @param {string} taskId - Task ID
     */
    async function executeTask(taskId) {
        try {
            // Show confirmation
            const confirmed = confirm('Are you sure you want to execute this task?');
            if (!confirmed) {return;}
            
            // Show loading state
            const executeBtn = document.querySelector(`.task-execute-btn[data-task-id="${taskId}"]`);
            if (executeBtn) {
                executeBtn.disabled = true;
                executeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Executing...';
            }
            
            const response = await fetch(`/api/sessions/${sessionId}/tasks/${taskId}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_input: `Execute task: ${taskId}`
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to execute task: ${response.status}`);
            }
            
            // Reload tasks
            await loadTasks();
            
            showToast('Task execution started', 'success');
        } catch (error) {
            console.error('Error executing task:', error);
            showToast(`Error executing task: ${error.message}`, 'danger');
        } finally {
            // Reset button state
            const executeBtn = document.querySelector(`.task-execute-btn[data-task-id="${taskId}"]`);
            if (executeBtn) {
                executeBtn.disabled = false;
                executeBtn.innerHTML = '<i class="bi bi-play-fill"></i> Execute Task';
            }
        }
    }
    
    /**
     * Cancel a task
     * @param {string} taskId - Task ID
     */
    async function cancelTask(taskId) {
        try {
            // Show confirmation
            const confirmed = confirm('Are you sure you want to cancel this task?');
            if (!confirmed) {return;}
            
            const response = await fetch(`/api/sessions/${sessionId}/tasks/${taskId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: 'cancelled'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to cancel task: ${response.status}`);
            }
            
            // Reload tasks
            await loadTasks();
            
            showToast('Task cancelled', 'info');
        } catch (error) {
            console.error('Error cancelling task:', error);
            showToast(`Error cancelling task: ${error.message}`, 'danger');
        }
    }
    
    /**
     * Pause a task
     * @param {string} taskId - Task ID
     */
    async function pauseTask(taskId) {
        try {
            // Show confirmation
            const confirmed = confirm('Are you sure you want to pause this task?');
            if (!confirmed) {return;}
            
            const response = await fetch(`/api/sessions/${sessionId}/tasks/${taskId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: 'pending'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to pause task: ${response.status}`);
            }
            
            // Reload tasks
            await loadTasks();
            
            showToast('Task paused', 'warning');
        } catch (error) {
            console.error('Error pausing task:', error);
            showToast(`Error pausing task: ${error.message}`, 'danger');
        }
    }
    
    /**
     * Re-run a task
     * @param {string} taskId - Task ID
     */
    async function rerunTask(taskId) {
        try {
            // Show confirmation
            const confirmed = confirm('Are you sure you want to re-run this task?');
            if (!confirmed) {return;}
            
            // First reset the task status
            const resetResponse = await fetch(`/api/sessions/${sessionId}/tasks/${taskId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: 'pending',
                    result: null,
                    error: null
                })
            });
            
            if (!resetResponse.ok) {
                throw new Error(`Failed to reset task: ${resetResponse.status}`);
            }
            
            // Then execute it
            const executeResponse = await fetch(`/api/sessions/${sessionId}/tasks/${taskId}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_input: `Re-run task: ${taskId}`
                })
            });
            
            if (!executeResponse.ok) {
                throw new Error(`Failed to execute task: ${executeResponse.status}`);
            }
            
            // Reload tasks
            await loadTasks();
            
            showToast('Task re-run started', 'success');
        } catch (error) {
            console.error('Error re-running task:', error);
            showToast(`Error re-running task: ${error.message}`, 'danger');
        }
    }
    
    /**
     * Archive a task
     * @param {string} taskId - Task ID
     */
    async function archiveTask(taskId) {
        try {
            // Show confirmation
            const confirmed = confirm('Are you sure you want to archive this task? This will hide it from the active tasks list.');
            if (!confirmed) {return;}
            
            const response = await fetch(`/api/sessions/${sessionId}/tasks/${taskId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    metadata: { archived: true }
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to archive task: ${response.status}`);
            }
            
            // Reload tasks
            await loadTasks();
            
            // Clear task detail if this was the selected task
            if (selectedTaskId === taskId) {
                selectedTaskId = null;
                clearTaskDetail();
            }
            
            showToast('Task archived', 'info');
        } catch (error) {
            console.error('Error archiving task:', error);
            showToast(`Error archiving task: ${error.message}`, 'danger');
        }
    }
    
    /**
     * Format content with markdown-like syntax
     * @param {string} content - Content to format
     * @returns {string} Formatted HTML
     */
    function formatContent(content) {
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
     * Format agent name for display
     * @param {string} agentId - Agent ID
     * @returns {string} Formatted agent name
     */
    function formatAgentName(agentId) {
        if (!agentId) {return 'Unknown';}
        
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
     * Format datetime for display
     * @param {string} datetimeStr - ISO datetime string
     * @returns {string} Formatted datetime
     */
    function formatDateTime(datetimeStr) {
        if (!datetimeStr) {return '';}
        
        try {
            return dayjs(datetimeStr).format('MMM D, YYYY HH:mm:ss');
        } catch (_e) {
            return datetimeStr;
        }
    }
    
    /**
     * Format priority for display
     * @param {number} priority - Priority value (1-5)
     * @returns {string} Formatted priority
     */
    function formatPriority(priority) {
        switch (priority) {
            case 1: return 'Low';
            case 2: return 'Medium-Low';
            case 3: return 'Medium';
            case 4: return 'Medium-High';
            case 5: return 'High';
            default: return 'Medium';
        }
    }
    
    /**
     * Get badge class for task status
     * @param {string} status - Task status
     * @returns {string} Badge CSS class
     */
    function getStatusBadgeClass(status) {
        switch (status) {
            case 'completed': return 'bg-success';
            case 'in_progress': return 'bg-primary';
            case 'assigned': return 'bg-info';
            case 'failed': return 'bg-danger';
            case 'cancelled': return 'bg-dark';
            default: return 'bg-secondary';
        }
    }
    
    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Bootstrap context class
     */
    function showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast show text-white bg-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Task Manager</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    // Initial load
    loadTasks();
    
    // Set up WebSocket for task updates
    if (typeof createSessionWebSocket === 'function') {
        const ws = createSessionWebSocket(sessionId);
        
        ws.on('onTasks', function({ tasks: _updatedTasks }) {
            // Refresh task list
            loadTasks();
        });
        
        ws.connect();
    }
    
    // Return public API
    return {
        loadTasks,
        createTask,
        executeTask,
        selectTask
    };
}

    // Public API
    return {
        initTaskManager
    };
})();

// Expose function globally for backward compatibility
window.initTaskManager = window.TaskManager.initTaskManager;
