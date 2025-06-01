/**
 * Collapsible Sidebar with Prompt References
 * Handles collapse/expand state management and drag-and-drop functionality
 */

class CollapsibleSidebar {
    constructor() {
        this.sidebarState = this.loadSidebarState();
        this.directoryPrompts = [];
        this.currentPromptId = null;
        this.currentDirectory = null;
        
        this.initializeCollapsibleCards();
        this.initializeDirectoryPrompts();
        this.bindEvents();
    }

    /**
     * Load sidebar state from sessionStorage
     */
    loadSidebarState() {
        try {
            const saved = window.sessionStorage.getItem('sidebarState');
            return saved ? JSON.parse(saved) : {
                metadata: true,
                directoryPrompts: true,
                dependencies: true,
                referencedBy: true,
                markdownCheat: true
            };
        } catch (error) {
            console.warn('Failed to load sidebar state from sessionStorage:', error);
            return {
                metadata: true,
                directoryPrompts: true,
                dependencies: true,
                referencedBy: true,
                markdownCheat: true
            };
        }
    }

    /**
     * Save sidebar state to sessionStorage
     */
    saveSidebarState() {
        try {
            window.sessionStorage.setItem('sidebarState', JSON.stringify(this.sidebarState));
        } catch (error) {
            console.warn('Failed to save sidebar state to sessionStorage:', error);
        }
    }

    /**
     * Initialize collapsible functionality for all sidebar cards
     */
    initializeCollapsibleCards() {
        const cards = document.querySelectorAll('.sidebar-card');
        
        cards.forEach(card => {
            const cardId = card.dataset.cardId;
            if (!cardId) {
                return;
            }

            const header = card.querySelector('.collapsible-header');
            const content = card.querySelector('.collapsible-content');
            const chevron = card.querySelector('.collapse-chevron');

            if (!header || !content || !chevron) {
                return;
            }

            // Set initial state
            const isExpanded = this.sidebarState[cardId] !== false;
            this.setCardState(card, isExpanded, false);

            // Add click handler
            header.addEventListener('click', (e) => {
                e.preventDefault();
                const currentlyExpanded = content.classList.contains('show');
                this.toggleCard(card, !currentlyExpanded);
            });

            // Add keyboard support
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    header.click();
                }
            });
        });
    }

    /**
     * Toggle a card's collapsed state
     */
    toggleCard(card, expand) {
        const cardId = card.dataset.cardId;
        const content = card.querySelector('.collapsible-content');
        const chevron = card.querySelector('.collapse-chevron');

        if (!cardId || !content || !chevron) {
            return;
        }

        // Update state
        this.sidebarState[cardId] = expand;
        this.saveSidebarState();

        // Apply visual changes
        this.setCardState(card, expand, true);
    }

    /**
     * Set the visual state of a card
     */
    setCardState(card, expand, animate = true) {
        const content = card.querySelector('.collapsible-content');
        const chevron = card.querySelector('.collapse-chevron');

        if (!content || !chevron) {
            return;
        }

        if (expand) {
            content.classList.add('show');
            chevron.classList.remove('collapsed');
        } else {
            content.classList.remove('show');
            chevron.classList.add('collapsed');
        }

        // Add animation class if needed
        if (animate) {
            content.classList.add('collapsing');
            setTimeout(() => {
                content.classList.remove('collapsing');
            }, 350);
        }
    }

    /**
     * Initialize directory prompts functionality
     */
    initializeDirectoryPrompts() {
        // Get current prompt context
        this.currentPromptId = document.getElementById('prompt-true-unique-id')?.textContent?.trim();
        
        // Extract directory from currentPromptData if available
        if (window.currentPromptData && window.currentPromptData.directory) {
            this.currentDirectory = window.currentPromptData.directory;
            this.loadDirectoryPrompts();
        } else {
            // Wait for currentPromptData to be available
            this.waitForCurrentPromptData();
        }
    }

    /**
     * Wait for currentPromptData to be available
     */
    waitForCurrentPromptData() {
        const checkData = () => {
            if (window.currentPromptData && window.currentPromptData.directory) {
                this.currentDirectory = window.currentPromptData.directory;
                this.loadDirectoryPrompts();
            } else {
                setTimeout(checkData, 100);
            }
        };
        checkData();
    }

    /**
     * Load prompts from the current directory
     */
    async loadDirectoryPrompts() {
        if (!this.currentDirectory) {
            console.warn('No current directory available for loading directory prompts');
            return;
        }

        const container = document.getElementById('directory-prompts-list');
        if (!container) {
            console.warn('Directory prompts container not found');
            return;
        }

        try {
            // Show loading state
            container.innerHTML = '<div class="text-center p-2"><div class="spinner-border spinner-border-sm"></div> Loading...</div>';

            const response = await fetch(`/api/prompts/directories/${encodeURIComponent(this.currentDirectory)}/prompts`);
            
            if (!response.ok) {
                throw new Error(`Failed to load directory prompts: ${response.status}`);
            }

            const prompts = await response.json();
            
            // Filter out the current prompt
            this.directoryPrompts = prompts.filter(p => p.id !== this.currentPromptId);
            
            this.renderDirectoryPrompts();
            
        } catch (error) {
            console.error('Error loading directory prompts:', error);
            container.innerHTML = '<div class="text-danger p-2">Error loading prompts</div>';
            if (window.showToast) {
                window.showToast('Failed to load directory prompts', 'error');
            }
        }
    }

    /**
     * Render the directory prompts list
     */
    renderDirectoryPrompts() {
        const container = document.getElementById('directory-prompts-list');
        if (!container) {
            return;
        }

        if (this.directoryPrompts.length === 0) {
            container.innerHTML = '<div class="directory-prompts-empty">No other prompts in this directory</div>';
            return;
        }

        container.innerHTML = '';

        this.directoryPrompts.forEach(prompt => {
            const item = this.createDirectoryPromptItem(prompt);
            container.appendChild(item);
        });
    }

    /**
     * Create a directory prompt item element
     */
    createDirectoryPromptItem(prompt) {
        const item = document.createElement('div');
        item.className = 'directory-prompt-item list-group-item';
        item.draggable = true;
        item.dataset.promptId = prompt.id;
        item.dataset.promptName = prompt.display_name || prompt.id;

        const displayName = prompt.display_name || prompt.id;
        const showId = displayName !== prompt.id;

        item.innerHTML = `
            <span class="directory-prompt-name" title="${prompt.id}">${displayName}</span>
            ${showId ? `<span class="directory-prompt-id">${prompt.id}</span>` : ''}
        `;

        // Add click handler for navigation
        item.addEventListener('click', (e) => {
            if (!e.defaultPrevented) {
                window.location.href = `/prompts/${prompt.id}`;
            }
        });

        // Add drag handlers
        this.addDragHandlers(item);

        return item;
    }

    /**
     * Add drag and drop handlers to a prompt item
     */
    addDragHandlers(item) {
        const promptId = item.dataset.promptId;

        item.addEventListener('dragstart', (e) => {
            e.preventDefault = false; // Allow the drag
            
            // Set drag data
            e.dataTransfer.setData('text/plain', `[[${promptId}]]`);
            e.dataTransfer.setData('application/x-prompt-id', promptId);
            e.dataTransfer.effectAllowed = 'copy';

            // Create custom drag image
            const dragImage = this.createDragImage(promptId);
            e.dataTransfer.setDragImage(dragImage, 10, 10);

            // Add visual feedback
            item.classList.add('dragging');

            // Clean up drag image after a brief delay
            setTimeout(() => {
                if (dragImage.parentNode) {
                    dragImage.parentNode.removeChild(dragImage);
                }
            }, 0);
        });

        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
        });
    }

    /**
     * Create a custom drag image
     */
    createDragImage(promptId) {
        const dragImage = document.createElement('div');
        dragImage.className = 'drag-preview';
        dragImage.textContent = `[[${promptId}]]`;
        
        // Add to body temporarily
        document.body.appendChild(dragImage);
        
        return dragImage;
    }

    /**
     * Set up drag target on the editor
     */
    setupEditorDragTarget() {
        if (!window.editor) {
            // Wait for editor to be available
            setTimeout(() => this.setupEditorDragTarget(), 100);
            return;
        }

        const editorElement = window.editor.display.wrapper;
        
        editorElement.addEventListener('dragover', (e) => {
            // Only allow drop if Raw Content tab is active
            const rawTab = document.getElementById('raw-content');
            if (!rawTab || !rawTab.classList.contains('show')) {
                e.dataTransfer.dropEffect = 'none';
                return;
            }

            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        editorElement.addEventListener('drop', (e) => {
            // Only allow drop if Raw Content tab is active
            const rawTab = document.getElementById('raw-content');
            if (!rawTab || !rawTab.classList.contains('show')) {
                if (window.showToast) {
                    window.showToast('Drag and drop is only available in Raw Content view', 'info');
                }
                return;
            }

            e.preventDefault();

            const promptReference = e.dataTransfer.getData('text/plain');
            if (!promptReference) {
                return;
            }

            // Get cursor position from mouse coordinates
            const coords = window.editor.coordsChar({ left: e.clientX, top: e.clientY });
            
            // Insert the prompt reference at the cursor position
            window.editor.replaceRange(promptReference, coords);
            
            // Focus the editor
            window.editor.focus();

            if (window.showToast) {
                window.showToast('Prompt reference inserted!', 'success');
            }
        });
    }

    /**
     * Bind global events
     */
    bindEvents() {
        // Set up editor drag target when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupEditorDragTarget();
            });
        } else {
            this.setupEditorDragTarget();
        }

        // Listen for prompt data updates to refresh directory prompts
        document.addEventListener('promptDataUpdated', () => {
            if (window.currentPromptData && window.currentPromptData.directory !== this.currentDirectory) {
                this.currentDirectory = window.currentPromptData.directory;
                this.loadDirectoryPrompts();
            }
        });
    }

    /**
     * Refresh directory prompts (public method)
     */
    refresh() {
        this.loadDirectoryPrompts();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.collapsibleSidebar = new CollapsibleSidebar();
    });
} else {
    window.collapsibleSidebar = new CollapsibleSidebar();
}
