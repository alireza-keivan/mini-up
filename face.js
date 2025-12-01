// Dashboard functionality - Complete Version with Database Support

// ============================================================================
// Service Control Functions
// ============================================================================

async function startService() {
    if (!confirmAction('Start the face recognition service?')) {
        return;
    }
    
    try {
        const data = await apiRequest('/api/service/start', {
            method: 'POST'
        });
        
        if (data.success) {
            showNotification(data.message, 'success');
            await checkServiceStatus();
        } else {
            showNotification(data.message || 'Failed to start service', 'error');
        }
    } catch (error) {
        showNotification('Error starting service: ' + error.message, 'error');
    }
}

async function restartService() {
    if (!confirmAction('Restart the face recognition service?')) {
        return;
    }
    
    try {
        const data = await apiRequest('/api/service/restart', {
            method: 'POST'
        });
        
        if (data.success) {
            showNotification(data.message, 'success');
            await checkServiceStatus();
        } else {
            showNotification(data.message || 'Failed to restart service', 'error');
        }
    } catch (error) {
        showNotification('Error restarting service: ' + error.message, 'error');
    }
}

async function stopService() {
    if (!confirmAction('Stop the face recognition service?')) {
        return;
    }
    
    try {
        const data = await apiRequest('/api/service/stop', {
            method: 'POST'
        });
        
        if (data.success) {
            showNotification(data.message, 'warning');
            await checkServiceStatus();
        } else {
            showNotification(data.message || 'Failed to stop service', 'error');
        }
    } catch (error) {
        showNotification('Error stopping service: ' + error.message, 'error');
    }
}

// ============================================================================
// Database Dashboard State
// ============================================================================

let dbAutoRefreshInterval = null;
let dbIsAutoRefreshing = false;

// ============================================================================
// Database Health Check
// ============================================================================

async function checkDatabaseHealth() {
    const statusEl = document.getElementById('dbStatus');
    const indicatorEl = document.getElementById('dbStatusIndicator');
    
    if (!statusEl) return; // Not on dashboard page
    
    try {
        const response = await fetch('/api/db/health');
        const result = await response.json();
        
        if (result.success && result.data) {
            const health = result.data;
            if (health.connected) {
                statusEl.textContent = 'Connected';
                statusEl.className = 'status-value status-healthy';
                if (indicatorEl) {
                    indicatorEl.className = 'status-indicator running';
                }
            } else {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status-value status-error';
                if (indicatorEl) {
                    indicatorEl.className = 'status-indicator stopped';
                }
            }
        } else {
            statusEl.textContent = 'Error';
            statusEl.className = 'status-value status-error';
        }
    } catch (error) {
        console.error('Database health check failed:', error);
        if (statusEl) {
            statusEl.textContent = 'Error';
            statusEl.className = 'status-value status-error';
        }
    }
}

// ============================================================================
// Load Statistics
// ============================================================================

async function loadStatistics() {
    const totalLogsEl = document.getElementById('totalLogs');
    const verificationRateEl = document.getElementById('verificationRate');
    const avgConfidenceEl = document.getElementById('avgConfidence');
    
    try {
        const response = await fetch('/api/db/stats');
        const result = await response.json();
        
        if (result.success && result.stats) {
            const stats = result.stats;
            
            if (totalLogsEl) {
                totalLogsEl.textContent = stats.total_logs || 0;
            }
            if (verificationRateEl) {
                const rate = stats.verification_rate || 0;
                verificationRateEl.textContent = rate.toFixed(1) + '%';
            }
            if (avgConfidenceEl) {
                const conf = stats.avg_confidence || 0;
                avgConfidenceEl.textContent = (conf * 100).toFixed(1) + '%';
            }
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
        if (totalLogsEl) totalLogsEl.textContent = '-';
        if (verificationRateEl) verificationRateEl.textContent = '-';
        if (avgConfidenceEl) avgConfidenceEl.textContent = '-';
    }
}

// ============================================================================
// Load Recent Activity
// ============================================================================

async function loadRecentActivity() {
    const container = document.getElementById('recentActivityBody');
    if (!container) return;
    
    const timeRange = document.getElementById('activityTimeRange');
    const minutes = timeRange ? parseInt(timeRange.value) || 60 : 60;
    
    try {
        const response = await fetch(`/api/db/logs/recent?minutes=${minutes}`);
        const result = await response.json();
        
        if (result.success && result.logs) {
            renderActivityTable(result.logs, container);
        } else {
            container.innerHTML = '<tr><td colspan="5" class="text-center">No recent activity</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load recent activity:', error);
        container.innerHTML = '<tr><td colspan="5" class="text-center text-error">Error loading activity</td></tr>';
    }
}

function renderActivityTable(logs, container) {
    if (!logs || logs.length === 0) {
        container.innerHTML = '<tr><td colspan="5" class="text-center">No recent activity</td></tr>';
        return;
    }
    
    let html = '';
    logs.forEach(log => {
        const time = log.timestamp ? new Date(log.timestamp).toLocaleString('fa-IR') : '-';
        const person = log.person_name || 'Unknown';
        const verified = log.is_verified ? '✅ Verified' : '❌ Not Verified';
        const confidence = log.confidence ? (log.confidence * 100).toFixed(1) + '%' : '-';
        const door = log.door_number || '-';
        
        html += `
            <tr>
                <td>${time}</td>
                <td>${person}</td>
                <td>${verified}</td>
                <td>${confidence}</td>
                <td>${door}</td>
            </tr>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================================================
// Load Persons List
// ============================================================================

async function loadPersonsList() {
    const container = document.getElementById('personsListBody');
    if (!container) return;
    
    try {
        const response = await fetch('/api/db/persons');
        const result = await response.json();
        
        if (result.success && result.persons) {
            renderPersonsTable(result.persons, container);
        } else {
            container.innerHTML = '<tr><td colspan="3" class="text-center">No persons found</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load persons:', error);
        container.innerHTML = '<tr><td colspan="3" class="text-center text-error">Error loading persons</td></tr>';
    }
}

function renderPersonsTable(persons, container) {
    if (!persons || persons.length === 0) {
        container.innerHTML = '<tr><td colspan="3" class="text-center">No persons found</td></tr>';
        return;
    }
    
    let html = '';
    persons.forEach(person => {
        const lastSeen = person.last_seen ? new Date(person.last_seen).toLocaleString('fa-IR') : '-';
        html += `
            <tr>
                <td>${person.name}</td>
                <td>${person.recognition_count}</td>
                <td>${lastSeen}</td>
            </tr>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================================================
// Load Full Logs (All Logs Tab)
// ============================================================================

async function loadFullLogs() {
    const container = document.getElementById('fullLogsBody');
    if (!container) return;
    
    const timeRange = document.getElementById('logsTimeRange');
    const hours = timeRange ? parseInt(timeRange.value) || 24 : 24;
    const minutes = hours * 60;
    
    try {
        const response = await fetch(`/api/db/logs?limit=200`);
        const result = await response.json();
        
        if (result.success && result.logs) {
            renderFullLogsTable(result.logs, container);
        } else {
            container.innerHTML = '<tr><td colspan="6" class="text-center">No logs found</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load logs:', error);
        container.innerHTML = '<tr><td colspan="6" class="text-center text-error">Error loading logs</td></tr>';
    }
}

function renderFullLogsTable(logs, container) {
    if (!logs || logs.length === 0) {
        container.innerHTML = '<tr><td colspan="6" class="text-center">No logs found</td></tr>';
        return;
    }
    
    let html = '';
    logs.forEach(log => {
        const time = log.timestamp ? new Date(log.timestamp).toLocaleString('fa-IR') : '-';
        const person = log.person_name || 'Unknown';
        const verified = log.is_verified ? '✅' : '❌';
        const confidence = log.confidence ? (log.confidence * 100).toFixed(1) + '%' : '-';
        const door = log.door_number || '-';
        const image = log.image_filename || '-';
        
        html += `
            <tr>
                <td>${time}</td>
                <td>${person}</td>
                <td>${verified}</td>
                <td>${confidence}</td>
                <td>${door}</td>
                <td>${image}</td>
            </tr>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================================================
// Load Config Snapshots
// ============================================================================

async function loadConfigSnapshots() {
    const container = document.getElementById('snapshotsBody');
    if (!container) return;
    
    try {
        const response = await fetch('/api/db/config-snapshots');
        const result = await response.json();
        
        if (result.success && result.snapshots) {
            renderSnapshotsTable(result.snapshots, container);
        } else {
            container.innerHTML = '<tr><td colspan="3" class="text-center">No snapshots found</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load snapshots:', error);
        container.innerHTML = '<tr><td colspan="3" class="text-center text-error">Error loading snapshots</td></tr>';
    }
}

function renderSnapshotsTable(snapshots, container) {
    if (!snapshots || snapshots.length === 0) {
        container.innerHTML = '<tr><td colspan="3" class="text-center">No snapshots found</td></tr>';
        return;
    }
    
    let html = '';
    snapshots.forEach(snap => {
        const created = snap.created_at ? new Date(snap.created_at).toLocaleString('fa-IR') : '-';
        const description = snap.description || 'No description';
        html += `
            <tr>
                <td>${snap.id}</td>
                <td>${created}</td>
                <td>${description}</td>
            </tr>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================================================
// Save Config Snapshot
// ============================================================================

async function saveConfigSnapshot() {
    const description = prompt('Enter a description for this snapshot (optional):');
    
    try {
        const response = await fetch('/api/db/config-snapshots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: description || 'Manual snapshot' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Config snapshot saved successfully', 'success');
            loadConfigSnapshots();
        } else {
            showNotification(result.message || 'Failed to save snapshot', 'error');
        }
    } catch (error) {
        showNotification('Error saving snapshot: ' + error.message, 'error');
    }
}

// ============================================================================
// Export Functions
// ============================================================================

async function exportLogs(format = 'json') {
    try {
        const response = await fetch('/api/db/logs?limit=1000');
        const result = await response.json();
        
        if (!result.success || !result.logs) {
            showNotification('No logs to export', 'warning');
            return;
        }
        
        let content, filename, mimeType;
        
        if (format === 'csv') {
            content = convertToCSV(result.logs);
            filename = 'recognition_logs.csv';
            mimeType = 'text/csv';
        } else {
            content = JSON.stringify(result.logs, null, 2);
            filename = 'recognition_logs.json';
            mimeType = 'application/json';
        }
        
        downloadFile(content, filename, mimeType);
        showNotification(`Exported ${result.logs.length} logs`, 'success');
        
    } catch (error) {
        showNotification('Error exporting logs: ' + error.message, 'error');
    }
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const rows = [headers.join(',')];
    
    data.forEach(row => {
        const values = headers.map(h => {
            const val = row[h];
            if (val === null || val === undefined) return '';
            if (typeof val === 'object') return JSON.stringify(val);
            return String(val).includes(',') ? `"${val}"` : val;
        });
        rows.push(values.join(','));
    });
    
    return rows.join('\n');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ============================================================================
// Tab Switching
// ============================================================================

function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
        tab.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
// --- continuation of showTab() ---

    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
        selectedTab.style.display = 'block';
    }
    
    // Highlight active button
    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Load data for the selected tab
    if (tabName === 'tabStatistics') {
        loadStatistics();
    } else if (tabName === 'tabRecentActivity') {
        loadRecentActivity();
    } else if (tabName === 'tabPersons') {
        loadPersonsList();
    } else if (tabName === 'tabAllLogs') {
        loadFullLogs();
    } else if (tabName === 'tabSnapshots') {
        loadConfigSnapshots();
    }
}

// ============================================================================
// Auto-refresh for dashboard
// ============================================================================

function toggleAutoRefresh() {
    const checkbox = document.getElementById('autoRefreshToggle');
    if (!checkbox) return;

    if (checkbox.checked) {
        dbIsAutoRefreshing = true;
        dbAutoRefreshInterval = setInterval(() => {
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;

            if (activeTab.id === 'tabStatistics') {
                loadStatistics();
            } else if (activeTab.id === 'tabRecentActivity') {
                loadRecentActivity();
            } else if (activeTab.id === 'tabPersons') {
                loadPersonsList();
            } else if (activeTab.id === 'tabAllLogs') {
                loadFullLogs();
            } else if (activeTab.id === 'tabSnapshots') {
                loadConfigSnapshots();
            }
        }, 5000);

        showNotification('Auto-refresh enabled', 'success');
    } else {
        dbIsAutoRefreshing = false;
        clearInterval(dbAutoRefreshInterval);
        showNotification('Auto-refresh disabled', 'warning');
    }
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Only run DB dashboard logic if DB dashboard elements exist
    if (document.getElementById('dbDashboard')) {
        
        // Initial load
        checkDatabaseHealth();
        loadStatistics();
        loadRecentActivity();
        loadPersonsList();
        loadFullLogs();
        loadConfigSnapshots();
        
        // Tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.getAttribute('data-tab');
                showTab(tabName);
            });
        });

        // Auto refresh toggle
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', toggleAutoRefresh);
        }

        // Time-range selects
        const activityTimeRange = document.getElementById('activityTimeRange');
        if (activityTimeRange) {
            activityTimeRange.addEventListener('change', loadRecentActivity);
        }

        const logsTimeRange = document.getElementById('logsTimeRange');
        if (logsTimeRange) {
            logsTimeRange.addEventListener('change', loadFullLogs);
        }

    }
});
