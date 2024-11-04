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
            previousContent: {}
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

        async updateContent() {
            try {
                const response = await fetch('/api/content');
                const data = await response.json();
                
                // Store previous content for diff highlighting
                this.previousContent = { ...this.content };
                this.content = data;

                // Update panel status
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

        onDemandeInput() {
            this.demandeChanged = true;
        },

        highlightContent(panelId) {
            const oldContent = this.previousContent[panelId] || '';
            const newContent = this.content[panelId] || '';
            
            if (oldContent === newContent) return newContent;

            // Simple diff highlighting
            const oldLines = oldContent.split('\n');
            const newLines = newContent.split('\n');
            let html = '';

            newLines.forEach((line, i) => {
                if (line !== oldLines[i]) {
                    html += `<span class="highlight-change">${line}</span>\n`;
                } else {
                    html += line + '\n';
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
                a.href = url;
                a.download = `parallagon-logs-${new Date().toISOString()}.txt`;
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
        this.updateContent();
        this.addLog('info', 'Application initialized');
    },
    beforeUnmount() {
        this.stopUpdateLoop();
    }
};

Vue.createApp(ParallagonApp).mount('#app');
