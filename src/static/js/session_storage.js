/**
 * Session Storage Management
 * 
 * This module provides utilities for managing session storage, including
 * viewing storage information, managing artifacts, and viewing logs.
 */

window.SessionStorage = (function() {
    /**
     * Initialize session storage management.
     * 
     * @param {string} sessionId - The session ID
     */
    function initSessionStorage(sessionId) {
    // Load storage info
    loadStorageInfo(sessionId);
    
    // Set up event listeners
    document.getElementById('view-artifacts-btn').addEventListener('click', () => {
        loadArtifacts(sessionId);
    });
    
    document.getElementById('view-logs-btn').addEventListener('click', () => {
        loadLogs(sessionId, 'session');
    });
    
    document.getElementById('upload-artifact-btn').addEventListener('click', () => {
        showUploadArtifactModal(sessionId);
    });
    
    // Set up artifact upload form
    document.getElementById('artifact-upload-form').addEventListener('submit', (e) => {
        e.preventDefault();
        uploadArtifact(sessionId);
    });
}

    /**
     * Load storage information for a session.
     * 
     * @param {string} sessionId - The session ID
     */
    async function loadStorageInfo(sessionId) {
    try {
        const token = localStorage.getItem('authToken');
        
        if (!token) {
            showNotification('error', 'Authentication required');
            return;
        }
        
        // Show loading state
        document.getElementById('storage-info-container').innerHTML = `
            <div class="d-flex justify-content-center my-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Fetch storage info
        const response = await fetch(`/api/sessions/${sessionId}/storage`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load storage info: ${response.status} ${response.statusText}`);
        }
        
        const storageInfo = await response.json();
        
        // Update UI
        updateStorageInfoUI(sessionId, storageInfo);
        
    } catch (error) {
        console.error('Error loading storage info:', error);
        
        document.getElementById('storage-info-container').innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill"></i>
                Error loading storage information: ${error.message}
            </div>
        `;
    }
}

    /**
     * Update the storage info UI.
     * 
     * @param {string} sessionId - The session ID
     * @param {Object} storageInfo - The storage info data
     */
    function updateStorageInfoUI(sessionId, storageInfo) {
    const container = document.getElementById('storage-info-container');
    
    // Create storage info display
    let html = `
        <div class="row mt-3">
            <div class="col-md-6">
                <h5>Storage Directories</h5>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Path</th>
                            <th>Size</th>
                            <th>Files</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Add directory info
    for (const [dirType, dirInfo] of Object.entries(storageInfo)) {
        if (dirType === 'config_settings') {continue;}
        
        // const exists = dirInfo.exists; // Not currently used
        const path = dirInfo.path;
        const size = dirInfo.size_formatted || '0 B';
        const fileCount = dirInfo.file_count || 0;
        
        html += `
            <tr>
                <td>${dirType}</td>
                <td><code>${path}</code></td>
                <td>${size}</td>
                <td>${fileCount}</td>
            </tr>
        `;
    }
    
    html += `
                    </tbody>
                </table>
            </div>
            <div class="col-md-6">
                <h5>Storage Configuration</h5>
                <div class="card">
                    <div class="card-body">
    `;
    
    // Add config settings
    if (storageInfo.config_settings) {
        html += `
            <div class="mb-3">
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="persist-messages" 
                        ${storageInfo.config_settings.persist_messages ? 'checked' : ''} disabled>
                    <label class="form-check-label" for="persist-messages">Persist Messages</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="persist-tasks" 
                        ${storageInfo.config_settings.persist_tasks ? 'checked' : ''} disabled>
                    <label class="form-check-label" for="persist-tasks">Persist Tasks</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="persist-artifacts" 
                        ${storageInfo.config_settings.persist_artifacts ? 'checked' : ''} disabled>
                    <label class="form-check-label" for="persist-artifacts">Persist Artifacts</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="auto-create-dirs" 
                        ${storageInfo.config_settings.auto_create_dirs ? 'checked' : ''} disabled>
                    <label class="form-check-label" for="auto-create-dirs">Auto-Create Directories</label>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-info" role="alert">
                <i class="bi bi-info-circle-fill"></i>
                No storage configuration information available.
            </div>
        `;
    }
    
    html += `
                    </div>
                </div>
                
                <div class="mt-3">
                    <h5>Actions</h5>
                    <div class="btn-group" role="group">
                        <button id="view-artifacts-btn" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-archive"></i> View Artifacts
                        </button>
                        <button id="view-logs-btn" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-journal-text"></i> View Logs
                        </button>
                        <button id="upload-artifact-btn" class="btn btn-sm btn-outline-success">
                            <i class="bi bi-upload"></i> Upload Artifact
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="storage-content-container" class="mt-4"></div>
    `;
    
    container.innerHTML = html;
    
    // Re-attach event listeners
    document.getElementById('view-artifacts-btn').addEventListener('click', () => {
        loadArtifacts(sessionId);
    });
    
    document.getElementById('view-logs-btn').addEventListener('click', () => {
        loadLogs(sessionId, 'session');
    });
    
    document.getElementById('upload-artifact-btn').addEventListener('click', () => {
        showUploadArtifactModal(sessionId);
    });
}

    /**
     * Load artifacts for a session.
     * 
     * @param {string} sessionId - The session ID
     */
    async function loadArtifacts(sessionId) {
    try {
        const token = localStorage.getItem('authToken');
        
        if (!token) {
            showNotification('error', 'Authentication required');
            return;
        }
        
        // Show loading state
        const container = document.getElementById('storage-content-container');
        container.innerHTML = `
            <div class="d-flex justify-content-center my-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Fetch artifacts
        const response = await fetch(`/api/sessions/${sessionId}/storage/artifacts`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load artifacts: ${response.status} ${response.statusText}`);
        }
        
        const artifacts = await response.json();
        
        // Update UI
        updateArtifactsUI(sessionId, artifacts);
        
    } catch (error) {
        console.error('Error loading artifacts:', error);
        
        document.getElementById('storage-content-container').innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill"></i>
                Error loading artifacts: ${error.message}
            </div>
        `;
    }
}

    /**
     * Update the artifacts UI.
     * 
     * @param {string} sessionId - The session ID
     * @param {Array} artifacts - The artifacts data
     */
    function updateArtifactsUI(sessionId, artifacts) {
    const container = document.getElementById('storage-content-container');
    
    // Create artifacts display
    let html = `
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">Session Artifacts</h5>
            </div>
            <div class="card-body">
    `;
    
    if (artifacts.length === 0) {
        html += `
            <div class="alert alert-info" role="alert">
                <i class="bi bi-info-circle-fill"></i>
                No artifacts found for this session.
            </div>
        `;
    } else {
        html += `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Size</th>
                            <th>Created</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add artifact rows
        artifacts.forEach(artifact => {
            // Determine file type
            let fileType = 'Unknown';
            let fileIcon = 'bi-file';
            
            if (artifact.metadata && artifact.metadata.content_type) {
                fileType = artifact.metadata.content_type;
                
                if (fileType.startsWith('image/')) {
                    fileIcon = 'bi-file-image';
                } else if (fileType.startsWith('text/')) {
                    fileIcon = 'bi-file-text';
                } else if (fileType.startsWith('application/json')) {
                    fileIcon = 'bi-file-code';
                } else if (fileType.startsWith('application/pdf')) {
                    fileIcon = 'bi-file-pdf';
                }
            } else if (artifact.id.includes('.')) {
                const extension = artifact.id.split('.').pop().toLowerCase();
                
                if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(extension)) {
                    fileType = `image/${extension}`;
                    fileIcon = 'bi-file-image';
                } else if (['txt', 'md', 'csv'].includes(extension)) {
                    fileType = `text/${extension}`;
                    fileIcon = 'bi-file-text';
                } else if (extension === 'json') {
                    fileType = 'application/json';
                    fileIcon = 'bi-file-code';
                } else if (extension === 'pdf') {
                    fileType = 'application/pdf';
                    fileIcon = 'bi-file-pdf';
                }
            }
            
            // Format size
            const size = artifact.size;
            let sizeStr = '';
            
            if (size < 1024) {
                sizeStr = `${size} B`;
            } else if (size < 1024*1024) {
                sizeStr = `${(size/1024).toFixed(1)} KB`;
            } else if (size < 1024*1024*1024) {
                sizeStr = `${(size/(1024*1024)).toFixed(1)} MB`;
            } else {
                sizeStr = `${(size/(1024*1024*1024)).toFixed(1)} GB`;
            }
            
            // Format date
            const created = new Date(artifact.created).toLocaleString();
            
            // Create row
            html += `
                <tr>
                    <td>
                        <i class="${fileIcon} me-2"></i>
                        ${artifact.id}
                    </td>
                    <td>${sizeStr}</td>
                    <td>${created}</td>
                    <td>${fileType}</td>
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            <a href="/api/sessions/${sessionId}/storage/artifacts/${artifact.id}" 
                               class="btn btn-outline-primary" target="_blank">
                                <i class="bi bi-download"></i>
                            </a>
                            <button class="btn btn-outline-danger delete-artifact-btn" 
                                    data-artifact-id="${artifact.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-artifact-btn').forEach(button => {
        button.addEventListener('click', () => {
            const artifactId = button.getAttribute('data-artifact-id');
            deleteArtifact(sessionId, artifactId);
        });
    });
}

    /**
     * Load logs for a session.
     * 
     * @param {string} sessionId - The session ID
     * @param {string} logType - The type of log
     */
    async function loadLogs(sessionId, logType) {
    try {
        const token = localStorage.getItem('authToken');
        
        if (!token) {
            showNotification('error', 'Authentication required');
            return;
        }
        
        // Show loading state
        const container = document.getElementById('storage-content-container');
        container.innerHTML = `
            <div class="d-flex justify-content-center my-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Fetch logs
        const response = await fetch(`/api/sessions/${sessionId}/storage/logs/${logType}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load logs: ${response.status} ${response.statusText}`);
        }
        
        const logs = await response.json();
        
        // Update UI
        updateLogsUI(sessionId, logs);
        
    } catch (error) {
        console.error('Error loading logs:', error);
        
        document.getElementById('storage-content-container').innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill"></i>
                Error loading logs: ${error.message}
            </div>
        `;
    }
}

    /**
     * Update the logs UI.
     * 
     * @param {string} sessionId - The session ID
     * @param {Object} logs - The logs data
     */
    function updateLogsUI(sessionId, logs) {
    const container = document.getElementById('storage-content-container');
    
    // Create logs display
    let html = `
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">Session Logs (${logs.log_type})</h5>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary log-type-btn" data-log-type="session">
                        Session
                    </button>
                    <button class="btn btn-outline-primary log-type-btn" data-log-type="messages">
                        Messages
                    </button>
                    <button class="btn btn-outline-primary log-type-btn" data-log-type="artifacts">
                        Artifacts
                    </button>
                </div>
            </div>
            <div class="card-body">
    `;
    
    if (logs.entries.length === 0) {
        html += `
            <div class="alert alert-info" role="alert">
                <i class="bi bi-info-circle-fill"></i>
                No log entries found for this session.
            </div>
        `;
    } else {
        html += `
            <div class="log-container bg-dark text-light p-3" style="max-height: 400px; overflow-y: auto; font-family: monospace;">
        `;
        
        // Add log entries
        logs.entries.forEach(entry => {
            // Format the entry
            let formattedEntry = entry;
            
            // Highlight timestamps
            formattedEntry = formattedEntry.replace(/\[(.*?)\]/, '<span class="text-info">[$1]</span>');
            
            // Highlight other parts
            if (formattedEntry.includes('ERROR')) {
                formattedEntry = formattedEntry.replace(/ERROR/g, '<span class="text-danger">ERROR</span>');
            }
            if (formattedEntry.includes('WARNING')) {
                formattedEntry = formattedEntry.replace(/WARNING/g, '<span class="text-warning">WARNING</span>');
            }
            if (formattedEntry.includes('INFO')) {
                formattedEntry = formattedEntry.replace(/INFO/g, '<span class="text-info">INFO</span>');
            }
            
            html += `<div>${formattedEntry}</div>`;
        });
        
        html += `
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Add event listeners for log type buttons
    document.querySelectorAll('.log-type-btn').forEach(button => {
        button.addEventListener('click', () => {
            const logType = button.getAttribute('data-log-type');
            loadLogs(sessionId, logType);
        });
    });
}

    /**
     * Show the upload artifact modal.
     * 
     * @param {string} sessionId - The session ID
     */
    function showUploadArtifactModal(_sessionId) {
    // Get the modal
    const modal = new bootstrap.Modal(document.getElementById('upload-artifact-modal'));
    
    // Reset the form
    document.getElementById('artifact-upload-form').reset();
    
    // Show the modal
    modal.show();
}

    /**
     * Upload an artifact.
     * 
     * @param {string} sessionId - The session ID
     */
    async function uploadArtifact(sessionId) {
    try {
        const token = localStorage.getItem('authToken');
        
        if (!token) {
            showNotification('error', 'Authentication required');
            return;
        }
        
        // Get form data
        const fileInput = document.getElementById('artifact-file');
        const artifactId = document.getElementById('artifact-id').value.trim();
        
        if (fileInput.files.length === 0) {
            showNotification('error', 'Please select a file to upload');
            return;
        }
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        if (artifactId) {
            formData.append('artifact_id', artifactId);
        }
        
        // Show loading state
        const uploadButton = document.getElementById('upload-artifact-submit');
        uploadButton.disabled = true;
        uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
        
        // Upload artifact
        const response = await fetch(`/api/sessions/${sessionId}/storage/artifacts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Failed to upload artifact: ${response.status} ${response.statusText}`);
        }
        
        // const result = await response.json(); // Response not currently used
        
        // Show success message
        showNotification('success', 'Artifact uploaded successfully');
        
        // Hide modal
        bootstrap.Modal.getInstance(document.getElementById('upload-artifact-modal')).hide();
        
        // Reload artifacts
        loadArtifacts(sessionId);
        
    } catch (error) {
        console.error('Error uploading artifact:', error);
        showNotification('error', `Error uploading artifact: ${error.message}`);
    } finally {
        // Reset button
        const uploadButton = document.getElementById('upload-artifact-submit');
        uploadButton.disabled = false;
        uploadButton.innerHTML = 'Upload';
    }
}

    /**
     * Delete an artifact.
     * 
     * @param {string} sessionId - The session ID
     * @param {string} artifactId - The artifact ID
     */
    async function deleteArtifact(sessionId, artifactId) {
    if (!confirm(`Are you sure you want to delete the artifact "${artifactId}"?`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem('authToken');
        
        if (!token) {
            showNotification('error', 'Authentication required');
            return;
        }
        
        // Delete artifact
        const response = await fetch(`/api/sessions/${sessionId}/storage/artifacts/${artifactId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete artifact: ${response.status} ${response.statusText}`);
        }
        
        // Show success message
        showNotification('success', 'Artifact deleted successfully');
        
        // Reload artifacts
        loadArtifacts(sessionId);
        
    } catch (error) {
        console.error('Error deleting artifact:', error);
        showNotification('error', `Error deleting artifact: ${error.message}`);
    }
}
    
    // Public API
    return {
        initSessionStorage,
        loadStorageInfo,
        updateStorageInfoUI,
        loadArtifacts,
        updateArtifactsUI,
        loadLogs,
        updateLogsUI,
        showUploadArtifactModal,
        uploadArtifact,
        deleteArtifact
    };
})();

// Expose functions globally for backward compatibility
window.initSessionStorage = window.SessionStorage.initSessionStorage;
window.loadStorageInfo = window.SessionStorage.loadStorageInfo;
window.updateStorageInfoUI = window.SessionStorage.updateStorageInfoUI;
window.loadArtifacts = window.SessionStorage.loadArtifacts;
window.updateArtifactsUI = window.SessionStorage.updateArtifactsUI;
window.loadLogs = window.SessionStorage.loadLogs;
window.updateLogsUI = window.SessionStorage.updateLogsUI;
window.showUploadArtifactModal = window.SessionStorage.showUploadArtifactModal;
window.uploadArtifact = window.SessionStorage.uploadArtifact;
window.deleteArtifact = window.SessionStorage.deleteArtifact;
