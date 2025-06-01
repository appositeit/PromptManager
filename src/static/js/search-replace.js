/**
 * Search and Replace Functionality for CodeMirror Editor
 * 
 * Provides a dialog for searching and replacing text in the editor,
 * with support for regular expressions and live previews of matches
 * and replacements.
 */

class SearchReplace {
    /**
     * Initialize search and replace functionality
     * @param {CodeMirror} editor - The CodeMirror editor instance
     */
    constructor(editor) {
        this.editor = editor;
        this.dialog = null;
        this.searchInput = null;
        this.replaceInput = null;
        this.useRegexCheckbox = null;
        this.matchCase = null;
        this.matches = [];
        this.currentMatchIndex = -1;
        this.searchQuery = '';
        this.replaceText = '';
        this.useRegex = false;
        this.caseSensitive = false;
        this.searchMarkers = [];
        this.previewMarkers = [];
        this.isReplacePreviewVisible = false;
        
        // Add search key mapping
        this.editor.setOption('extraKeys', {
            ...(this.editor.getOption('extraKeys') || {}),
            'Alt-R': () => this.showDialog()
        });
    }
    
    /**
     * Create and show the search/replace dialog
     */
    showDialog() {
        // Only show in edit mode (raw content view)
        const editTab = document.getElementById('edit-tab');
        if (!editTab || !editTab.classList.contains('active')) {
            // Switch to edit tab first
            if (editTab) {editTab.click();}
        }
        
        // Create dialog if it doesn't exist
        if (!this.dialog) {
            this.createDialog();
        }
        
        // Show dialog
        this.dialog.style.display = 'block';
        
        // Focus search input
        setTimeout(() => {
            this.searchInput.focus();
            this.searchInput.select();
        }, 50);
    }
    
    /**
     * Create the search/replace dialog DOM elements
     */
    createDialog() {
        // Create dialog container
        this.dialog = document.createElement('div');
        this.dialog.className = 'search-replace-dialog';
        this.dialog.innerHTML = `
            <div class="search-replace-header">
                <h5>Search and Replace</h5>
                <button type="button" class="close-button" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="search-replace-body">
                <div class="form-group">
                    <label for="search-input">Search for:</label>
                    <input type="text" id="search-input" class="form-control" />
                    <div class="match-info">No matches found</div>
                </div>
                <div class="form-group">
                    <label for="replace-input">Replace with:</label>
                    <input type="text" id="replace-input" class="form-control" />
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="use-regex">
                    <label class="form-check-label" for="use-regex">
                        Use regular expressions
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="match-case">
                    <label class="form-check-label" for="match-case">
                        Match case
                    </label>
                </div>
            </div>
            <div class="search-replace-footer">
                <button type="button" class="btn btn-secondary btn-sm" id="prev-match-btn">
                    <i class="bi bi-arrow-up"></i> Previous
                </button>
                <button type="button" class="btn btn-secondary btn-sm" id="next-match-btn">
                    <i class="bi bi-arrow-down"></i> Next
                </button>
                <button type="button" class="btn btn-primary btn-sm" id="replace-btn">Replace</button>
                <button type="button" class="btn btn-primary btn-sm" id="replace-all-btn">Replace All</button>
                <button type="button" class="btn btn-secondary btn-sm" id="cancel-btn">Cancel</button>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(this.dialog);
        
        // Get references to form elements
        this.searchInput = document.getElementById('search-input');
        this.replaceInput = document.getElementById('replace-input');
        this.useRegexCheckbox = document.getElementById('use-regex');
        this.matchCaseCheckbox = document.getElementById('match-case');
        this.matchInfo = document.querySelector('.match-info');
        
        // Add event listeners
        this.searchInput.addEventListener('input', () => this.handleSearchInput());
        this.replaceInput.addEventListener('input', () => this.handleReplaceInput());
        this.useRegexCheckbox.addEventListener('change', () => this.handleSearchInput());
        this.matchCaseCheckbox.addEventListener('change', () => this.handleSearchInput());
        
        document.getElementById('prev-match-btn').addEventListener('click', () => this.findPrevious());
        document.getElementById('next-match-btn').addEventListener('click', () => this.findNext());
        document.getElementById('replace-btn').addEventListener('click', () => this.replace());
        document.getElementById('replace-all-btn').addEventListener('click', () => this.replaceAll());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideDialog());
        document.querySelector('.close-button').addEventListener('click', () => this.hideDialog());
        
        // Keyboard shortcuts
        this.dialog.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideDialog();
                e.preventDefault();
            } else if (e.key === 'Enter') {
                if (e.shiftKey) {
                    this.findPrevious();
                } else if (e.ctrlKey) {
                    this.replaceAll();
                } else {
                    this.replace();
                }
                e.preventDefault();
            } else if (e.key === 'F3' || (e.key === 'g' && e.ctrlKey)) {
                if (e.shiftKey) {
                    this.findPrevious();
                } else {
                    this.findNext();
                }
                e.preventDefault();
            }
        });
        
        // Add styles
        this.addStyles();
    }
    
    /**
     * Add CSS styles for the dialog
     */
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .search-replace-dialog {
                position: fixed;
                top: 100px;
                right: 30px;
                width: 350px;
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 1050;
                display: none;
                font-family: var(--bs-font-sans-serif);
            }
            
            .search-replace-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                border-bottom: 1px solid #ddd;
            }
            
            .search-replace-header h5 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .close-button {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #666;
            }
            
            .search-replace-body {
                padding: 15px;
            }
            
            .search-replace-footer {
                padding: 12px 15px;
                border-top: 1px solid #ddd;
                display: flex;
                justify-content: flex-end;
                gap: 8px;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
            }
            
            .form-check {
                margin-bottom: 10px;
            }
            
            .match-info {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
            
            .cm-searching {
                background-color: rgba(13, 71, 161, 0.15);
            }
            
            .cm-searching-current {
                background-color: rgba(13, 71, 161, 0.35);
            }
            
            .cm-preview-replace {
                background-color: rgba(13, 71, 161, 0.15);
                text-decoration: line-through;
            }
            
            .cm-preview-replace::after {
                content: attr(data-replace-text);
                position: absolute;
                left: 0;
                bottom: -1.2em;
                background-color: #f0f8ff;
                border: 1px solid #add8e6;
                padding: 0 3px;
                font-size: 0.9em;
                z-index: 10;
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Handle search input changes
     */
    handleSearchInput() {
        // Clear existing markers
        this.clearMarkers();
        
        // Get search parameters
        this.searchQuery = this.searchInput.value;
        this.useRegex = this.useRegexCheckbox.checked;
        this.caseSensitive = this.matchCaseCheckbox.checked;
        
        if (!this.searchQuery) {
            this.matchInfo.textContent = 'No matches found';
            return;
        }
        
        // Find all matches
        this.findMatches();
        
        // Update UI
        this.updateMatchInfo();
        
        // Highlight first match if any
        if (this.matches.length > 0) {
            this.currentMatchIndex = 0;
            this.highlightCurrentMatch();
        }
        
        // Update preview of replacements if text is in replace field
        if (this.replaceInput.value) {
            this.handleReplaceInput();
        }
    }
    
    /**
     * Handle replace input changes
     */
    handleReplaceInput() {
        // Get replace text
        this.replaceText = this.replaceInput.value;
        
        // Clear existing preview markers
        this.clearPreviewMarkers();
        
        // If we have matches and replace text, show preview
        if (this.matches.length > 0 && this.searchQuery) {
            this.showReplacePreview();
        }
    }
    
    /**
     * Find all matches in the editor content
     */
    findMatches() {
        this.matches = [];
        
        // Get search parameters
        const content = this.editor.getValue();
        const flags = this.caseSensitive ? 'g' : 'gi';
        
        try {
            // Create regex for search
            const searchRegex = this.useRegex ? 
                new RegExp(this.searchQuery, flags) : 
                new RegExp(this.escapeRegExp(this.searchQuery), flags);
            
            // Find all matches
            let match;
            while ((match = searchRegex.exec(content)) !== null) {
                const start = this.editor.posFromIndex(match.index);
                const end = this.editor.posFromIndex(match.index + match[0].length);
                
                this.matches.push({
                    from: start,
                    to: end,
                    match: match[0],
                    index: match.index
                });
                
                // Create marker for match
                const marker = this.editor.markText(start, end, {
                    className: 'cm-searching'
                });
                
                this.searchMarkers.push(marker);
                
                // Prevent infinite loop for zero-length matches
                if (match.index === searchRegex.lastIndex) {
                    searchRegex.lastIndex++;
                }
            }
        } catch (e) {
            // Invalid regex
            console.error('Invalid regular expression:', e);
            this.matchInfo.textContent = 'Invalid regular expression';
        }
    }
    
    /**
     * Escape special regex characters in a string
     */
    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    /**
     * Update match count information
     */
    updateMatchInfo() {
        if (this.matches.length === 0) {
            this.matchInfo.textContent = 'No matches found';
        } else {
            this.matchInfo.textContent = `${this.currentMatchIndex + 1} of ${this.matches.length} matches`;
        }
    }
    
    /**
     * Highlight the current match
     */
    highlightCurrentMatch() {
        if (this.currentMatchIndex >= 0 && this.currentMatchIndex < this.matches.length) {
            // Clear previous current match highlight
            this.searchMarkers.forEach(marker => {
                marker.className = 'cm-searching';
            });
            
            // Highlight current match
            const match = this.matches[this.currentMatchIndex];
            
            // Update marker
            if (this.searchMarkers[this.currentMatchIndex]) {
                this.searchMarkers[this.currentMatchIndex].clear();
                this.searchMarkers[this.currentMatchIndex] = this.editor.markText(
                    match.from, match.to, 
                    { className: 'cm-searching-current' }
                );
            }
            
            // Scroll to match
            this.editor.scrollIntoView({
                from: match.from,
                to: match.to
            }, 100);
            
            // Update info text
            this.updateMatchInfo();
        }
    }
    
    /**
     * Show a preview of replacement text
     */
    showReplacePreview() {
        // Only show preview for current match
        if (this.currentMatchIndex >= 0 && this.currentMatchIndex < this.matches.length) {
            const match = this.matches[this.currentMatchIndex];
            
            try {
                // Generate replacement text
                let replacementText = this.replaceText;
                
                if (this.useRegex) {
                    // Apply regex capture groups if applicable
                    const regex = new RegExp(this.searchQuery, this.caseSensitive ? '' : 'i');
                    const matched = match.match.match(regex);
                    if (matched) {
                        replacementText = match.match.replace(regex, this.replaceText);
                    }
                }
                
                // Create marker for preview
                const marker = this.editor.markText(
                    match.from, match.to, 
                    {
                        className: 'cm-preview-replace',
                        attributes: { 'data-replace-text': replacementText }
                    }
                );
                
                this.previewMarkers.push(marker);
                this.isReplacePreviewVisible = true;
                
            } catch (e) {
                console.error('Error creating replacement preview:', e);
            }
        }
    }
    
    /**
     * Find the next match and highlight it
     */
    findNext() {
        if (this.matches.length === 0) {return;}
        
        this.currentMatchIndex = (this.currentMatchIndex + 1) % this.matches.length;
        this.highlightCurrentMatch();
        this.clearPreviewMarkers();
        if (this.replaceText) {
            this.showReplacePreview();
        }
    }
    
    /**
     * Find the previous match and highlight it
     */
    findPrevious() {
        if (this.matches.length === 0) {return;}
        
        this.currentMatchIndex = (this.currentMatchIndex - 1 + this.matches.length) % this.matches.length;
        this.highlightCurrentMatch();
        this.clearPreviewMarkers();
        if (this.replaceText) {
            this.showReplacePreview();
        }
    }
    
    /**
     * Replace the current match with the replacement text
     */
    replace() {
        if (this.currentMatchIndex >= 0 && this.currentMatchIndex < this.matches.length) {
            const match = this.matches[this.currentMatchIndex];
            
            try {
                // Generate replacement text
                let replacementText = this.replaceText;
                
                if (this.useRegex) {
                    // Apply regex capture groups if applicable
                    const regex = new RegExp(this.searchQuery, this.caseSensitive ? '' : 'i');
                    const matched = match.match.match(regex);
                    if (matched) {
                        replacementText = match.match.replace(regex, this.replaceText);
                    }
                }
                
                // Replace text in editor
                this.editor.replaceRange(replacementText, match.from, match.to);
                
                // Clear markers and find matches again (positions may have changed)
                this.clearMarkers();
                this.clearPreviewMarkers();
                
                // Find matches again
                this.findMatches();
                
                // Update current match index if matches remain
                if (this.matches.length > 0) {
                    this.currentMatchIndex = Math.min(this.currentMatchIndex, this.matches.length - 1);
                    this.highlightCurrentMatch();
                    
                    // Show preview for next match
                    if (this.replaceText) {
                        this.showReplacePreview();
                    }
                } else {
                    this.currentMatchIndex = -1;
                    this.updateMatchInfo();
                }
            } catch (e) {
                console.error('Error replacing text:', e);
            }
        }
    }
    
    /**
     * Replace all matches with the replacement text
     */
    replaceAll() {
        if (this.matches.length === 0) {return;}
        
        // We need to replace from end to start to avoid position issues
        const matchesCopy = [...this.matches].sort((a, b) => b.index - a.index);
        
        // Start an edit operation for undo
        this.editor.operation(() => {
            for (const match of matchesCopy) {
                try {
                    // Generate replacement text
                    let replacementText = this.replaceText;
                    
                    if (this.useRegex) {
                        // Apply regex capture groups if applicable
                        const regex = new RegExp(this.searchQuery, this.caseSensitive ? '' : 'i');
                        const matched = match.match.match(regex);
                        if (matched) {
                            replacementText = match.match.replace(regex, this.replaceText);
                        }
                    }
                    
                    // Replace text in editor
                    this.editor.replaceRange(replacementText, match.from, match.to);
                } catch (e) {
                    console.error('Error replacing text:', e);
                }
            }
        });
        
        // Clear markers
        this.clearMarkers();
        this.clearPreviewMarkers();
        
        // Find matches again (should be none if all were replaced)
        this.findMatches();
        
        // Update match info
        this.updateMatchInfo();
    }
    
    /**
     * Clear all search markers
     */
    clearMarkers() {
        for (const marker of this.searchMarkers) {
            marker.clear();
        }
        this.searchMarkers = [];
    }
    
    /**
     * Clear all preview markers
     */
    clearPreviewMarkers() {
        for (const marker of this.previewMarkers) {
            marker.clear();
        }
        this.previewMarkers = [];
        this.isReplacePreviewVisible = false;
    }
    
    /**
     * Hide the search/replace dialog
     */
    hideDialog() {
        this.dialog.style.display = 'none';
        this.clearMarkers();
        this.clearPreviewMarkers();
        this.editor.focus();
    }
}

// Make SearchReplace class available globally
window.SearchReplace = SearchReplace;
