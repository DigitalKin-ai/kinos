// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const ParallagonApp = {
    delimiters: ['${', '}'],  // Use different delimiters to avoid Jinja2 conflicts
    data() {
        return {
            running: false,
            loading: false,
            error: null,
            notifications: [],
            connectionStatus: 'disconnected',
            activeTab: 'demande',
            tabs: [
                { id: 'demande', name: 'Demande', icon: 'mdi mdi-file-document-outline' },
                { id: 'specifications', name: 'Specifications', icon: 'mdi mdi-file-tree' },
                { id: 'management', name: 'Management', icon: 'mdi mdi-account-supervisor' },
                { id: 'production', name: 'Production', icon: 'mdi mdi-code-braces' },
                { id: 'evaluation', name: 'Evaluation', icon: 'mdi mdi-check-circle' },
                { id: 'suivi-mission', name: 'Suivi Mission', icon: 'mdi mdi-console-line' }
            ],
            content: {
                demande: '',
                specifications: '',
                management: '',
                production: '',
                evaluation: ''
            },
            previousContent: {},
            panels: [
                { id: 'specifications', name: 'Specifications', icon: 'mdi mdi-file-tree', updating: false },
                { id: 'management', name: 'Management', icon: 'mdi mdi-account-supervisor', updating: false },
                { id: 'production', name: 'Production', icon: 'mdi mdi-code-braces', updating: false },
                { id: 'evaluation', name: 'Evaluation', icon: 'mdi mdi-check-circle', updating: false }
            ],
            logs: [],
            demandeChanged: false,
            updateInterval: null,
            previousContent: {},
            ws: null
        }
    },
    methods: {
        async loadInitialContent() {
            try {
                this.loading = true;
                const response = await fetch('/api/content');
                if (!response.ok) {
                    throw new Error('Failed to load initial content');
                }
                const data = await response.json();
                this.content = data;
                this.previousContent = { ...data };
                this.addNotification('success', 'Content loaded successfully');
            } catch (error) {
                console.error('Error loading initial content:', error);
                this.addNotification('error', `Failed to load content: ${error.message}`);
            } finally {
                this.loading = false;
            }
        },
        notificationIcon(type) {
            switch (type) {
                case 'success':
                    return 'mdi mdi-check-circle';
                case 'error':
                    return 'mdi mdi-alert-circle';
                case 'warning':
                    return 'mdi mdi-alert';
                default:
                    return 'mdi mdi-information';
            }
        },

        async startAgents() {
            try {
                this.loading = true;
                await fetch('/api/start', { method: 'POST' });
                this.running = true;
                this.startUpdateLoop();
                // Activer l'onglet Suivi Mission
                this.activeTab = 'suivi-mission';
                this.addNotification('success', 'Agents started successfully');
                // Start logs update
                this.startLogsUpdate();
            } catch (error) {
                this.error = error.message;
                this.addNotification('error', `Failed to start agents: ${error.message}`);
            } finally {
                this.loading = false;
            }
        },

        startLogsUpdate() {
            if (!this.logsInterval) {
                this.logsInterval = setInterval(async () => {
                    try {
                        const response = await fetch('/api/logs');
                        const data = await response.json();
                        if (data.logs && Array.isArray(data.logs)) {
                            this.logs = data.logs;
                            // Auto-scroll to bottom
                            this.$nextTick(() => {
                                const logsContent = document.querySelector('.suivi-mission-content');
                                if (logsContent) {
                                    logsContent.scrollTop = logsContent.scrollHeight;
                                }
                            });
                        }
                    } catch (error) {
                        console.error('Failed to fetch logs:', error);
                    }
                }, 1000);
            }
        },

        addNotification(type, message) {
            const id = Date.now();
            // Ajout de classes CSS pour le style
            const notification = {
                id,
                type,
                message,
                class: `notification-${type}` // Ajout d'une classe pour le style
            };
            
            this.notifications.push(notification);
            
            // Log pour debug
            console.log('Adding notification:', notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 5000);
        },

        async stopAgents() {
            try {
                await fetch('/api/stop', { method: 'POST' });
                this.running = false;
                this.stopUpdateLoop();
                // Stop logs update
                if (this.logsInterval) {
                    clearInterval(this.logsInterval);
                    this.logsInterval = null;
                }
            } catch (error) {
                console.error('Failed to stop agents:', error);
                this.addLog('error', 'Failed to stop agents: ' + error.message);
            }
        },

        async resetFiles() {
            try {
                if (confirm('Are you sure you want to reset all files to their initial state?')) {
                    const response = await fetch('/api/reset', {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        this.addNotification('success', 'Files reset successfully');
                        await this.updateContent();
                    } else {
                        throw new Error('Failed to reset files');
                    }
                }
            } catch (error) {
                console.error('Failed to reset files:', error);
                this.addNotification('error', `Failed to reset files: ${error.message}`);
            }
        },

        startPolling() {
            setInterval(async () => {
                if (this.running) {
                    try {
                        const response = await fetch('/api/content');
                        const data = await response.json();
                        
                        this.previousContent = { ...this.content };
                        this.content = data;

                        // Check for changes and update UI
                        this.panels.forEach(panel => {
                            const hasChanged = this.previousContent[panel.id] !== this.content[panel.id];
                            panel.updating = hasChanged;
                            if (hasChanged) {
                                this.addLog('info', `${panel.name} content updated`);
                            }
                        });
                    } catch (error) {
                        console.error('Failed to poll content:', error);
                        this.addLog('error', 'Failed to update content: ' + error.message);
                    }
                }
            }, 1000); // Poll every second
        },

        async updateContent() {
            try {
                // Get content updates
                const contentResponse = await fetch('/api/content');
                const contentData = await contentResponse.json();
                
                // Get notifications
                const notificationsResponse = await fetch('/api/notifications');
                const notificationsData = await notificationsResponse.json();
                
                // Process notifications
                if (Array.isArray(notificationsData)) {
                    notificationsData.forEach(notification => {
                        this.addNotification(notification.type, notification.message);
                    });
                }
                
                this.previousContent = { ...this.content };
                this.content = contentData;

                // Check for changes and update UI
                this.panels.forEach(panel => {
                    const hasChanged = this.previousContent[panel.id] !== this.content[panel.id];
                    panel.updating = hasChanged;
                    if (hasChanged) {
                        this.addLog('info', `${panel.name} content updated`);
                    }
                });
            } catch (error) {
                console.error('Failed to update content:', error);
                this.addLog('error', 'Failed to update content: ' + error.message);
            }
        },


        debouncedSaveDemande: debounce(async function() {
            await this.saveDemande();
        }, 1000),

        onDemandeInput() {
            this.demandeChanged = true;
            this.debouncedSaveDemande();
        },

        computeDiff(oldLines, newLines) {
            const diff = [];
            let i = 0, j = 0;
            
            while (i < oldLines.length || j < newLines.length) {
                if (i >= oldLines.length) {
                    diff.push({ added: true, value: newLines[j] });
                    j++;
                } else if (j >= newLines.length) {
                    diff.push({ removed: true, value: oldLines[i] });
                    i++;
                } else if (oldLines[i] !== newLines[j]) {
                    diff.push({ removed: true, value: oldLines[i] });
                    diff.push({ added: true, value: newLines[j] });
                    i++;
                    j++;
                } else {
                    diff.push({ value: oldLines[i] });
                    i++;
                    j++;
                }
            }
            
            return diff;
        },

        setActiveTab(tabId) {
            this.activeTab = tabId;
        },
        
        highlightContent(panelId) {
            const oldContent = this.previousContent[panelId] || '';
            const newContent = this.content[panelId] || '';
            
            if (oldContent === newContent) return newContent;

            const diff = this.computeDiff(
                oldContent.split('\n'),
                newContent.split('\n')
            );

            return diff.map(part => {
                if (part.added) {
                    return `<span class="highlight-add">${this.escapeHtml(part.value)}</span>`;
                }
                if (part.removed) {
                    return `<span class="highlight-remove">${this.escapeHtml(part.value)}</span>`;
                }
                return this.escapeHtml(part.value);
            }).join('\n');
        },

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        async exportLogs() {
            try {
                const response = await fetch('/api/logs/export');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                
                a.href = url;
                a.download = `parallagon-logs-${timestamp}.txt`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.addLog('success', 'Logs exported successfully');
            } catch (error) {
                console.error('Failed to export logs:', error);
                this.addLog('error', 'Failed to export logs: ' + error.message);
            }
        },

        async clearLogs() {
            try {
                await fetch('/api/logs/clear', { method: 'POST' });
                this.logs = [];
                this.addLog('info', 'Logs cleared');
            } catch (error) {
                console.error('Failed to clear logs:', error);
                this.addLog('error', 'Failed to clear logs: ' + error.message);
            }
        },

        async loadTestData() {
            try {
                const response = await fetch('/api/test-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    this.addNotification('success', 'Données de test chargées');
                    await this.updateContent(); // Refresh the content
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to load test data');
                }
            } catch (error) {
                console.error('Failed to load test data:', error);
                this.addNotification('error', `Failed to load test data: ${error.message}`);
            }
        },

        async loadTestData() {
            try {
                const response = await fetch('/api/test-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    this.addNotification('success', 'Données de test chargées');
                    await this.updateContent(); // Rafraîchit le contenu
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to load test data');
                }
            } catch (error) {
                console.error('Failed to load test data:', error);
                this.addNotification('error', `Failed to load test data: ${error.message}`);
            }
        },

        addLog(level, message, operation = null, status = null) {
            const timestamp = new Date().toISOString();
            const logEntry = {
                id: Date.now(),
                timestamp,
                level,
                message,
                operation,
                status
            };
            
            // Format message with operation and status if present
            if (operation && status) {
                logEntry.formattedMessage = `${operation}: ${status} - ${message}`;
            } else {
                logEntry.formattedMessage = message;
            }
            
            this.logs.push(logEntry);

            // Keep only last 100 logs
            if (this.logs.length > 100) {
                this.logs.shift();
            }

            // Auto-scroll logs
            this.$nextTick(() => {
                const logsContent = document.querySelector('.logs-content');
                if (logsContent) {
                    logsContent.scrollTop = logsContent.scrollHeight;
                }
            });
        },

        async updateLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                if (data.logs && Array.isArray(data.logs)) {
                    this.logs = data.logs;
                }
            } catch (error) {
                console.error('Failed to fetch logs:', error);
            }
        },

        startUpdateLoop() {
            this.updateInterval = setInterval(() => {
                this.updateContent();
                this.updateLogs();  // Add logs update
                this.checkNotifications();  // Add notifications check
            }, 1000);
        },

        async checkNotifications() {
            try {
                const response = await fetch('/api/notifications');
                const notifications = await response.json();
                
                if (Array.isArray(notifications)) {
                    notifications.forEach(notification => {
                        console.log('Received notification:', notification); // Debug log
                        this.addNotification(notification.type, notification.message);
                    });
                }
            } catch (error) {
                console.error('Failed to check notifications:', error);
            }
        },

        stopUpdateLoop() {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        }
    },

    
    mounted() {
        // Add notifications container to body
        const notificationsContainer = document.createElement('div');
        notificationsContainer.className = 'notifications-container';
        document.body.appendChild(notificationsContainer);
        
        this.loadInitialContent()
            .then(() => {
                this.startPolling();
                this.addLog('info', 'Application initialized');
            })
            .catch(error => {
                console.error('Error in mounted:', error);
                this.addNotification('error', 'Failed to initialize application');
            });
    },
    
    beforeUnmount() {
        this.stopUpdateLoop();
    }
};

Vue.createApp(ParallagonApp).mount('#app');
