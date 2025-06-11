/**
 * New Prompt Modal Utility
 * Provides reusable functionality for creating new prompts
 */

class NewPromptModal {
    constructor(context = 'manage_prompts', currentDirectory = null) {
        this.context = context;
        this.currentDirectory = currentDirectory;
        this.modal = null;
        this.directories = [];
        
        this.init();
    }
    
    init() {
        // Get DOM elements
        this.promptNameInput = document.getElementById('promptName');
        this.promptDirectorySelect = document.getElementById('promptDirectory');
        this.promptIdPreview = document.getElementById('promptIdPreview');
        this.promptDisplayNamePreview = document.getElementById('promptDisplayNamePreview');
        this.promptDescriptionInput = document.getElementById('promptDescription');
        this.promptTagsInput = document.getElementById('promptTags');
        this.createPromptBtn = document.getElementById('createPromptBtn');
        this.createPromptInNewTabBtn = document.getElementById('createPromptInNewTabBtn');
        this.modalElement = document.getElementById('newPromptModal');
        
        if (this.modalElement) {
            this.modal = new bootstrap.Modal(this.modalElement);
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // ID preview functionality
        if (this.promptNameInput && this.promptDirectorySelect && this.promptIdPreview) {
            this.promptNameInput.addEventListener('input', () => this.updateIdPreview());
            this.promptDirectorySelect.addEventListener('change', () => this.updateIdPreview());
        }
        
        // Create prompt button
        if (this.createPromptBtn) {
            this.createPromptBtn.addEventListener('click', () => this.createPrompt(false));
        }
        
        // Create in new tab button (only in prompt editor context)
        if (this.createPromptInNewTabBtn) {
            this.createPromptInNewTabBtn.addEventListener('click', () => this.createPrompt(true));
        }
        
        // Modal keyboard shortcuts
        if (this.modalElement) {
            this.modalElement.addEventListener('keydown', (event) => {
                if (event.ctrlKey && event.shiftKey && event.key === 'Enter') {
                    event.preventDefault();
                    if (this.createPromptInNewTabBtn) {
                        this.createPromptInNewTabBtn.click();
                    }
                } else if (event.ctrlKey && event.key === 'Enter') {
                    event.preventDefault();
                    this.createPromptBtn?.click();
                } else if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey) {
                    // Allow normal Enter behavior in form fields, but trigger create on form submission
                    const activeElement = document.activeElement;
                    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'SELECT')) {
                        event.preventDefault();
                        this.createPromptBtn?.click();
                    }
                }
            });
        }
    }
    
    updateIdPreview() {
        const name = this.promptNameInput?.value.trim();
        const directory = this.promptDirectorySelect?.value;
        
        if (name && directory) {
            // Show the full path ID
            const fullPathId = `${directory}/${name}`;
            if (this.promptIdPreview) {
                this.promptIdPreview.value = fullPathId;
            }
            
            // For display name preview, show a simple approximation
            // (The actual display name will be calculated by the server based on all prompts)
            if (this.promptDisplayNamePreview) {
                const dirPath = directory.split('/');
                const dirName = dirPath[dirPath.length - 1] || 'root';
                this.promptDisplayNamePreview.value = `${dirName}:${name} (approximate)`;
            }
        } else {
            if (this.promptIdPreview) {
                this.promptIdPreview.value = '';
            }
            if (this.promptDisplayNamePreview) {
                this.promptDisplayNamePreview.value = '';
            }
        }
    }
    
    populateDirectorySelect(directories) {
        this.directories = directories;
        
        if (this.promptDirectorySelect) {
            this.promptDirectorySelect.innerHTML = '';
            
            // Sort directories alphabetically by name
            const enabledDirectories = directories
                .filter(dir => dir.enabled)
                .sort((a, b) => a.name.localeCompare(b.name));
            
            enabledDirectories.forEach(dir => {
                const option = document.createElement('option');
                option.value = dir.path;
                option.textContent = dir.name;
                this.promptDirectorySelect.appendChild(option);
            });
            
            // Set default directory if in prompt editor context
            if (this.context === 'prompt_editor' && this.currentDirectory) {
                this.promptDirectorySelect.value = this.currentDirectory;
                this.updateIdPreview();
            }
        }
    }
    
    show() {
        if (this.modal) {
            this.modal.show();
            // Focus the name input after modal is shown
            setTimeout(() => {
                this.promptNameInput?.focus();
            }, 300);
        }
    }
    
    hide() {
        if (this.modal) {
            this.modal.hide();
        }
    }
    
    clearForm() {
        if (this.promptNameInput) {this.promptNameInput.value = '';}
        if (this.promptIdPreview) {this.promptIdPreview.value = '';}
        if (this.promptDisplayNamePreview) {this.promptDisplayNamePreview.value = '';}
        if (this.promptDescriptionInput) {this.promptDescriptionInput.value = '';}
        if (this.promptTagsInput) {this.promptTagsInput.value = '';}
    }
    
    createPrompt(openInNewTab = false) {
        const name = this.promptNameInput?.value.trim();
        const directory = this.promptDirectorySelect?.value;
        const description = this.promptDescriptionInput?.value.trim();
        const tags = this.promptTagsInput?.value.trim();
        const content = '';  // Empty content, will be filled with default in the backend
        
        // Validate
        if (!name) {
            alert('Prompt name is required');
            return;
        }
        
        if (!directory) {
            alert('Directory is required');
            return;
        }
        
        // Create tag array
        const tagArray = tags ? tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        // Create prompt data with new schema
        const promptData = {
            name: name,  // Changed from 'id' to 'name'
            content: content || `# ${name}\n\nEnter content here...`,
            directory: directory,
            description: description,
            tags: tagArray
        };
        
        console.log('Sending prompt data:', promptData);
        
        // Disable buttons during creation
        if (this.createPromptBtn) {
            this.createPromptBtn.disabled = true;
            this.createPromptBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
        }
        if (this.createPromptInNewTabBtn) {
            this.createPromptInNewTabBtn.disabled = true;
        }
        
        // Send POST request
        fetch('/api/prompts/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(promptData)
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Failed to create prompt: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Success - show toast with any sanitization message
            if (data.sanitized_message) {
                showToast(data.sanitized_message, 'warning');
            }
            showToast('Prompt created successfully', 'success');
            
            // Close modal and clear form
            this.hide();
            this.clearForm();
            
            // Reload prompts if we have a loadPrompts function available
            if (typeof loadPrompts === 'function') {
                loadPrompts();
            }
            
            // Navigate to the new prompt
            const promptUrl = `/prompts/${data.id}`;
            if (openInNewTab) {
                window.open(promptUrl, '_blank');
            } else {
                window.location.href = promptUrl;
            }
        })
        .catch(error => {
            console.error('Error creating prompt:', error);
            showToast('Error creating prompt: ' + error.message, 'error');
        })
        .finally(() => {
            // Re-enable buttons
            if (this.createPromptBtn) {
                this.createPromptBtn.disabled = false;
                this.createPromptBtn.innerHTML = '<i class="bi bi-plus-circle"></i> Create';
            }
            if (this.createPromptInNewTabBtn) {
                this.createPromptInNewTabBtn.disabled = false;
            }
        });
    }
}

// Global instance - will be initialized when needed
window.newPromptModal = null;

// Helper function to show new prompt modal
window.showNewPromptModal = function(context = 'manage_prompts', currentDirectory = null) {
    if (!window.newPromptModal) {
        window.newPromptModal = new NewPromptModal(context, currentDirectory);
    } else {
        // Update context and current directory if different
        window.newPromptModal.context = context;
        window.newPromptModal.currentDirectory = currentDirectory;
        
        // Update directory selection if needed
        if (context === 'prompt_editor' && currentDirectory && window.newPromptModal.promptDirectorySelect) {
            window.newPromptModal.promptDirectorySelect.value = currentDirectory;
            window.newPromptModal.updateIdPreview();
        }
    }
    
    window.newPromptModal.show();
};

// Helper function to populate directories
window.populateNewPromptDirectories = function(directories) {
    if (window.newPromptModal) {
        window.newPromptModal.populateDirectorySelect(directories);
    }
};

// Make the class available globally
window.NewPromptModal = NewPromptModal;
