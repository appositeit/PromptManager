// Collapsible sidebar and directory prompts functionality

// State management for sidebar collapse states
const sidebarState = {
    metadata: true,
    directoryPrompts: true,
    dependencies: true,
    referencedBy: true,
    markdownCheat: true
};

// Load sidebar state from sessionStorage
function loadSidebarState() {
    const saved = sessionStorage.getItem('promptEditorSidebarState');
    if (saved) {
        try {
            Object.assign(sidebarState, JSON.parse(saved));
        } catch (e) {
            console.warn('Failed to parse saved sidebar state:', e);
        }
    }
}

// Save sidebar state to sessionStorage
function saveSidebarState() {
    sessionStorage.setItem('promptEditorSidebarState', JSON.stringify(sidebarState));
}

// Initialize collapsible sidebar functionality
function initializeCollapsibleSidebar() {
    loadSidebarState();
    
    // Set initial states based on saved preferences
    Object.entries(sidebarState).forEach(([key, isExpanded]) => {
        const collapseId = `${key.replace(/([A-Z])/g, '-$1').toLowerCase()}-collapse`;
        const collapseElement = document.getElementById(collapseId);
        const button = document.querySelector(`[data-bs-target="#${collapseId}"]`);
        
        if (collapseElement && button) {
            if (isExpanded) {
                collapseElement.classList.add('show');
                button.setAttribute('aria-expanded', 'true');
                button.querySelector('i').classList.remove('bi-chevron-down');
                button.querySelector('i').classList.add('bi-chevron-up');
            } else {
                collapseElement.classList.remove('show');
                button.setAttribute('aria-expanded', 'false');
                button.querySelector('i').classList.remove('bi-chevron-up');
                button.querySelector('i').classList.add('bi-chevron-down');
            }
        }
    });
    
    // Add event listeners for state changes
    document.querySelectorAll('.sidebar-collapse-btn').forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-bs-target');
            const key = target.replace('#', '').replace('-collapse', '').replace(/-([a-z])/g, (g) => g[1].toUpperCase());
            
            // Update state when collapse is toggled
            setTimeout(() => {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                sidebarState[key] = isExpanded;
                saveSidebarState();
            }, 50);
        });
    });
}

// Load and display directory prompts
function loadDirectoryPrompts() {
    const directoryPromptsDiv = document.getElementById('directory-prompts');
    if (!directoryPromptsDiv || !currentPromptData || !currentPromptData.directory_info) {
        return;
    }
    
    const currentDirectory = currentPromptData.directory_info.path;
    
    // Show loading state
    directoryPromptsDiv.innerHTML = '<p class="text-muted small">Loading directory prompts...</p>';
    
    // Fetch prompts in the same directory
    fetch(`/api/prompts/directories/${encodeURIComponent(currentDirectory)}/prompts`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load directory prompts: ${response.status}`);
            }
            return response.json();
        })
        .then(prompts => {
            // Filter out the current prompt and sort alphabetically
            const otherPrompts = prompts
                .filter(prompt => prompt.id !== promptId)
                .sort((a, b) => {
                    const nameA = prompt.display_name || prompt.name || prompt.id;
                    const nameB = prompt.display_name || prompt.name || prompt.id;
                    return nameA.localeCompare(nameB);
                });
            
            if (otherPrompts.length === 0) {
                directoryPromptsDiv.innerHTML = '<p class="text-muted small">No other prompts in this directory.</p>';
                return;
            }
            
            // Create prompt items with drag functionality
            directoryPromptsDiv.innerHTML = '';
            otherPrompts.forEach(prompt => {
                const promptItem = document.createElement('div');
                promptItem.className = 'prompt-item';
                promptItem.draggable = true;
                promptItem.dataset.promptId = prompt.id;
                promptItem.dataset.promptName = prompt.display_name || prompt.name || prompt.id;
                
                const promptName = document.createElement('span');
                promptName.className = 'prompt-name';
                promptName.textContent = prompt.display_name || prompt.name || prompt.id;
                promptName.title = `${prompt.display_name || prompt.name || prompt.id} (ID: ${prompt.id})`;
                
                const dragHandle = document.createElement('i');
                dragHandle.className = 'bi bi-grip-vertical drag-handle';
                dragHandle.title = 'Drag to insert [[prompt_name]]';
                
                promptItem.appendChild(promptName);
                promptItem.appendChild(dragHandle);
                
                // Add click handler to navigate to prompt
                promptName.addEventListener('click', (e) => {
                    e.stopPropagation();
                    window.location.href = `/prompts/${prompt.id}`;
                });
                
                directoryPromptsDiv.appendChild(promptItem);
            });
            
            // Initialize drag and drop
            initializeDragAndDrop();
        })
        .catch(error => {
            console.error('Error loading directory prompts:', error);
            directoryPromptsDiv.innerHTML = '<p class="text-danger small">Error loading directory prompts.</p>';
        });
}

// Initialize drag and drop functionality
function initializeDragAndDrop() {
    const promptItems = document.querySelectorAll('#directory-prompts .prompt-item');
    const editorElement = document.querySelector('.CodeMirror');
    
    if (!editorElement) return;
    
    // Add drag event listeners to prompt items
    promptItems.forEach(item => {
        item.addEventListener('dragstart', (e) => {
            if (!rawContentPane.classList.contains('show')) {
                e.preventDefault();
                showToast('Drag and drop is only available in Raw Content view.', 'info');
                return;
            }
            
            const promptId = item.dataset.promptId;
            const promptName = item.dataset.promptName;
            
            // Set drag data
            e.dataTransfer.setData('text/plain', `[[${promptId}]]`);
            e.dataTransfer.setData('application/x-prompt-id', promptId);
            e.dataTransfer.setData('application/x-prompt-name', promptName);
            e.dataTransfer.effectAllowed = 'copy';
            
            // Add visual feedback
            item.classList.add('dragging');
            
            // Create custom drag image
            const dragImage = item.cloneNode(true);
            dragImage.style.transform = 'rotate(2deg)';
            dragImage.style.opacity = '0.8';
            document.body.appendChild(dragImage);
            e.dataTransfer.setDragImage(dragImage, 10, 10);
            
            setTimeout(() => document.body.removeChild(dragImage), 0);
        });
        
        item.addEventListener('dragend', (e) => {
            item.classList.remove('dragging');
        });
    });
    
    // Add drop zone functionality to CodeMirror editor
    editorElement.addEventListener('dragover', (e) => {
        if (!rawContentPane.classList.contains('show')) return;
        
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        editorElement.classList.add('drag-over');
    });
    
    editorElement.addEventListener('dragleave', (e) => {
        if (e.target === editorElement) {
            editorElement.classList.remove('drag-over');
        }
    });
    
    editorElement.addEventListener('drop', (e) => {
        e.preventDefault();
        editorElement.classList.remove('drag-over');
        
        if (!rawContentPane.classList.contains('show')) {
            showToast('Can only drop prompts in Raw Content view.', 'warning');
            return;
        }
        
        const promptId = e.dataTransfer.getData('application/x-prompt-id');
        const promptName = e.dataTransfer.getData('application/x-prompt-name');
        
        if (!promptId) return;
        
        // Get the cursor position based on where the drop occurred
        const coords = editor.coordsChar({
            left: e.clientX,
            top: e.clientY
        });
        
        // Insert the prompt inclusion at the cursor position
        const inclusionText = `[[${promptId}]]`;
        editor.replaceRange(inclusionText, coords);
        
        // Focus back to editor and position cursor after insertion
        editor.focus();
        editor.setCursor({
            line: coords.line,
            ch: coords.ch + inclusionText.length
        });
        
        showToast(`Inserted [[${promptName}]]`, 'success');
    });
}

// Export functions for use in main script
window.initializeCollapsibleSidebar = initializeCollapsibleSidebar;
window.loadDirectoryPrompts = loadDirectoryPrompts;
