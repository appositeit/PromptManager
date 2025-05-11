/**
 * Task Visualizer
 * 
 * This module provides visualization components for task graphs, timelines,
 * and other real-time session visualizations using D3.js.
 */

/**
 * Task Graph Visualizer
 * 
 * Visualizes tasks and their relationships as a graph using D3.js force layout.
 */
class TaskGraphVisualizer {
    /**
     * Create a new Task Graph Visualizer.
     * 
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Configuration options
     */
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // Configuration
        this.options = {
            width: options.width || this.container.clientWidth || 800,
            height: options.height || this.container.clientHeight || 600,
            nodeRadius: options.nodeRadius || 20,
            linkDistance: options.linkDistance || 100,
            linkStrength: options.linkStrength || 0.2,
            chargeStrength: options.chargeStrength || -300,
            centerStrength: options.centerStrength || 0.1,
            ...options
        };
        
        // Data
        this.nodes = [];
        this.links = [];
        
        // D3 elements
        this.svg = null;
        this.simulation = null;
        this.linkElements = null;
        this.nodeElements = null;
        this.textElements = null;
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the visualization.
     */
    initialize() {
        // Create SVG
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height);
        
        // Define arrowhead marker
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('xoverflow', 'visible')
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke', 'none');
        
        // Create links group
        this.linkElements = this.svg.append('g')
            .attr('class', 'links')
            .selectAll('line');
        
        // Create nodes group
        this.nodeElements = this.svg.append('g')
            .attr('class', 'nodes')
            .selectAll('circle');
        
        // Create text group
        this.textElements = this.svg.append('g')
            .attr('class', 'texts')
            .selectAll('text');
        
        // Create simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(this.options.linkDistance).strength(this.options.linkStrength))
            .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2).strength(this.options.centerStrength))
            .on('tick', () => this.ticked());
    }
    
    /**
     * Update the visualization with new data.
     * 
     * @param {Object} data - Visualization data
     * @param {Array} data.agents - Array of agent objects
     * @param {Array} data.tasks - Array of task objects
     */
    update(data) {
        if (!data) return;
        
        // Process agents
        const agents = (data.agents || []).map(agent => ({
            id: agent.id,
            name: agent.name,
            type: 'agent',
            status: agent.status || 'idle',
            capabilities: agent.capabilities || []
        }));
        
        // Process tasks
        const tasks = (data.tasks || []).map(task => ({
            id: task.id,
            name: task.title || 'Unnamed Task',
            type: 'task',
            status: task.status || 'pending',
            assignedTo: task.assigned_to,
            parentId: task.parent_id
        }));
        
        // Combine nodes
        this.nodes = [...agents, ...tasks];
        
        // Create links
        this.links = [];
        
        // Add task parent links
        tasks.forEach(task => {
            if (task.parentId) {
                this.links.push({
                    source: task.parentId,
                    target: task.id,
                    type: 'parent-child'
                });
            }
        });
        
        // Add agent assignment links
        tasks.forEach(task => {
            if (task.assignedTo) {
                this.links.push({
                    source: task.assignedTo,
                    target: task.id,
                    type: 'assignment'
                });
            }
        });
        
        // Update visualization
        this.updateVisualization();
    }
    
    /**
     * Update the visualization elements.
     */
    updateVisualization() {
        // Update links
        this.linkElements = this.linkElements
            .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`)
            .join(
                enter => enter.append('line')
                    .attr('stroke-width', d => d.type === 'parent-child' ? 2 : 1)
                    .attr('stroke', d => d.type === 'parent-child' ? '#333' : '#999')
                    .attr('stroke-dasharray', d => d.type === 'assignment' ? '5,5' : 'none')
                    .attr('marker-end', 'url(#arrowhead)'),
                update => update
                    .attr('stroke-width', d => d.type === 'parent-child' ? 2 : 1)
                    .attr('stroke', d => d.type === 'parent-child' ? '#333' : '#999')
                    .attr('stroke-dasharray', d => d.type === 'assignment' ? '5,5' : 'none'),
                exit => exit.remove()
            );
        
        // Update nodes
        this.nodeElements = this.nodeElements
            .data(this.nodes, d => d.id)
            .join(
                enter => enter.append('circle')
                    .attr('r', d => d.type === 'agent' ? this.options.nodeRadius * 1.2 : this.options.nodeRadius)
                    .attr('fill', d => this.getNodeColor(d))
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 2)
                    .call(this.setupDragListeners())
                    .on('click', (event, d) => this.onNodeClick(d))
                    .append('title')
                    .text(d => d.name),
                update => update
                    .attr('fill', d => this.getNodeColor(d))
                    .select('title')
                    .text(d => d.name),
                exit => exit.remove()
            );
        
        // Update text labels
        this.textElements = this.textElements
            .data(this.nodes, d => d.id)
            .join(
                enter => enter.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('alignment-baseline', 'middle')
                    .text(d => this.getNodeLabel(d))
                    .style('fill', d => d.type === 'agent' ? '#fff' : '#000')
                    .style('font-weight', d => d.type === 'agent' ? 'bold' : 'normal')
                    .style('font-size', d => d.type === 'agent' ? '10px' : '8px')
                    .style('pointer-events', 'none'),
                update => update
                    .text(d => this.getNodeLabel(d))
                    .style('fill', d => d.type === 'agent' ? '#fff' : '#000'),
                exit => exit.remove()
            );
        
        // Update simulation
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        this.simulation.alpha(0.5).restart();
    }
    
    /**
     * Handle simulation tick.
     */
    ticked() {
        // Update link positions
        this.linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        // Update node positions
        this.nodeElements
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        // Update text positions
        this.textElements
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
    
    /**
     * Set up drag listeners for nodes.
     */
    setupDragListeners() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    /**
     * Get color for a node based on its type and status.
     * 
     * @param {Object} node - Node object
     * @returns {string} Color
     */
    getNodeColor(node) {
        if (node.type === 'agent') {
            // Agent colors
            switch (node.status) {
                case 'active': return '#4CAF50';
                case 'busy': return '#FF9800';
                case 'error': return '#F44336';
                default: return '#2196F3';
            }
        } else {
            // Task colors
            switch (node.status) {
                case 'pending': return '#FFEB3B';
                case 'assigned': return '#FFC107';
                case 'in_progress': return '#FF9800';
                case 'completed': return '#4CAF50';
                case 'failed': return '#F44336';
                default: return '#E0E0E0';
            }
        }
    }
    
    /**
     * Get label for a node.
     * 
     * @param {Object} node - Node object
     * @returns {string} Label
     */
    getNodeLabel(node) {
        if (node.type === 'agent') {
            return node.name.substring(0, 1).toUpperCase();
        } else {
            return '';
        }
    }
    
    /**
     * Handle node click.
     * 
     * @param {Object} node - Node object
     */
    onNodeClick(node) {
        // Dispatch event
        const event = new CustomEvent('node-click', {
            detail: {
                node: node
            }
        });
        
        this.container.dispatchEvent(event);
    }
    
    /**
     * Resize the visualization.
     * 
     * @param {number} width - New width
     * @param {number} height - New height
     */
    resize(width, height) {
        // Update size
        this.options.width = width || this.container.clientWidth || 800;
        this.options.height = height || this.container.clientHeight || 600;
        
        // Update SVG
        this.svg
            .attr('width', this.options.width)
            .attr('height', this.options.height);
        
        // Update simulation
        this.simulation
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2).strength(this.options.centerStrength))
            .alpha(0.5)
            .restart();
    }
}

/**
 * Task Timeline Visualizer
 * 
 * Visualizes tasks as a timeline using D3.js.
 */
class TaskTimelineVisualizer {
    /**
     * Create a new Task Timeline Visualizer.
     * 
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Configuration options
     */
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // Configuration
        this.options = {
            width: options.width || this.container.clientWidth || 800,
            height: options.height || this.container.clientHeight || 500,
            margin: options.margin || { top: 50, right: 50, bottom: 50, left: 150 },
            barHeight: options.barHeight || 20,
            barSpacing: options.barSpacing || 10,
            ...options
        };
        
        // Data
        this.tasks = [];
        this.agents = [];
        this.timeRange = [new Date(), new Date()];
        
        // D3 elements
        this.svg = null;
        this.xScale = null;
        this.yScale = null;
        this.xAxis = null;
        this.yAxis = null;
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the visualization.
     */
    initialize() {
        // Create SVG
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height);
        
        // Create groups
        this.axisGroup = this.svg.append('g')
            .attr('class', 'axis');
        
        this.barsGroup = this.svg.append('g')
            .attr('class', 'bars')
            .attr('transform', `translate(${this.options.margin.left}, ${this.options.margin.top})`);
            
        // Initialize scales
        this.xScale = d3.scaleTime()
            .range([0, this.options.width - this.options.margin.left - this.options.margin.right]);
            
        this.yScale = d3.scaleBand()
            .range([0, this.options.height - this.options.margin.top - this.options.margin.bottom])
            .padding(0.1);
            
        // Initialize axes
        this.xAxis = d3.axisTop(this.xScale);
        this.yAxis = d3.axisLeft(this.yScale);
        
        // Append axes
        this.axisGroup.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(${this.options.margin.left}, ${this.options.margin.top})`);
            
        this.axisGroup.append('g')
            .attr('class', 'y-axis')
            .attr('transform', `translate(${this.options.margin.left}, ${this.options.margin.top})`);
    }
    
    /**
     * Update the visualization with new data.
     * 
     * @param {Object} data - Visualization data
     * @param {Array} data.agents - Array of agent objects
     * @param {Array} data.tasks - Array of task objects
     */
    update(data) {
        if (!data) return;
        
        // Process agents
        this.agents = (data.agents || []).map(agent => ({
            id: agent.id,
            name: agent.name,
            status: agent.status || 'idle'
        }));
        
        // Process tasks
        this.tasks = (data.tasks || []).filter(task => task.start_time || task.created_at).map(task => {
            const startTime = task.start_time ? new Date(task.start_time) : new Date(task.created_at);
            const endTime = task.end_time ? new Date(task.end_time) : task.completed_at ? new Date(task.completed_at) : new Date();
            
            return {
                id: task.id,
                title: task.title || 'Unnamed Task',
                description: task.description || '',
                status: task.status || 'pending',
                assignedTo: task.assigned_to,
                startTime: startTime,
                endTime: endTime,
                duration: endTime - startTime
            };
        });
        
        // Calculate time range
        if (this.tasks.length > 0) {
            const startTimes = this.tasks.map(task => task.startTime);
            const endTimes = this.tasks.map(task => task.endTime);
            
            // Allow for a small buffer on either side
            const minTime = new Date(Math.min(...startTimes));
            minTime.setMinutes(minTime.getMinutes() - 5);
            
            const maxTime = new Date(Math.max(...endTimes));
            maxTime.setMinutes(maxTime.getMinutes() + 5);
            
            this.timeRange = [minTime, maxTime];
        }
        
        // Update visualization
        this.updateVisualization();
    }
    
    /**
     * Update the visualization elements.
     */
    updateVisualization() {
        // Update scales
        this.xScale.domain(this.timeRange);
        
        // Create task labels for y-axis
        const taskLabels = this.tasks.map(task => {
            const agent = this.agents.find(a => a.id === task.assignedTo);
            return `${task.title} (${agent ? agent.name : 'Unassigned'})`;
        });
        
        this.yScale.domain(taskLabels);
        
        // Update axes
        this.axisGroup.select('.x-axis')
            .call(this.xAxis);
            
        this.axisGroup.select('.y-axis')
            .call(this.yAxis);
        
        // Update task bars
        const taskBars = this.barsGroup.selectAll('.task-bar')
            .data(this.tasks, d => d.id);
            
        // Exit
        taskBars.exit().remove();
        
        // Enter
        const taskBarsEnter = taskBars.enter()
            .append('g')
            .attr('class', 'task-bar')
            .attr('transform', (d, i) => {
                const agent = this.agents.find(a => a.id === d.assignedTo);
                const label = `${d.title} (${agent ? agent.name : 'Unassigned'})`;
                return `translate(0, ${this.yScale(label)})`;
            });
            
        // Add rectangles
        taskBarsEnter.append('rect')
            .attr('x', d => this.xScale(d.startTime))
            .attr('y', 0)
            .attr('width', d => Math.max(this.xScale(d.endTime) - this.xScale(d.startTime), 3))
            .attr('height', this.yScale.bandwidth())
            .attr('fill', d => this.getTaskColor(d))
            .attr('rx', 3)
            .attr('ry', 3)
            .on('click', (event, d) => this.onTaskClick(d))
            .append('title')
            .text(d => `${d.title}\nStatus: ${d.status}\nDuration: ${this.formatDuration(d.duration)}`);
            
        // Update
        taskBars.select('rect')
            .attr('x', d => this.xScale(d.startTime))
            .attr('width', d => Math.max(this.xScale(d.endTime) - this.xScale(d.startTime), 3))
            .attr('fill', d => this.getTaskColor(d))
            .select('title')
            .text(d => `${d.title}\nStatus: ${d.status}\nDuration: ${this.formatDuration(d.duration)}`);
    }
    
    /**
     * Get color for a task based on its status.
     * 
     * @param {Object} task - Task object
     * @returns {string} Color
     */
    getTaskColor(task) {
        switch (task.status) {
            case 'pending': return '#FFEB3B';
            case 'assigned': return '#FFC107';
            case 'in_progress': return '#FF9800';
            case 'completed': return '#4CAF50';
            case 'failed': return '#F44336';
            default: return '#E0E0E0';
        }
    }
    
    /**
     * Format duration in milliseconds to a readable string.
     * 
     * @param {number} duration - Duration in milliseconds
     * @returns {string} Formatted duration
     */
    formatDuration(duration) {
        const seconds = Math.floor(duration / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }
    
    /**
     * Handle task click.
     * 
     * @param {Object} task - Task object
     */
    onTaskClick(task) {
        // Dispatch event
        const event = new CustomEvent('task-click', {
            detail: {
                task: task
            }
        });
        
        this.container.dispatchEvent(event);
    }
    
    /**
     * Resize the visualization.
     * 
     * @param {number} width - New width
     * @param {number} height - New height
     */
    resize(width, height) {
        // Update size
        this.options.width = width || this.container.clientWidth || 800;
        this.options.height = height || this.container.clientHeight || 500;
        
        // Update SVG
        this.svg
            .attr('width', this.options.width)
            .attr('height', this.options.height);
        
        // Update scales
        this.xScale.range([0, this.options.width - this.options.margin.left - this.options.margin.right]);
        this.yScale.range([0, this.options.height - this.options.margin.top - this.options.margin.bottom]);
        
        // Update visualization
        this.updateVisualization();
    }
}
