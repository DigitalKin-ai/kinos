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
    data() {
        return {
            running: false,
            content: {
                demande: '',
                specifications: '',
                management: '',
                production: '',
                evaluation: ''
            },
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
        async startAgents() {
            try {
                await fetch('/api/start', { method: 'POST' });
                this.running = true;
                this.startUpdateLoop();
            } catch (error) {
                console.error('Failed to start agents:', error);
                this.addLog('error', 'Failed to start agents: ' + error.message);
            }
        },

        async stopAgents() {
            try {
                await fetch('/api/stop', { method: 'POST' });
                this.running = false;
                this.stopUpdateLoop();
            } catch (error) {
                console.error('Failed to stop agents:', error);
                this.addLog('error', 'Failed to stop agents: ' + error.message);
            }
        },

        initWebSocket() {
            this.ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'content_update') {
                    // Store previous content for diff highlighting
                    this.previousContent = { ...this.content };
                    this.content = data.content;
                    
                    // Update panel status
                    this.panels.forEach(panel => {
                        const hasChanged = this.previousContent[panel.id] !== this.content[panel.id];
                        panel.updating = hasChanged;
                        if (hasChanged) {
                            this.addLog('info', `${panel.name} content updated`);
                        }
                    });
                } else if (data.type === 'log') {
                    this.addLog(data.level, data.message);
                }
            };
            
            this.ws.onclose = () => {
                this.addLog('warning', 'WebSocket connection closed. Attempting to reconnect...');
                setTimeout(() => this.initWebSocket(), 5000);
            };
        },

        async updateContent() {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                try {
                    const response = await fetch('/api/content');
                    const data = await response.json();
                    
                    this.previousContent = { ...this.content };
                    this.content = data;

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
            }
        },

        async saveDemande() {
            try {
                const response = await fetch('/api/demande', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: this.content.demande })
                });
                
                if (response.ok) {
                    this.demandeChanged = false;
                    this.addLog('success', 'Demande saved successfully');
                } else {
                    throw new Error('Failed to save demande');
                }
            } catch (error) {
                console.error('Failed to save demande:', error);
                this.addLog('error', 'Failed to save demande: ' + error.message);
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

        highlightContent(panelId) {
            const oldContent = this.previousContent[panelId] || '';
            const newContent = this.content[panelId] || '';
            
            if (oldContent === newContent) return newContent;

            const oldLines = oldContent.split('\n');
            const newLines = newContent.split('\n');
            let html = '';

            // Use diff algorithm to identify changes
            const diff = this.computeDiff(oldLines, newLines);
            
            diff.forEach(part => {
                if (part.added) {
                    html += `<span class="highlight-add">${part.value}</span>\n`;
                } else if (part.removed) {
                    html += `<span class="highlight-remove">${part.value}</span>\n`;
                } else {
                    html += `${part.value}\n`;
                }
            });

            return html;
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

        addLog(level, message) {
            const timestamp = new Date().toISOString();
            this.logs.push({
                id: Date.now(),
                timestamp,
                level,
                message
            });

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

        startUpdateLoop() {
            this.updateInterval = setInterval(() => {
                this.updateContent();
            }, 1000);
        },

        stopUpdateLoop() {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        }
    },
    mounted() {
        this.initWebSocket();
        this.addLog('info', 'Application initialized');
    },
    beforeUnmount() {
        if (this.ws) {
            this.ws.close();
        }
        this.stopUpdateLoop();
    }
};

Vue.createApp(ParallagonApp).mount('#app');
