/**
 * Toast manager component for displaying notifications.
 */

class ToastManager {
    /**
     * Constructor for ToastManager
     * 
     * @param {Object} options - Component options
     * @param {string} options.containerId - Toast container ID (default: 'toast-container')
     * @param {string} options.position - Toast position (default: 'bottom-end')
     */
    constructor(options = {}) {
        this.containerId = options.containerId || 'toast-container';
        this.position = options.position || 'bottom-end';
        this.container = null;
        
        // Initialize container
        this.getContainer();
    }
    
    /**
     * Get or create the toast container
     * 
     * @returns {HTMLElement} Toast container element
     */
    getContainer() {
        if (this.container) {
            return this.container;
        }
        
        // Check if container already exists
        let container = document.getElementById(this.containerId);
        
        // Create container if it doesn't exist
        if (!container) {
            container = document.createElement('div');
            container.id = this.containerId;
            
            // Set position classes based on position option
            if (this.position === 'top-start') {
                container.className = 'toast-container position-fixed top-0 start-0 p-3';
            } else if (this.position === 'top-center') {
                container.className = 'toast-container position-fixed top-0 start-50 translate-middle-x p-3';
            } else if (this.position === 'top-end') {
                container.className = 'toast-container position-fixed top-0 end-0 p-3';
            } else if (this.position === 'middle-start') {
                container.className = 'toast-container position-fixed top-50 start-0 translate-middle-y p-3';
            } else if (this.position === 'middle-center') {
                container.className = 'toast-container position-fixed top-50 start-50 translate-middle p-3';
            } else if (this.position === 'middle-end') {
                container.className = 'toast-container position-fixed top-50 end-0 translate-middle-y p-3';
            } else if (this.position === 'bottom-start') {
                container.className = 'toast-container position-fixed bottom-0 start-0 p-3';
            } else if (this.position === 'bottom-center') {
                container.className = 'toast-container position-fixed bottom-0 start-50 translate-middle-x p-3';
            } else { // Default: bottom-end
                container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            }
            
            document.body.appendChild(container);
        }
        
        this.container = container;
        return container;
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
        const container = this.getContainer();
        
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
        container.appendChild(toast);
        
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

// For browser environments, make showToast function globally available for backward compatibility
window.showToast = (message, type = 'success', duration = 3000) => {
    return toastManager.show(message, type, duration);
};

// Make classes available globally
window.ToastManager = ToastManager;
window.toastManager = toastManager;
