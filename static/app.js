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
            logCounter: 0,  // Counter for unique log IDs
            running: false,
            loading: false,
            error: null,
            notifications: [],
            connectionStatus: 'disconnected',
            activeTab: 'demande',
            tabIds: {
                'demande.md': 'demande',
                'specifications.md': 'specifications',
                'management.md': 'management',
                'production.md': 'production',
                'evaluation.md': 'evaluation',
                'suivi.md': 'suivi'
            },
            tabs: [
                { id: 'demande', name: 'Demande', icon: 'mdi mdi-file-document-outline' },
                { id: 'specifications', name: 'Specifications', icon: 'mdi mdi-file-tree' },
                { id: 'management', name: 'Management', icon: 'mdi mdi-account-supervisor' },
                { id: 'production', name: 'Production', icon: 'mdi mdi-code-braces' },
                { id: 'evaluation', name: 'Evaluation', icon: 'mdi mdi-check-circle' },
                { id: 'suivi', name: 'Suivi', icon: 'mdi mdi-history' },
                { id: 'suivi-mission', name: 'Logs', icon: 'mdi mdi-console-line' },
                { id: 'export-logs', name: 'Export', icon: 'mdi mdi-download' }
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

        async saveDemande() {
            try {
                if (!this.content.demande) {
                    this.addNotification('error', 'No demand content to save');
                    return;
                }

                const response = await fetch('/api/demande', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        content: this.content.demande
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to save demand');
                }

                this.demandeChanged = false;
                this.addNotification('success', 'Demand saved successfully');
            } catch (error) {
                console.error('Error saving demand:', error);
                this.addNotification('error', `Failed to save demand: ${error.message}`);
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
            console.log("Adding notification:", type, message);
            const id = Date.now();
            const notification = {
                id,
                type,
                message,
                class: `notification-${type}`
            };
            
            this.notifications.push(notification);
            console.log("Current notifications:", this.notifications);
            
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


        debouncedSaveDemande: debounce(function() {
            this.saveDemande();  // Use this.saveDemande instead of saveDemande
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
                id: `${this.logCounter}_${Date.now()}`,  // Unique ID combining counter and timestamp
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
            this.logCounter++;  // Increment counter after use

            // Keep only last 100 logs using slice
            if (this.logs.length > 100) {
                this.logs = this.logs.slice(-100);
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

        async checkForChanges() {
            if (!this.running) {
                console.debug('App not running, skipping change check');
                return;
            }
            
            try {
                const response = await fetch('/api/changes');
                const changes = await response.json();
                
                changes.forEach(change => {
                    if (change.operation === 'flash_tab' && change.status) {
                        const tabId = this.tabIds[change.status];
                        if (tabId) {
                            const tab = document.querySelector(`.tab-item[data-tab="${tabId}"]`);
                            if (tab) {
                                tab.classList.remove('flash-tab');
                                void tab.offsetWidth; // Force reflow
                                tab.classList.add('flash-tab');
                                
                                setTimeout(() => {
                                    tab.classList.remove('flash-tab');
                                }, 1000);
                            }
                        }
                    }
                });
            } catch (error) {
                console.error('Error checking changes:', error);
            }
        },

        startUpdateLoop() {
            // Vérifier les notifications plus fréquemment
            this.notificationsInterval = setInterval(() => {
                this.checkNotifications();
            }, 500);  // Toutes les 500ms
            
            // Autres mises à jour moins fréquentes
            this.updateInterval = setInterval(() => {
                this.updateContent();
                this.updateLogs();
                this.checkForChanges();
            }, 1000);
        },

        async checkNotifications() {
            try {
                const response = await fetch('/api/notifications');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const notifications = await response.json();
                
                if (Array.isArray(notifications) && notifications.length > 0) {
                    console.log('Received notifications:', notifications);
                    
                    notifications.forEach(notification => {
                        console.log('Processing notification:', notification);
                        
                        // Ajouter la notification visuelle
                        this.addNotification(notification.type, notification.message);
                        
                        // Gérer le flash du tab
                        if (notification.panel) {
                            const panelName = notification.panel.toLowerCase();
                            const tabFile = `${panelName}.md`;
                            console.log('Looking for tab:', tabFile, 'in', this.tabIds);
                            
                            const tabId = this.tabIds[tabFile];
                            if (tabId) {
                                console.log('Found tab ID:', tabId);
                                const tab = document.querySelector(`.tab-item[data-tab="${tabId}"]`);
                                
                                if (tab) {
                                    console.log('Flashing tab:', tabId);
                                    tab.classList.remove('flash-tab');
                                    void tab.offsetWidth;
                                    tab.classList.add('flash-tab');
                                    
                                    setTimeout(() => {
                                        tab.classList.remove('flash-tab');
                                    }, 1000);
                                } else {
                                    console.log('Tab element not found for ID:', tabId);
                                }
                            } else {
                                console.log('No tab ID found for:', tabFile);
                            }
                        }
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
            if (this.notificationsInterval) {
                clearInterval(this.notificationsInterval);
                this.notificationsInterval = null;
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
"""
SuiviAgent - Agent responsible for monitoring and logging system activity.

Key responsibilities:
- Tracks agent activities and interactions
- Maintains system-wide logging
- Provides activity summaries and reports
- Monitors system health and performance
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
import time
from datetime import datetime
import openai

class SuiviAgent(ParallagonAgent):
    """Agent handling system monitoring and logging"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)
        self.logs_buffer = config.get("logs_buffer", [])

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "suivi": self.current_content,
                "other_files": self.other_files,
                "logs": self.logs_buffer
            }
            
            response = self._get_llm_response(context)
            if response and response != self.current_content:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(response)
                self.current_content = response
                self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response with standardized error handling"""
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            self.logger(f"[{self.__class__.__name__}] LLM response received")
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return context.get('suivi', '')

    def _format_logs(self, logs: list) -> str:
        """Format logs for inclusion in the prompt"""
        formatted = []
        for log in logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'info')
            message = log.get('message', '')
            formatted.append(f"[{timestamp}] [{level.upper()}] {message}")
        return "\n".join(formatted)

    def _build_prompt(self, context: dict) -> str:
        return f"""Vous êtes l'agent de suivi. Votre rôle est de suivre et documenter l'activité du système.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Logs récents :
{self._format_logs(context['logs'])}

Votre tâche :
1. Analyser les logs et l'activité système
2. Identifier les patterns et tendances
3. Générer un rapport de suivi

Format de réponse :
# État du Système
[status: RUNNING|STOPPED]
[agents_actifs: X/Y]
[santé: GOOD|WARNING|ERROR]

# Activité Récente
- [HH:MM:SS] Description activité 1
- [HH:MM:SS] Description activité 2

# Points d'Attention
- Point important 1
- Point important 2

# Métriques
- Agents actifs: X/Y
- Taux de changement: X/minute
- Temps de réponse moyen: Xs

IMPORTANT:
- Être concis et factuel
- Mettre en évidence les anomalies
- Inclure les timestamps
- Maintenir l'historique"""

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a specific section"""
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            return ""
        elif len(matches) > 1:
            self.logger(f"Warning: Multiple '{section_name}' sections found")
            
        return matches[0].group(1).strip()

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for context"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
