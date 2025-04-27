/**
 * Dashboard JavaScript
 * :TechnologyVersion: JavaScript ES6+
 * :Context: Client-side functionality for system monitoring dashboard
 */

// Dashboard Global State
const dashboardState = {
    metrics: null,
    lastUpdated: null,
    isLoading: false,
    refreshInterval: config.refreshInterval,
    refreshTimer: null
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

/**
 * Initialize the dashboard components and listeners
 */
function initDashboard() {
    // Set up refresh interval selector
    const refreshSelector = document.getElementById('refreshInterval');
    if (refreshSelector) {
        refreshSelector.value = dashboardState.refreshInterval;
        refreshSelector.addEventListener('change', function() {
            updateRefreshInterval(parseInt(this.value));
        });
    }

    // Set up action buttons
    setupActionButtons();
    
    // Initialize charts
    initCharts();
    
    // Load initial data
    loadDashboardData();
    
    // Start the auto-refresh timer
    startRefreshTimer();
}

/**
 * Set up event listeners for action buttons
 */
function setupActionButtons() {
    // Refresh database button
    const refreshDatabaseBtn = document.getElementById('refreshDatabaseBtn');
    if (refreshDatabaseBtn) {
        refreshDatabaseBtn.addEventListener('click', () => {
            loadDatabaseStats();
        });
    }
    
    // Refresh pipeline button
    const refreshPipelineBtn = document.getElementById('refreshPipelineBtn');
    if (refreshPipelineBtn) {
        refreshPipelineBtn.addEventListener('click', () => {
            loadPipelineMetrics();
        });
    }
}

/**
 * Initialize Chart.js charts
 */
function initCharts() {
    // CPU Gauge
    const cpuGauge = document.getElementById('cpuGauge');
    if (cpuGauge) {
        dashboardState.charts = dashboardState.charts || {};
        dashboardState.charts.cpuGauge = new Chart(cpuGauge, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#3498db', '#ecf0f1']
                }]
            },
            options: {
                cutout: '70%',
                responsive: true,
                maintainAspectRatio: false,
                circumference: 270,
                rotation: 135,
                plugins: {
                    tooltip: { enabled: false },
                    legend: { display: false }
                }
            }
        });
    }
    
    // Memory Gauge
    const memoryGauge = document.getElementById('memoryGauge');
    if (memoryGauge) {
        dashboardState.charts = dashboardState.charts || {};
        dashboardState.charts.memoryGauge = new Chart(memoryGauge, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#2ecc71', '#ecf0f1']
                }]
            },
            options: {
                cutout: '70%',
                responsive: true,
                maintainAspectRatio: false,
                circumference: 270,
                rotation: 135,
                plugins: {
                    tooltip: { enabled: false },
                    legend: { display: false }
                }
            }
        });
    }
    
    // Disk Gauge
    const diskGauge = document.getElementById('diskGauge');
    if (diskGauge) {
        dashboardState.charts = dashboardState.charts || {};
        dashboardState.charts.diskGauge = new Chart(diskGauge, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#f39c12', '#ecf0f1']
                }]
            },
            options: {
                cutout: '70%',
                responsive: true,
                maintainAspectRatio: false,
                circumference: 270,
                rotation: 135,
                plugins: {
                    tooltip: { enabled: false },
                    legend: { display: false }
                }
            }
        });
    }
    
    // Initialize pipeline charts
    initPipelineCharts();
}

/**
 * Initialize pipeline performance charts
 */
function initPipelineCharts() {
    // Processing Rates Chart
    const processingRatesChart = document.getElementById('processingRatesChart');
    if (processingRatesChart) {
        dashboardState.charts = dashboardState.charts || {};
        dashboardState.charts.processingRates = new Chart(processingRatesChart, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Items per Second',
                    data: [],
                    backgroundColor: '#3498db'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Items per Second'
                        }
                    }
                }
            }
        });
    }
    
    // Error Rates Chart
    const errorRatesChart = document.getElementById('errorRatesChart');
    if (errorRatesChart) {
        dashboardState.charts = dashboardState.charts || {};
        dashboardState.charts.errorRates = new Chart(errorRatesChart, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Error Count (24h)',
                    data: [],
                    backgroundColor: '#e74c3c'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Error Count'
                        }
                    }
                }
            }
        });
    }
}

/**
 * Load all dashboard data
 */
function loadDashboardData() {
    dashboardState.isLoading = true;
    
    fetch(config.apiEndpoints.metrics)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            dashboardState.metrics = data;
            dashboardState.lastUpdated = new Date();
            updateDashboard(data);
            dashboardState.isLoading = false;
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            dashboardState.isLoading = false;
            showError('Failed to load dashboard data. See console for details.');
        });
}

/**
 * Load database statistics
 */
function loadDatabaseStats() {
    fetch(config.apiEndpoints.databaseStats)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (dashboardState.metrics) {
                dashboardState.metrics.database = data;
            }
            updateDatabaseSection(data);
        })
        .catch(error => {
            console.error('Error fetching database stats:', error);
            showError('Failed to load database statistics. See console for details.');
        });
}

/**
 * Load pipeline metrics
 */
function loadPipelineMetrics() {
    fetch(config.apiEndpoints.pipelineMetrics)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (dashboardState.metrics) {
                dashboardState.metrics.pipeline = data;
            }
            updatePipelineSection(data);
        })
        .catch(error => {
            console.error('Error fetching pipeline metrics:', error);
            showError('Failed to load pipeline metrics. See console for details.');
        });
}

/**
 * Update the entire dashboard with new data
 * @param {Object} data - The complete metrics data
 */
function updateDashboard(data) {
    // Update timestamp
    updateLastUpdatedTime();
    
    // Update overall system status
    updateSystemStatus(data.system_status);
    
    // Update sections
    if (data.database) {
        updateDatabaseSection(data.database);
    }
    
    if (data.pipeline) {
        updatePipelineSection(data.pipeline);
    }
    
    if (data.system) {
        updateSystemHealthSection(data.system);
    }
}

/**
 * Update the system status indicator
 * @param {string} status - The system status (healthy, warning, critical)
 */
function updateSystemStatus(status) {
    const statusIndicator = document.getElementById('systemStatusIndicator');
    if (!statusIndicator) return;
    
    // Remove previous status classes
    statusIndicator.classList.remove('status-healthy', 'status-warning', 'status-critical');
    
    // Set the current status
    const statusText = statusIndicator.querySelector('.status-text');
    
    if (status === 'healthy') {
        statusIndicator.dataset.status = 'healthy';
        if (statusText) statusText.textContent = 'System Status: Healthy';
    } else if (status === 'warning') {
        statusIndicator.dataset.status = 'warning';
        if (statusText) statusText.textContent = 'System Status: Warning';
    } else if (status === 'critical') {
        statusIndicator.dataset.status = 'critical';
        if (statusText) statusText.textContent = 'System Status: Critical';
    } else {
        statusIndicator.dataset.status = 'unknown';
        if (statusText) statusText.textContent = 'System Status: Unknown';
    }
}

/**
 * Update the system health section with new data
 * @param {Object} data - The system health data
 */
function updateSystemHealthSection(data) {
    // Update CPU gauge
    if (data.cpu && dashboardState.charts && dashboardState.charts.cpuGauge) {
        const cpuUsage = data.cpu.average_usage || 0;
        dashboardState.charts.cpuGauge.data.datasets[0].data = [cpuUsage, 100 - cpuUsage];
        dashboardState.charts.cpuGauge.update();
        
        // Update CPU value and details
        const cpuValue = document.getElementById('cpuValue');
        if (cpuValue) cpuValue.textContent = `${Math.round(cpuUsage)}%`;
        
        const cpuCores = document.getElementById('cpuCores');
        if (cpuCores) cpuCores.textContent = data.cpu.core_count || 'N/A';
        
        const cpuLoad = document.getElementById('cpuLoad');
        if (cpuLoad) cpuLoad.textContent = `${Math.round(cpuUsage)}%`;
    }
    
    // Update Memory gauge
    if (data.memory && dashboardState.charts && dashboardState.charts.memoryGauge) {
        const memoryUsage = data.memory.percent || 0;
        dashboardState.charts.memoryGauge.data.datasets[0].data = [memoryUsage, 100 - memoryUsage];
        dashboardState.charts.memoryGauge.update();
        
        // Update Memory value and details
        const memoryValue = document.getElementById('memoryValue');
        if (memoryValue) memoryValue.textContent = `${Math.round(memoryUsage)}%`;
        
        const memoryTotal = document.getElementById('memoryTotal');
        if (memoryTotal) memoryTotal.textContent = formatBytes(data.memory.total);
        
        const memoryAvailable = document.getElementById('memoryAvailable');
        if (memoryAvailable) memoryAvailable.textContent = formatBytes(data.memory.available);
    }
    
    // Update Disk gauge (using average if multiple disks)
    if (data.disk && dashboardState.charts && dashboardState.charts.diskGauge) {
        let diskUsage = 0;
        let diskTotal = 0;
        let diskFree = 0;
        let count = 0;
        
        // Calculate average disk usage
        for (const [partition, info] of Object.entries(data.disk)) {
            if (info.percent) {
                diskUsage += info.percent;
                diskTotal += info.total || 0;
                diskFree += info.free || 0;
                count++;
            }
        }
        
        if (count > 0) {
            diskUsage = diskUsage / count;
        }
        
        dashboardState.charts.diskGauge.data.datasets[0].data = [diskUsage, 100 - diskUsage];
        dashboardState.charts.diskGauge.update();
        
        // Update Disk value and details
        const diskValue = document.getElementById('diskValue');
        if (diskValue) diskValue.textContent = `${Math.round(diskUsage)}%`;
        
        const diskTotalElem = document.getElementById('diskTotal');
        if (diskTotalElem) diskTotalElem.textContent = formatBytes(diskTotal);
        
        const diskFreeElem = document.getElementById('diskFree');
        if (diskFreeElem) diskFreeElem.textContent = formatBytes(diskFree);
    }
    
    // Update recent errors
    if (data.recent_errors) {
        const errorsList = document.getElementById('recentErrorsList');
        if (errorsList) {
            errorsList.innerHTML = '';
            
            if (data.recent_errors.length === 0) {
                const li = document.createElement('li');
                li.className = 'error-item placeholder';
                li.textContent = 'No recent errors';
                errorsList.appendChild(li);
            } else {
                data.recent_errors.forEach(error => {
                    const li = document.createElement('li');
                    li.className = 'error-item error';
                    
                    const timeSpan = document.createElement('span');
                    timeSpan.className = 'error-time';
                    timeSpan.textContent = formatTimestamp(error.timestamp);
                    
                    const componentSpan = document.createElement('span');
                    componentSpan.className = 'error-component';
                    componentSpan.textContent = error.component || 'Unknown';
                    
                    const messagePara = document.createElement('p');
                    messagePara.textContent = error.error || 'No error message';
                    
                    li.appendChild(timeSpan);
                    li.appendChild(componentSpan);
                    li.appendChild(messagePara);
                    errorsList.appendChild(li);
                });
            }
        }
    }
}

/**
 * Update the database section with new data
 * @param {Object} data - The database statistics data
 */
function updateDatabaseSection(data) {
    // Update connection status
    const dbConnectionStatus = document.getElementById('dbConnectionStatus');
    if (dbConnectionStatus) {
        const statusDot = dbConnectionStatus.querySelector('.status-dot');
        const statusText = dbConnectionStatus.querySelector('.status-text');
        
        if (data.connection_status === 'connected') {
            if (statusDot) statusDot.style.backgroundColor = 'var(--status-healthy)';
            if (statusText) statusText.textContent = 'Database Status: Connected';
        } else {
            if (statusDot) statusDot.style.backgroundColor = 'var(--status-critical)';
            if (statusText) statusText.textContent = 'Database Status: Disconnected';
        }
    }
    
    // Update table counts
    if (data.table_counts) {
        const tableCountsTable = document.getElementById('tableCountsTable');
        const tableSelector = document.getElementById('tableSelector');
        
        if (tableCountsTable) {
            const tbody = tableCountsTable.querySelector('tbody');
            if (tbody) {
                tbody.innerHTML = '';
                
                if (Object.keys(data.table_counts).length === 0) {
                    const tr = document.createElement('tr');
                    tr.className = 'placeholder-row';
                    const td = document.createElement('td');
                    td.colSpan = 3;
                    td.textContent = 'No tables found';
                    tr.appendChild(td);
                    tbody.appendChild(tr);
                } else {
                    // Also update the table selector
                    if (tableSelector) {
                        // Save current selection
                        const currentValue = tableSelector.value;
                        tableSelector.innerHTML = '<option value="">Select a table</option>';
                        
                        for (const [table, count] of Object.entries(data.table_counts)) {
                            // Update table counts table
                            const tr = document.createElement('tr');
                            
                            const nameTd = document.createElement('td');
                            nameTd.textContent = table;
                            
                            const countTd = document.createElement('td');
                            countTd.textContent = count;
                            
                            const actionsTd = document.createElement('td');
                            const viewBtn = document.createElement('button');
                            viewBtn.className = 'action-button secondary-btn';
                            viewBtn.textContent = 'View Data';
                            viewBtn.dataset.table = table;
                            viewBtn.addEventListener('click', () => {
                                tableSelector.value = table;
                                updateRecentData(table, data.recent_data);
                            });
                            actionsTd.appendChild(viewBtn);
                            
                            tr.appendChild(nameTd);
                            tr.appendChild(countTd);
                            tr.appendChild(actionsTd);
                            tbody.appendChild(tr);
                            
                            // Add to selector
                            const option = document.createElement('option');
                            option.value = table;
                            option.textContent = table;
                            tableSelector.appendChild(option);
                        }
                        
                        // Restore selection if possible
                        if (currentValue && Array.from(tableSelector.options).some(opt => opt.value === currentValue)) {
                            tableSelector.value = currentValue;
                        }
                    }
                }
            }
        }
        
        // Set up table selector event listener
        if (tableSelector && !tableSelector.hasListener) {
            tableSelector.addEventListener('change', function() {
                if (this.value) {
                    updateRecentData(this.value, data.recent_data);
                }
            });
            tableSelector.hasListener = true;
        }
    }
    
    // If a table is selected, update its recent data
    const tableSelector = document.getElementById('tableSelector');
    if (tableSelector && tableSelector.value && data.recent_data) {
        updateRecentData(tableSelector.value, data.recent_data);
    }
}

/**
 * Update recent data table for a specific table
 * @param {string} tableName - The name of the selected table
 * @param {Object} recentData - Object containing recent data for all tables
 */
function updateRecentData(tableName, recentData) {
    const recentDataTable = document.getElementById('recentDataTable');
    if (!recentDataTable) return;
    
    const tbody = recentDataTable.querySelector('tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!recentData || !recentData[tableName] || recentData[tableName].length === 0) {
        const tr = document.createElement('tr');
        tr.className = 'placeholder-row';
        const td = document.createElement('td');
        td.colSpan = 3;
        td.textContent = 'No recent data available';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }
    
    // Add rows for each recent data item
    recentData[tableName].forEach(item => {
        const tr = document.createElement('tr');
        
        // ID column (use id, _id, or first property)
        const idTd = document.createElement('td');
        const idField = item.id || item._id || Object.keys(item)[0];
        idTd.textContent = item[idField] || 'N/A';
        
        // Data column (show a few key fields)
        const dataTd = document.createElement('td');
        const dataFields = Object.keys(item).filter(k => 
            k !== 'id' && k !== '_id' && k !== 'created_at' && k !== 'updated_at');
        if (dataFields.length > 0) {
            const dataStr = dataFields.slice(0, 3).map(field => 
                `${field}: ${JSON.stringify(item[field])}`).join(', ');
            dataTd.textContent = dataStr;
        } else {
            dataTd.textContent = 'No data fields';
        }
        
        // Timestamp column
        const timeTd = document.createElement('td');
        if (item.created_at || item.updated_at) {
            timeTd.textContent = formatTimestamp(item.created_at || item.updated_at);
        } else {
            timeTd.textContent = 'Unknown';
        }
        
        tr.appendChild(idTd);
        tr.appendChild(dataTd);
        tr.appendChild(timeTd);
        tbody.appendChild(tr);
    });
}

/**
 * Update the pipeline section with new data
 * @param {Object} data - The pipeline metrics data
 */
function updatePipelineSection(data) {
    // Update pipeline status table
    if (data.pipeline_status) {
        const pipelineTable = document.getElementById('pipelineStatusTable');
        if (pipelineTable) {
            const tbody = pipelineTable.querySelector('tbody');
            if (tbody) {
                tbody.innerHTML = '';
                
                if (Object.keys(data.pipeline_status).length === 0) {
                    const tr = document.createElement('tr');
                    tr.className = 'placeholder-row';
                    const td = document.createElement('td');
                    td.colSpan = 4;
                    td.textContent = 'No pipeline data available';
                    tr.appendChild(td);
                    tbody.appendChild(tr);
                } else {
                    for (const [pipeline, info] of Object.entries(data.pipeline_status)) {
                        const tr = document.createElement('tr');
                        
                        const nameTd = document.createElement('td');
                        nameTd.textContent = pipeline;
                        
                        const statusTd = document.createElement('td');
                        statusTd.innerHTML = `<span class="status-indicator ${info.status}"></span> ${info.status}`;
                        
                        const lastRunTd = document.createElement('td');
                        lastRunTd.textContent = formatTimestamp(info.last_run);
                        
                        const processedTd = document.createElement('td');
                        processedTd.textContent = info.processed_count || 0;
                        
                        tr.appendChild(nameTd);
                        tr.appendChild(statusTd);
                        tr.appendChild(lastRunTd);
                        tr.appendChild(processedTd);
                        tbody.appendChild(tr);
                    }
                }
            }
        }
    }
    
    // Update processing rates chart
    if (data.processing_rates && dashboardState.charts && dashboardState.charts.processingRates) {
        const labels = Object.keys(data.processing_rates);
        const values = labels.map(label => data.processing_rates[label].items_per_second || 0);
        
        dashboardState.charts.processingRates.data.labels = labels;
        dashboardState.charts.processingRates.data.datasets[0].data = values;
        dashboardState.charts.processingRates.update();
    }
    
    // Update error rates chart
    if (data.error_rates && dashboardState.charts && dashboardState.charts.errorRates) {
        const labels = Object.keys(data.error_rates);
        const values = labels.map(label => data.error_rates[label].error_count || 0);
        
        dashboardState.charts.errorRates.data.labels = labels;
        dashboardState.charts.errorRates.data.datasets[0].data = values;
        dashboardState.charts.errorRates.update();
    }
}

/**
 * Start or restart the auto-refresh timer
 */
function startRefreshTimer() {
    // Clear any existing timer
    if (dashboardState.refreshTimer) {
        clearInterval(dashboardState.refreshTimer);
    }
    
    // Only set a timer if the interval is > 0
    if (dashboardState.refreshInterval > 0) {
        dashboardState.refreshTimer = setInterval(() => {
            loadDashboardData();
        }, dashboardState.refreshInterval * 1000);
    }
}

/**
 * Update the refresh interval
 * @param {number} interval - New interval in seconds
 */
function updateRefreshInterval(interval) {
    dashboardState.refreshInterval = interval;
    startRefreshTimer();
    
    // Save to localStorage if available
    try {
        localStorage.setItem('dashboardRefreshInterval', interval);
    } catch (e) {
        console.warn('Could not save refresh interval to localStorage:', e);
    }
}

/**
 * Update the last updated timestamp
 */
function updateLastUpdatedTime() {
    const element = document.getElementById('lastUpdatedTime');
    if (element) {
        element.textContent = formatTimestamp(new Date());
    }
}

/**
 * Show an error message to the user
 * @param {string} message - The error message to show
 */
function showError(message) {
    // Simple implementation - consider using a toast or notification system
    console.error(message);
    alert(message);
}

/**
 * Format a timestamp in a human-readable format
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
        const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
        return date.toLocaleString();
    } catch (e) {
        console.warn('Error formatting timestamp:', e);
        return 'Invalid date';
    }
}

/**
 * Format bytes to a human-readable format
 * @param {number} bytes - The number of bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted size string
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    if (!bytes) return 'Unknown';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}