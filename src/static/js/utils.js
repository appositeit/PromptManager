/**
 * Unified utility functions for the prompt management system.
 */

/**
 * Show a toast notification.
 * 
 * @param {string} message - The message to display
 * @param {string} type - Bootstrap alert type (success, danger, warning, etc.)
 * @param {number} duration - Time in milliseconds to show the toast
 */
function showToast(message, type = 'success', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    
    // MODIFICATION START: Apply custom class for success, default for others
    if (type === 'success') {
        toast.className = 'toast toast-success-subtle';
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header"> <!-- Styled by .toast-success-subtle .toast-header -->
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-dark" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
    } else {
        toast.className = `toast bg-${type} text-white`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
    }
    // MODIFICATION END
    
    // Add to container
    toastContainer.appendChild(toast);
    
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
}

/**
 * Format a date using dayjs relative time.
 * 
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    try {
        return dayjs(dateString).fromNow();
    } catch (error) {
        console.warn('Error formatting date:', error);
        return dateString || 'Unknown';
    }
}

/**
 * Format a date using custom format.
 * 
 * @param {string} dateString - ISO date string
 * @param {string} format - Format string (default: 'YYYY-MM-DD HH:mm:ss')
 * @returns {string} Formatted date
 */
function formatDateWithFormat(dateString, format = 'YYYY-MM-DD HH:mm:ss') {
    try {
        return dayjs(dateString).format(format);
    } catch (error) {
        console.warn('Error formatting date:', error);
        return dateString || 'Unknown';
    }
}

/**
 * Escape HTML special characters in a string.
 * 
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    if (!str) return '';
    
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Perform a stable sort on an array based on a given comparison function.
 * This ensures that equal elements maintain their relative order.
 * 
 * @param {Array} array - The array to sort
 * @param {Function} compareFunction - Function that defines the sort order
 * @returns {Array} The sorted array
 */
function stableSort(array, compareFunction) {
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
 * Convert markdown to HTML.
 * A simple, lightweight markdown converter.
 * 
 * @param {string} markdown - Markdown text to convert
 * @returns {string} HTML representation of the markdown
 */
function markdownToHtml(markdown) {
    if (!markdown) return '';
    
    // Simple markdown to HTML conversion
    return markdown
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/```([a-z]*)\n([\s\S]*?)\n```/g, '<pre><code class="language-$1">$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
        .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
        .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
        .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
        .replace(/^#### (.*?)$/gm, '<h4>$1</h4>')
        .replace(/^##### (.*?)$/gm, '<h5>$1</h5>')
        .replace(/^###### (.*?)$/gm, '<h6>$1</h6>');
}

/**
 * Load data from API endpoint.
 * 
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise} Promise resolving to JSON response
 */
async function fetchApi(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showToast(`API request failed: ${error.message}`, 'danger');
        throw error;
    }
}

// Export all functions for modules that support ES6 imports
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showToast,
        formatDate,
        formatDateWithFormat,
        escapeHtml,
        stableSort,
        markdownToHtml,
        fetchApi
    };
}
