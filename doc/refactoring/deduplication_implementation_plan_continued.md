# Code Deduplication Implementation Plan (Continued)

## 3. Template Macros System (continued)

### Updated `manage_prompts.html` (example using macros) - continued

```html
                <button type="button" class="btn btn-primary" id="createPromptBtn">Create</button>
            </div>
        </div>
    </div>
</div>

<!-- Add Directory Modal -->
<div class="modal fade" id="addDirectoryModal" tabindex="-1" aria-labelledby="addDirectoryModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="addDirectoryModalLabel">Add Prompt Directory</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="addDirectoryForm">
                    <div class="mb-3">
                        <label for="directoryPath" class="form-label">Directory Path</label>
                        <input type="text" class="form-control" id="directoryPath" required>
                    </div>
                    <div class="mb-3">
                        <label for="directoryName" class="form-label">Display Name</label>
                        <input type="text" class="form-control" id="directoryName">
                        <div class="form-text">If not provided, the directory name will be used</div>
                    </div>
                    <div class="mb-3">
                        <label for="directoryDescription" class="form-label">Description</label>
                        <input type="text" class="form-control" id="directoryDescription">
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="addDirectoryBtn">Add</button>
            </div>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modals -->
{{ tables.confirmation_modal('deletePromptModal', 'Confirm Deletion', 'Are you sure you want to delete the prompt <strong id="delete-prompt-id"></strong>?', 'Delete', 'danger') }}

{{ tables.confirmation_modal('deleteDirectoryModal', 'Confirm Deletion', 'Are you sure you want to remove this directory? This will remove the directory from the system, but will not delete any files.', 'Remove', 'danger') }}
{% endblock %}

{% block extra_js %}
<script type="module">
    // Import utility functions
    import { showToast, formatDate, stableSort } from '/static/js/utils.js';
    import { reloadDirectory, reloadAllPrompts } from '/static/js/directory_manager.js';

    // Global variables
    let prompts = [];
    let directories = [];
    let currentFilter = {
        type: 'all',
        tag: 'all',
        search: ''
    };
    
    // Sort settings
    let currentSort = {
        column: 'directory',
        direction: 'asc'
    };
    
    document.addEventListener('DOMContentLoaded', function() {
        // Load prompts
        loadPrompts();
        
        // Load directories
        loadDirectories();
        
        // Set up refresh all button
        document.getElementById('refresh-all-btn').addEventListener('click', refreshAllDirectories);
        
        // Set up event handlers - search immediately on typing
        document.getElementById('prompt-search').addEventListener('input', function() {
            currentFilter.search = this.value;
            filterPrompts();
        });
        
        // Keep the button functionality for compatibility
        document.getElementById('prompt-search-btn').addEventListener('click', function() {
            currentFilter.search = document.getElementById('prompt-search').value;
            filterPrompts();
        });
        
        // Add focus to search box when page loads and when no item is selected
        document.addEventListener('keydown', function(event) {
            // If a text input or textarea isn't focused and user starts typing a letter/number
            if (document.activeElement.tagName !== 'INPUT' && 
                document.activeElement.tagName !== 'TEXTAREA' &&
                document.activeElement.tagName !== 'SELECT' &&
                event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
                // Focus the search box and add the typed character
                const searchBox = document.getElementById('prompt-search');
                searchBox.focus();
                // Don't overwrite the value as the input event will handle the filtering
            }
        });
        
        // Set up sorting functionality
        const sortableHeaders = document.querySelectorAll('.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.dataset.sort;
                
                // Toggle direction if clicking on the same column
                if (currentSort.column === column) {
                    currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSort.column = column;
                    currentSort.direction = 'asc';
                }
                
                // Update visuals and re-sort
                updateSortHeaders();
                updatePromptsTable();
            });
        });
        
        // Initialize sort headers
        updateSortHeaders();
        
        // Add keyboard navigation for the prompt table - enhanced to work with search box focus
        document.addEventListener('keydown', function(event) {
            const promptsTable = document.getElementById('prompts-table-body');
            if (!promptsTable) return;
            
            const rows = promptsTable.querySelectorAll('tr');
            if (!rows.length) return;
            
            // Find the currently selected row
            let selectedRow = promptsTable.querySelector('tr.selected');
            let selectedIndex = -1;
            
            if (selectedRow) {
                // Find the index of the selected row
                for (let i = 0; i < rows.length; i++) {
                    if (rows[i] === selectedRow) {
                        selectedIndex = i;
                        break;
                    }
                }
            }
            
            // Special handling for search box
            const isSearchBoxFocused = document.activeElement === document.getElementById('prompt-search');
            
            // Handle up/down arrow keys for navigation regardless of focus
            if (event.key === 'ArrowDown' && (isSearchBoxFocused || 
                !(event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT'))) {
                event.preventDefault();
                
                if (selectedIndex === -1 || selectedIndex >= rows.length - 1) {
                    // Select the first row if nothing is selected or at the end
                    selectedIndex = 0;
                } else {
                    // Select the next row
                    selectedIndex++;
                }
                
                // Update selection
                updateRowSelection(rows, selectedIndex);
            } else if (event.key === 'ArrowUp' && (isSearchBoxFocused || 
                !(event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT'))) {
                event.preventDefault();
                
                if (selectedIndex <= 0) {
                    // Select the last row if nothing is selected or at the beginning
                    selectedIndex = rows.length - 1;
                } else {
                    // Select the previous row
                    selectedIndex--;
                }
                
                // Update selection
                updateRowSelection(rows, selectedIndex);
            } else if (event.key === 'Enter' && selectedRow && 
                (isSearchBoxFocused || 
                !(event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT'))) {
                event.preventDefault();
                
                // Navigate to the selected prompt
                const promptLink = selectedRow.querySelector('a');
                if (promptLink) {
                    window.location.href = promptLink.href;
                }
            }
        });
        
        // Set up other event handlers...
        // [other event handlers implementation]
    });
    
    // Function to update the sort header icons and classes
    function updateSortHeaders() {
        // Remove all sort classes
        document.querySelectorAll('.sortable').forEach(header => {
            header.classList.remove('sort-active', 'sort-asc', 'sort-desc');
        });
        
        // Find the active header and update its classes
        const activeHeader = document.querySelector(`.sortable[data-sort="${currentSort.column}"]`);
        if (activeHeader) {
            activeHeader.classList.add('sort-active');
            activeHeader.classList.add(currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');
            
            // Update the icon class
            const icon = activeHeader.querySelector('.sort-icon');
            if (icon) {
                icon.classList.remove('bi-sort-alpha-down', 'bi-sort-alpha-up');
                icon.classList.add(currentSort.direction === 'asc' ? 'bi-sort-alpha-down' : 'bi-sort-alpha-up');
            }
        }
    }
    
    // Rest of the implementation...
    // [implementation of the rest of the functions]
</script>
{% endblock %}
```

## 4. JavaScript Component System

### New Component Base Class (`/static/js/components/base-component.js`)

```javascript
/**
 * Base component class for UI components.
 */
export class BaseComponent {
    /**
     * Constructor for BaseComponent
     * 
     * @param {Object} options - Component options
     * @param {string} options.id - Component ID
     * @param {HTMLElement} options.container - Container element
     */
    constructor(options = {}) {
        this.id = options.id || `component-${Date.now()}`;
        this.container = options.container || document.body;
        this.elements = {};
        this.data = options.data || {};
        this.events = {};
        
        // Default initialization
        if (options.autoInit !== false) {
            this.init();
        }
    }
    
    /**
     * Initialize the component
     */
    init() {
        this.render();
        this.bindEvents();
    }
    
    /**
     * Render the component (to be implemented by subclasses)
     */
    render() {
        throw new Error('Render method must be implemented by subclasses');
    }
    
    /**
     * Bind events to DOM elements (to be implemented by subclasses)
     */
    bindEvents() {
        // Default implementation
    }
    
    /**
     * Add an event listener to the component
     * 
     * @param {string} event - Event name
     * @param {Function} callback - Event callback
     */
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        
        this.events[event].push(callback);
        return this;
    }
    
    /**
     * Trigger an event on the component
     * 
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    trigger(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
        
        return this;
    }
    
    /**
     * Update the component data
     * 
     * @param {Object} data - New data
     */
    update(data) {
        this.data = { ...this.data, ...data };
        this.render();
        return this;
    }
    
    /**
     * Destroy the component
     */
    destroy() {
        // Remove event listeners
        this.events = {};
        
        // Remove DOM elements
        Object.values(this.elements).forEach(element => {
            if (element instanceof HTMLElement) {
                element.remove();
            }
        });
        
        this.elements = {};
    }
}
```

### Toast Component (`/static/js/components/toast-manager.js`)

```javascript
/**
 * Toast manager component for displaying notifications.
 */
import { BaseComponent } from './base-component.js';

export class ToastManager extends BaseComponent {
    /**
     * Constructor for ToastManager
     * 
     * @param {Object} options - Component options
     * @param {string} options.id - Component ID
     * @param {HTMLElement} options.container - Container element
     * @param {string} options.position - Toast position (default: 'bottom-end')
     */
    constructor(options = {}) {
        super({
            ...options,
            id: options.id || 'toast-manager'
        });
    }
    
    /**
     * Render the toast container
     */
    render() {
        // Create toast container if it doesn't exist
        if (!this.elements.container) {
            this.elements.container = document.createElement('div');
            this.elements.container.id = `${this.id}-container`;
            this.elements.container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            this.container.appendChild(this.elements.container);
        }
    }
    
    /**
     * Show a toast notification
     * 
     * @param {string} message - Message to display
     * @param {string} type - Toast type (success, danger, warning, info)
     * @param {number} duration - Toast duration in milliseconds
     * @returns {string} Toast ID
     */
    show(message, type = 'success', duration = 3000) {
        // Ensure container exists
        this.render();
        
        // Create toast element
        const toastId = `toast-${Date.now()}`;
        const toast = document.createElement('div');
        toast.className = `toast bg-${type} text-white`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Toast content
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add to container
        this.elements.container.appendChild(toast);
        
        // Initialize and show toast
        const toastInstance = new bootstrap.Toast(toast, {
            animation: true,
            autohide: true,
            delay: duration
        });
        
        toastInstance.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
        
        // Trigger event
        this.trigger('show', { id: toastId, message, type });
        
        return toastId;
    }
    
    /**
     * Show a success toast
     * 
     * @param {string} message - Message to display
     * @param {number} duration - Toast duration in milliseconds
     * @returns {string} Toast ID
     */
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }
    
    /**
     * Show a danger/error toast
     * 
     * @param {string} message - Message to display
     * @param {number} duration - Toast duration in milliseconds
     * @returns {string} Toast ID
     */
    error(message, duration = 3000) {
        return this.show(message, 'danger', duration);
    }
    
    /**
     * Show a warning toast
     * 
     * @param {string} message - Message to display
     * @param {number} duration - Toast duration in milliseconds
     * @returns {string} Toast ID
     */
    warning(message, duration = 3000) {
        return this.show(message, 'warning', duration);
    }
    
    /**
     * Show an info toast
     * 
     * @param {string} message - Message to display
     * @param {number} duration - Toast duration in milliseconds
     * @returns {string} Toast ID
     */
    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }
}

// Create a global instance
const toastManager = new ToastManager();
export default toastManager;

// Register showToast as a global function for backward compatibility
window.showToast = (message, type = 'success', duration = 3000) => {
    return toastManager.show(message, type, duration);
};
```

### DataTable Component (`/static/js/components/data-table.js`)

```javascript
/**
 * DataTable component for displaying, sorting, and filtering tabular data.
 */
import { BaseComponent } from './base-component.js';

export class DataTable extends BaseComponent {
    /**
     * Constructor for DataTable
     * 
     * @param {Object} options - Component options
     * @param {string} options.id - Component ID
     * @param {HTMLElement} options.container - Container element
     * @param {Array} options.data - Table data
     * @param {Array} options.columns - Column definitions
     * @param {string} options.emptyMessage - Message to show when table is empty
     * @param {Function} options.rowRenderer - Custom row renderer function
     */
    constructor(options = {}) {
        super({
            ...options,
            id: options.id || 'data-table'
        });
        
        this.columns = options.columns || [];
        this.emptyMessage = options.emptyMessage || 'No data available.';
        this.rowRenderer = options.rowRenderer;
        
        // Sort settings
        this.sort = {
            column: options.defaultSortColumn,
            direction: options.defaultSortDirection || 'asc'
        };
        
        // Filter settings
        this.filter = {
            text: '',
            fields: options.filterFields || null,
            callback: options.filterCallback || null
        };
        
        // Selection settings
        this.selection = {
            enabled: options.selectable !== false,
            selectedIndex: -1,
            allowMultiple: options.allowMultipleSelection || false,
            selectedRows: []
        };
    }
    
    /**
     * Render the data table
     */
    render() {
        // Create table container if it doesn't exist
        if (!this.elements.container) {
            this.elements.container = document.createElement('div');
            this.elements.container.id = `${this.id}-container`;
            this.elements.container.className = 'table-responsive';
            this.container.appendChild(this.elements.container);
        }
        
        // Create table
        const tableHtml = `
            <table class="table table-hover" id="${this.id}">
                <thead>
                    <tr>
                        ${this.renderTableHeader()}
                    </tr>
                </thead>
                <tbody id="${this.id}-body">
                    ${this.renderTableBody()}
                </tbody>
            </table>
        `;
        
        // Update container
        this.elements.container.innerHTML = tableHtml;
        
        // Store references to DOM elements
        this.elements.table = document.getElementById(this.id);
        this.elements.tbody = document.getElementById(`${this.id}-body`);
        this.elements.headers = this.elements.table.querySelectorAll('th.sortable');
    }
    
    /**
     * Render the table header
     * 
     * @returns {string} HTML for table header
     */
    renderTableHeader() {
        return this.columns.map(column => {
            const isSortable = column.sortable !== false;
            const isActive = this.sort.column === column.key;
            
            const classes = [
                isSortable ? 'sortable' : '',
                isActive ? 'sort-active' : '',
                isActive ? `sort-${this.sort.direction}` : ''
            ].filter(Boolean).join(' ');
            
            return `
                <th 
                    data-sort="${column.key}" 
                    class="${classes}" 
                    style="${column.width ? `width: ${column.width}` : ''}"
                >
                    ${column.label}
                    ${isSortable ? '<i class="bi bi-sort-alpha-down sort-icon"></i>' : ''}
                </th>
            `;
        }).join('');
    }
    
    /**
     * Render the table body
     * 
     * @returns {string} HTML for table body
     */
    renderTableBody() {
        // Apply filtering
        let filteredData = this.data;
        
        if (this.filter.text) {
            filteredData = this.filterData(filteredData);
        }
        
        // Apply sorting
        if (this.sort.column) {
            filteredData = this.sortData(filteredData);
        }
        
        // Check if empty
        if (filteredData.length === 0) {
            return `
                <tr>
                    <td colspan="${this.columns.length}" class="text-center py-4">
                        <p class="mb-0">${this.emptyMessage}</p>
                    </td>
                </tr>
            `;
        }
        
        // Use custom row renderer if provided
        if (typeof this.rowRenderer === 'function') {
            return filteredData.map((item, index) => 
                this.rowRenderer(item, index, this)
            ).join('');
        }
        
        // Default row rendering
        return filteredData.map((item, index) => {
            const isSelected = this.selection.selectedRows.includes(index) || 
                               this.selection.selectedIndex === index;
            
            return `
                <tr class="${isSelected ? 'selected' : ''}" data-index="${index}">
                    ${this.columns.map(column => {
                        // Get cell value
                        let value = item[column.key];
                        
                        // Apply formatter if provided
                        if (column.formatter && typeof column.formatter === 'function') {
                            value = column.formatter(value, item, index);
                        }
                        
                        return `<td>${value !== undefined ? value : ''}</td>`;
                    }).join('')}
                </tr>
            `;
        }).join('');
    }
    
    /**
     * Filter the data
     * 
     * @param {Array} data - Data to filter
     * @returns {Array} Filtered data
     */
    filterData(data) {
        if (!this.filter.text) {
            return data;
        }
        
        // Use custom filter callback if provided
        if (typeof this.filter.callback === 'function') {
            return data.filter(item => this.filter.callback(item, this.filter.text));
        }
        
        // Default filtering on specified fields
        const searchText = this.filter.text.toLowerCase();
        const fields = this.filter.fields || 
                      this.columns.map(column => column.key);
        
        return data.filter(item => {
            return fields.some(field => {
                const value = item[field];
                if (value === undefined || value === null) {
                    return false;
                }
                
                return String(value).toLowerCase().includes(searchText);
            });
        });
    }
    
    /**
     * Sort the data
     * 
     * @param {Array} data - Data to sort
     * @returns {Array} Sorted data
     */
    sortData(data) {
        if (!this.sort.column) {
            return data;
        }
        
        // Find column definition
        const column = this.columns.find(col => col.key === this.sort.column);
        
        // Create compare function
        const compareFunction = (a, b) => {
            // Get values
            let aValue = a[this.sort.column];
            let bValue = b[this.sort.column];
            
            // Use custom sorter if provided
            if (column && column.sorter && typeof column.sorter === 'function') {
                return column.sorter(aValue, bValue, a, b);
            }
            
            // Default sorting
            if (aValue === undefined || aValue === null) {
                return this.sort.direction === 'asc' ? -1 : 1;
            }
            
            if (bValue === undefined || bValue === null) {
                return this.sort.direction === 'asc' ? 1 : -1;
            }
            
            // Type-specific comparison
            if (typeof aValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = String(bValue).toLowerCase();
                return this.sort.direction === 'asc' ? 
                    aValue.localeCompare(bValue) : 
                    bValue.localeCompare(aValue);
            }
            
            // Number comparison
            return this.sort.direction === 'asc' ? 
                aValue - bValue : 
                bValue - aValue;
        };
        
        // Use stable sort
        return this.stableSort(data, compareFunction);
    }
    
    /**
     * Perform a stable sort
     * 
     * @param {Array} array - Array to sort
     * @param {Function} compareFunction - Compare function
     * @returns {Array} Sorted array
     */
    stableSort(array, compareFunction) {
        // Add indices to track original order
        const indexed = array.map((item, index) => [item, index]);
        
        // Sort with original index as tiebreaker
        indexed.sort((a, b) => {
            const compareResult = compareFunction(a[0], b[0]);
            return compareResult === 0 ? a[1] - b[1] : compareResult;
        });
        
        // Extract the sorted items
        return indexed.map(pair => pair[0]);
    }
    
    /**
     * Bind table events
     */
    bindEvents() {
        // Sortable header click
        this.elements.headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                
                // Toggle direction if clicking on the same column
                if (this.sort.column === column) {
                    this.sort.direction = this.sort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    this.sort.column = column;
                    this.sort.direction = 'asc';
                }
                
                // Update table
                this.render();
                
                // Trigger event
                this.trigger('sort', { column, direction: this.sort.direction });
            });
        });
        
        // Row selection
        if (this.selection.enabled) {
            this.elements.tbody.addEventListener('click', event => {
                const row = event.target.closest('tr');
                if (!row || !row.dataset.index) {
                    return;
                }
                
                const index = parseInt(row.dataset.index, 10);
                
                if (this.selection.allowMultiple && event.ctrlKey) {
                    // Toggle selection
                    const selIndex = this.selection.selectedRows.indexOf(index);
                    if (selIndex === -1) {
                        this.selection.selectedRows.push(index);
                    } else {
                        this.selection.selectedRows.splice(selIndex, 1);
                    }
                } else {
                    // Single selection
                    this.selection.selectedIndex = index;
                    this.selection.selectedRows = [index];
                }
                
                // Update display
                this.render();
                
                // Trigger event
                this.trigger('select', { 
                    index, 
                    selectedRows: this.selection.selectedRows,
                    data: this.data[index]
                });
            });
        }
    }
    
    /**
     * Set filter text
     * 
     * @param {string} text - Filter text
     */
    setFilter(text) {
        this.filter.text = text;
        this.render();
        this.trigger('filter', { text });
        return this;
    }
    
    /**
     * Set data
     * 
     * @param {Array} data - New data
     */
    setData(data) {
        this.data = data;
        this.render();
        this.trigger('data', { data });
        return this;
    }
    
    /**
     * Get selected rows
     * 
     * @returns {Array} Selected row data
     */
    getSelected() {
        if (!this.selection.enabled) {
            return [];
        }
        
        if (this.selection.allowMultiple) {
            return this.selection.selectedRows.map(index => this.data[index]);
        }
        
        return this.selection.selectedIndex >= 0 ? 
            [this.data[this.selection.selectedIndex]] : [];
    }
}
```

## Implementation Timeline

### Phase 1: JavaScript Utils & Base Utilities (Week 1)

1. Create unified `utils.js` with all shared functions
2. Remove duplicated functions from templates
3. Update all imports and references
4. Create component base classes

### Phase 2: Service Layer Refactoring (Week 2)

1. Create `BaseResourceService` class
2. Refactor `PromptService` to inherit from base class
3. Refactor `FragmentService` to inherit from base class
4. Write tests for new service structure
5. Update API endpoints to use new services

### Phase 3: Template System (Week 3)

1. Create template macros for common UI components
2. Update templates to use macros
3. Create JavaScript components for complex UI components
4. Update references and integrations

### Phase 4: Quality Assurance & Documentation (Week 4)

1. Comprehensive testing of all changes
2. Verify no functionality loss
3. Update documentation with new patterns
4. Create migration guides for future development
5. Final review and merge

## Testing Strategy

1. **Unit Tests**: Create tests for all refactored services and components
2. **Integration Tests**: Verify end-to-end workflows still function correctly
3. **Manual Testing**: Perform hands-on verification of UI components
4. **Performance Testing**: Ensure refactored code maintains or improves performance

## Conclusion

The proposed implementation plan addresses the major code duplication issues identified in the prompt_manager project. By following a systematic approach to refactoring, we can reduce code duplication, improve maintainability, and create a more consistent codebase while minimizing the risk of introducing new bugs.

The phased approach allows for incremental improvement, with each phase building on the previous one. This makes the refactoring process more manageable and allows for validation at each step.

By implementing these changes, we'll create a more robust and maintainable codebase that adheres to the DRY principle, making future development more efficient and reducing the risk of bugs introduced by inconsistent implementations.
