/**
 * Functions for managing prompt directories.
 * These functions help with refreshing and managing directories.
 */

/**
 * Reload prompts from a specific directory.
 * 
 * @param {string} directoryPath - Path of the directory to reload
 * @returns {Promise} Promise that resolves when the reload is complete
 */
function reloadDirectory(directoryPath) {
    return fetch(`/api/prompts/directories/${encodeURIComponent(directoryPath)}/reload`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to reload directory: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Directory reload result:', data);
        return data;
    });
}

/**
 * Reload all prompts from all directories.
 * 
 * @returns {Promise} Promise that resolves when the reload is complete
 */
function reloadAllPrompts() {
    return fetch('/api/prompts/reload', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to reload prompts: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Prompts reload result:', data);
        return data;
    });
}

/**
 * Toggle a directory's enabled status.
 * 
 * @param {string} directoryPath - Path of the directory to toggle
 * @param {boolean} currentStatus - Current enabled status
 * @returns {Promise} Promise that resolves when the toggle is complete
 */
function toggleDirectoryStatus(directoryPath, currentStatus) {
    return fetch(`/api/prompts/directories/${encodeURIComponent(directoryPath)}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            enabled: !currentStatus
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to toggle directory status: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Directory toggle result:', data);
        return data;
    });
}

/**
 * Update a directory's properties.
 * 
 * @param {string} directoryPath - Path of the directory to update
 * @param {object} updateData - Data to update (name, description, etc.)
 * @returns {Promise} Promise that resolves when the update is complete
 */
function updateDirectory(directoryPath, updateData) {
    return fetch(`/api/prompts/directories/${encodeURIComponent(directoryPath)}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to update directory: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Directory update result:', data);
        return data;
    });
}
