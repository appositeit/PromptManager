/**
 * Task Graph Visualization for the Coordinator System
 * 
 * This module provides visualization of task dependencies and agent interactions
 * using a directed graph representation.
 */

class TaskGraphVisualizer {
    /**
     * Initialize a new task graph visualizer.
     * 
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Visualization options
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }
        
        // Set default options
        this.options = {
            width: options.width || this.container.clientWidth || 800,
            height: options.height || 500,
            nodeRadius: options.nodeRadius || 10,
            linkDistance: options.linkDistance || 100,
            chargeStrength: options.chargeStrength || -300,
            colors: options.colors || {
                architect: "#6610f2",
                worker: "#007bff",
                task: {
                    pending: "#6c757d",
                    executing: "#fd7e14",
                    completed: "#28a745",
                    failed: "#dc3545"
                },
                message: {
                    task_request: "#007bff",
                    task_result: "#28a745",
                    question: "#6c757d",
                    answer: "#17a2b8"
                }
            },
            animationDuration: options.animationDuration || 500,
            ...options
        };
        
        // Initialize the SVG element
        this.svg = d3.select(this.container)
            .append("svg")
            .attr("width", this.options.width)
            .attr("height", this.options.height)
            .attr("class", "task-graph-svg");
            
        // Add zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                this.rootGroup.attr("transform", event.transform);
            });
            
        this.svg.call(this.zoom);
        
        // Create root group for zooming
        this.rootGroup = this.svg.append("g");
        
        // Create arrow marker definition
        this.rootGroup.append("defs")
            .append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");
            
        // Create groups for links and nodes
        this.linkGroup = this.rootGroup.append("g").attr("class", "links");
        this.nodeGroup = this.rootGroup.append("g").attr("class", "nodes");
        
        // Initialize data arrays
        this.nodes = [];
        this.links = [];
        
        // Initialize simulation
        this.simulation = null;
        this.initializeSimulation();
        
        // Add legend
        this.addLegend();
        
        // Add controls
        this.addControls();
        
        // Event handler for window resize
        window.addEventListener("resize", () => {
            this.resize();
        });
    }
    
    /**
     * Initialize the force simulation.
     */
    initializeSimulation() {
        this.simulation = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.id).distance(this.options.linkDistance))
            .force("charge", d3.forceManyBody().strength(this.options.chargeStrength))
            .force("center", d3.forceCenter(this.options.width / 2, this.options.height / 2))
            .on("tick", () => {
                this.updatePositions();
            });
    }
    
    /**
     * Add visualization controls.
     */
    addControls() {
        const controlPanel = d3.select(this.container)
            .append("div")
            .attr("class", "task-graph-controls")
            .style("position", "absolute")
            .style("top", "10px")
            .style("right", "10px")
            .style("z-index", "100");
            
        // Zoom controls
        const zoomControls = controlPanel.append("div")
            .attr("class", "btn-group btn-group-sm");
            
        zoomControls.append("button")
            .attr("class", "btn btn-outline-secondary")
            .attr("title", "Zoom In")
            .html('<i class="bi bi-zoom-in"></i>')
            .on("click", () => {
                this.svg.transition().duration(300).call(this.zoom.scaleBy, 1.2);
            });
            
        zoomControls.append("button")
            .attr("class", "btn btn-outline-secondary")
            .attr("title", "Zoom Out")
            .html('<i class="bi bi-zoom-out"></i>')
            .on("click", () => {
                this.svg.transition().duration(300).call(this.zoom.scaleBy, 0.8);
            });
            
        zoomControls.append("button")
            .attr("class", "btn btn-outline-secondary")
            .attr("title", "Reset View")
            .html('<i class="bi bi-arrows-fullscreen"></i>')
            .on("click", () => {
                this.svg.transition().duration(500).call(
                    this.zoom.transform,
                    d3.zoomIdentity.translate(this.options.width / 2, this.options.height / 2)
                        .scale(1)
                        .translate(-this.options.width / 2, -this.options.height / 2)
                );
            });
    }
    
    /**
     * Add a legend for the visualization.
     */
    addLegend() {
        const legend = this.svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(20, 20)`);
            
        // Agent types
        const agentTypes = [
            { type: "architect", label: "Architect" },
            { type: "worker", label: "Worker" }
        ];
        
        agentTypes.forEach((item, i) => {
            const g = legend.append("g")
                .attr("transform", `translate(0, ${i * 25})`);
                
            g.append("circle")
                .attr("r", 6)
                .attr("fill", this.options.colors[item.type]);
                
            g.append("text")
                .attr("x", 15)
                .attr("y", 5)
                .text(item.label)
                .attr("font-size", "12px");
        });
        
        // Task statuses
        const taskStatuses = [
            { status: "pending", label: "Pending Task" },
            { status: "executing", label: "Executing Task" },
            { status: "completed", label: "Completed Task" },
            { status: "failed", label: "Failed Task" }
        ];
        
        taskStatuses.forEach((item, i) => {
            const g = legend.append("g")
                .attr("transform", `translate(120, ${i * 25})`);
                
            g.append("rect")
                .attr("width", 12)
                .attr("height", 12)
                .attr("x", -6)
                .attr("y", -6)
                .attr("fill", this.options.colors.task[item.status]);
                
            g.append("text")
                .attr("x", 15)
                .attr("y", 5)
                .text(item.label)
                .attr("font-size", "12px");
        });
    }
    
    /**
     * Update the visualization with new data.
     * 
     * @param {Object} data - Task graph data
     */
    update(data) {
        if (!data) {return;}
        
        // Extract nodes and links from the data
        const { nodes, links } = this.processData(data);
        
        // Update the data arrays
        this.nodes = nodes;
        this.links = links;
        
        // Update the simulation
        this.updateSimulation();
        
        // Update the visualization
        this.render();
    }
    
    /**
     * Process the data into nodes and links for the visualization.
     * 
     * @param {Object} data - Task graph data
     * @returns {Object} Object with nodes and links arrays
     */
    processData(data) {
        const nodes = [];
        const links = [];
        
        // Process agents
        if (data.agents) {
            data.agents.forEach(agent => {
                nodes.push({
                    id: agent.id,
                    name: agent.name || agent.id,
                    isAgent: true
                });
            });
        }
        
        // Process tasks
        if (data.tasks) {
            data.tasks.forEach(task => {
                nodes.push({
                    id: task.id,
                    name: task.title || task.id,
                    status: task.status || "pending",
                    description: task.description,
                    isTask: true
                });
                
                // Add links for parent-child task relationships
                if (task.parent_id) {
                    links.push({
                        source: task.parent_id,
                        target: task.id,
                        type: "task_hierarchy"
                    });
                }
                
                // Add links for task assignments
                if (task.assigned_to) {
                    links.push({
                        source: task.assigned_to,
                        target: task.id,
                        type: "task_assignment"
                    });
                }
            });
        }
        
        // Process messages (optional for more detailed visualization)
        if (data.messages) {
            data.messages.forEach(message => {
                // Only add links for certain message types
                if (['task_request', 'task_result', 'question', 'answer'].includes(message.message_type)) {
                    links.push({
                        source: message.from_agent,
                        target: message.to_agent,
                        type: message.message_type,
                        id: message.id,
                        isMessage: true
                    });
                }
            });
        }
        
        return { nodes, links };
    }
    
    /**
     * Update the force simulation with new data.
     */
    updateSimulation() {
        if (!this.simulation) {return;}
        
        this.simulation.nodes(this.nodes);
        this.simulation.force("link").links(this.links);
        this.simulation.alpha(1).restart();
    }
    
    /**
     * Render the visualization.
     */
    render() {
        // Render links
        const link = this.linkGroup
            .selectAll(".link")
            .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}-${d.type}`);
            
        link.exit().transition().duration(this.options.animationDuration)
            .attr("stroke-opacity", 0)
            .remove();
            
        const linkEnter = link.enter().append("line")
            .attr("class", "link")
            .attr("stroke", d => {
                if (d.type && d.type in this.options.colors.message) {
                    return this.options.colors.message[d.type];
                }
                return "#999";
            })
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", d => d.isMessage ? 2 : 1)
            .attr("marker-end", "url(#arrowhead)");
            
        // Render nodes
        const node = this.nodeGroup
            .selectAll(".node")
            .data(this.nodes, d => d.id);
            
        node.exit().transition().duration(this.options.animationDuration)
            .attr("r", 0)
            .remove();
            
        const nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", this.dragstarted.bind(this))
                .on("drag", this.dragged.bind(this))
                .on("end", this.dragended.bind(this))
            );
            
        // Add node shapes based on type
        nodeEnter.each(function(d) {
            const element = d3.select(this);
            
            if (d.isAgent) {
                // Agents are circles
                element.append("circle")
                    .attr("r", 15)
                    .attr("fill", d => d.name === "architect" ? 
                        this.options.colors.architect : 
                        this.options.colors.worker
                    )
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 2);
            } else if (d.isTask) {
                // Tasks are rectangles
                element.append("rect")
                    .attr("width", 20)
                    .attr("height", 20)
                    .attr("x", -10)
                    .attr("y", -10)
                    .attr("fill", d => {
                        const status = d.status || "pending";
                        return this.options.colors.task[status];
                    })
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 1.5);
            } else {
                // Default is a small circle
                element.append("circle")
                    .attr("r", 5)
                    .attr("fill", "#999");
            }
        }.bind(this));
        
        // Add node labels
        nodeEnter.append("text")
            .attr("dy", d => d.isAgent ? -20 : -15)
            .attr("text-anchor", "middle")
            .attr("font-size", "12px")
            .text(d => d.name || d.id);
            
        // Add tooltips
        nodeEnter.append("title")
            .text(d => {
                if (d.isAgent) {
                    return `${d.name} (${d.name})`;
                } else if (d.isTask) {
                    return `${d.name}\nStatus: ${d.status}\n${d.description || ""}`;
                }
                return d.id;
            });
            
        // Update existing nodes
        node.select("circle")
            .transition().duration(this.options.animationDuration)
            .attr("fill", d => {
                if (d.isAgent) {
                    return d.name === "architect" ? 
                        this.options.colors.architect : 
                        this.options.colors.worker;
                }
                return "#999";
            });
            
        node.select("rect")
            .transition().duration(this.options.animationDuration)
            .attr("fill", d => {
                if (d.isTask) {
                    const status = d.status || "pending";
                    return this.options.colors.task[status];
                }
                return "#999";
            });
            
        // Update tooltips
        node.select("title")
            .text(d => {
                if (d.isAgent) {
                    return `${d.name} (${d.name})`;
                } else if (d.isTask) {
                    return `${d.name}\nStatus: ${d.status}\n${d.description || ""}`;
                }
                return d.id;
            });
    }
    
    /**
     * Update node and link positions on simulation tick.
     */
    updatePositions() {
        this.linkGroup.selectAll(".link")
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
            
        this.nodeGroup.selectAll(".node")
            .attr("transform", d => `translate(${d.x}, ${d.y})`);
    }
    
    /**
     * Handle start of node drag.
     */
    dragstarted(event, d) {
        if (!event.active) {this.simulation.alphaTarget(0.3).restart();}
        d.fx = d.x;
        d.fy = d.y;
    }
    
    /**
     * Handle node drag.
     */
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    /**
     * Handle end of node drag.
     */
    dragended(event, d) {
        if (!event.active) {this.simulation.alphaTarget(0);}
        d.fx = null;
        d.fy = null;
    }
    
    /**
     * Resize the visualization.
     */
    resize() {
        const width = this.container.clientWidth || this.options.width;
        const height = this.container.clientHeight || this.options.height;
        
        this.svg
            .attr("width", width)
            .attr("height", height);
            
        this.options.width = width;
        this.options.height = height;
        
        this.simulation
            .force("center", d3.forceCenter(width / 2, height / 2))
            .alpha(0.3)
            .restart();
    }
    
    /**
     * Filter the visualization.
     * 
     * @param {Object} filters - Filter criteria
     */
    filter(filters) {
        // Implementation for filtering the visualization
        // This would allow showing/hiding specific node types or statuses
    }
}

/**
 * Task Timeline Visualizer for showing task execution over time.
 */
class TaskTimelineVisualizer {
    /**
     * Initialize a new task timeline visualizer.
     * 
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Visualization options
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }
        
        // Set default options
        this.options = {
            width: options.width || this.container.clientWidth || 800,
            height: options.height || 300,
            margin: options.margin || { top: 40, right: 20, bottom: 50, left: 100 },
            colors: options.colors || {
                task: {
                    pending: "#6c757d",
                    executing: "#fd7e14",
                    completed: "#28a745",
                    failed: "#dc3545"
                }
            },
            animationDuration: options.animationDuration || 500,
            ...options
        };
        
        // Initialize the SVG element
        this.svg = d3.select(this.container)
            .append("svg")
            .attr("width", this.options.width)
            .attr("height", this.options.height)
            .attr("class", "task-timeline-svg");
            
        // Create root group for margins
        this.rootGroup = this.svg.append("g")
            .attr("transform", `translate(${this.options.margin.left}, ${this.options.margin.top})`);
            
        // Create plot area
        this.plotWidth = this.options.width - this.options.margin.left - this.options.margin.right;
        this.plotHeight = this.options.height - this.options.margin.top - this.options.margin.bottom;
        
        // Create groups for different visualization elements
        this.axisGroup = this.rootGroup.append("g").attr("class", "axis");
        this.taskGroup = this.rootGroup.append("g").attr("class", "tasks");
        
        // Initialize scales
        this.xScale = d3.scaleTime().range([0, this.plotWidth]);
        this.yScale = d3.scaleBand().range([0, this.plotHeight]).padding(0.2);
        
        // Initialize data
        this.tasks = [];
        
        // Add event handler for window resize
        window.addEventListener("resize", () => {
            this.resize();
        });
    }
    
    /**
     * Update the visualization with new data.
     * 
     * @param {Object} data - Timeline data
     */
    update(data) {
        if (!data || !data.tasks) {return;}
        
        // Process the data
        this.tasks = this.processData(data.tasks);
        
        // Update scales
        this.updateScales();
        
        // Render the visualization
        this.render();
    }
    
    /**
     * Process the task data for the timeline.
     * 
     * @param {Array} tasks - Task data
     * @returns {Array} Processed tasks with time information
     */
    processData(tasks) {
        // Process tasks for timeline visualization
        const processedTasks = tasks.map(task => {
            // Create a timeline object for the task
            return {
                id: task.id,
                name: task.title || task.id,
                status: task.status || "pending",
                startTime: task.start_time ? new Date(task.start_time) : new Date(),
                endTime: task.end_time ? new Date(task.end_time) : new Date(Date.now() + 3600000), // Default to now + 1 hour
                duration: task.duration || 3600000, // Default to 1 hour in ms
                description: task.description || "",
                parent_id: task.parent_id || null
            };
        });
        
        // Sort tasks by start time
        processedTasks.sort((a, b) => a.startTime - b.startTime);
        
        return processedTasks;
    }
    
    /**
     * Update scales based on the current data.
     */
    updateScales() {
        // Update x scale (time)
        const timeExtent = d3.extent(this.tasks.flatMap(task => [task.startTime, task.endTime]));
        this.xScale.domain(timeExtent);
        
        // Update y scale (tasks)
        this.yScale.domain(this.tasks.map(task => task.id));
    }
    
    /**
     * Render the timeline visualization.
     */
    render() {
        // Create x axis
        const xAxis = d3.axisBottom(this.xScale);
        
        this.axisGroup.selectAll(".x-axis").remove();
        this.axisGroup.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0, ${this.plotHeight})`)
            .call(xAxis);
            
        // Create y axis
        const yAxis = d3.axisLeft(this.yScale)
            .tickFormat(d => {
                const task = this.tasks.find(t => t.id === d);
                return task ? task.name : d;
            });
            
        this.axisGroup.selectAll(".y-axis").remove();
        this.axisGroup.append("g")
            .attr("class", "y-axis")
            .call(yAxis);
            
        // Render task bars
        const taskBars = this.taskGroup
            .selectAll(".task-bar")
            .data(this.tasks, d => d.id);
            
        taskBars.exit().remove();
        
        const taskBarsEnter = taskBars.enter()
            .append("g")
            .attr("class", "task-bar")
            .attr("transform", d => `translate(0, ${this.yScale(d.id)})`);
            
        // Add task rectangles
        taskBarsEnter.append("rect")
            .attr("x", d => this.xScale(d.startTime))
            .attr("width", d => Math.max(2, this.xScale(d.endTime) - this.xScale(d.startTime)))
            .attr("height", this.yScale.bandwidth())
            .attr("fill", d => this.options.colors.task[d.status])
            .attr("stroke", "#fff")
            .attr("stroke-width", 1);
            
        // Add tooltips
        taskBarsEnter.append("title")
            .text(d => `${d.name}\nStatus: ${d.status}\nStart: ${d.startTime.toLocaleString()}\nEnd: ${d.endTime.toLocaleString()}\n${d.description}`);
            
        // Update existing task bars
        taskBars.select("rect")
            .transition().duration(this.options.animationDuration)
            .attr("x", d => this.xScale(d.startTime))
            .attr("width", d => Math.max(2, this.xScale(d.endTime) - this.xScale(d.startTime)))
            .attr("fill", d => this.options.colors.task[d.status]);
            
        taskBars.select("title")
            .text(d => `${d.name}\nStatus: ${d.status}\nStart: ${d.startTime.toLocaleString()}\nEnd: ${d.endTime.toLocaleString()}\n${d.description}`);
    }
    
    /**
     * Resize the visualization.
     */
    resize() {
        const width = this.container.clientWidth || this.options.width;
        
        this.svg.attr("width", width);
        this.options.width = width;
        this.plotWidth = width - this.options.margin.left - this.options.margin.right;
        this.xScale.range([0, this.plotWidth]);
        
        this.render();
    }
}

// Export the visualizers
window.TaskGraphVisualizer = TaskGraphVisualizer;
window.TaskTimelineVisualizer = TaskTimelineVisualizer;
