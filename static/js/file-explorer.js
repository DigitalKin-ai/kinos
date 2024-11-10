export default {
    name: 'FileExplorer',
    props: {
        currentMission: Object
    },
    data() {
        return {
            files: [],
            loading: true,
            error: null,
            fileCheckInterval: null,
            flashingFiles: new Set(),
            expandedFiles: new Set(),
            fileContents: new Map(),
            activeTab: 'files',
            pollInterval: 5000,
            editingFile: null,
            editedContent: '',
            showEditModal: false,
            saving: false,
            hasUnsavedChanges: false,
            autoSaveInterval: null,
            lastSavedContent: '',
            errorMessage: null,
            showError: false
        }
    },
    computed: {
        fileCount() {
            return this.files ? this.files.length : 0;
        }
    },
    beforeUnmount() {
        if (this.fileCheckInterval) {
            clearInterval(this.fileCheckInterval);
            this.fileCheckInterval = null;
        }
    },
    methods: {
        handleKeyPress(e) {
            // Ctrl/Cmd + S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                if (!this.saving) {
                    this.saveFileChanges();
                }
            }
            // Esc to close
            if (e.key === 'Escape') {
                this.closeEditModal();
            }
        },

        startAutoSave() {
            this.lastSavedContent = this.editedContent;
            this.autoSaveInterval = setInterval(() => {
                if (this.hasUnsavedChanges && !this.saving) {
                    this.saveFileChanges();
                }
            }, 30000); // Auto-save every 30 seconds
        },

        stopAutoSave() {
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
                this.autoSaveInterval = null;
            }
        },

        getLanguage(fileName) {
            const ext = fileName.split('.').pop().toLowerCase();
            const languageMap = {
                'js': 'javascript',
                'py': 'python',
                'md': 'markdown',
                'json': 'json',
                'html': 'html',
                'css': 'css'
            };
            return languageMap[ext] || 'plaintext';
        },

        highlightCode() {
            if (this.editingFile) {
                const language = this.getLanguage(this.editingFile.name);
                if (language !== 'plaintext') {
                    this.$nextTick(() => {
                        const codeElements = this.$el.querySelectorAll('pre code');
                        codeElements.forEach(block => {
                            hljs.highlightElement(block);
                        });
                    });
                }
            }
        }
    },

    watch: {
        currentMission: {
            immediate: true,
            handler(newMission) {
                if (this.fileCheckInterval) {
                    clearInterval(this.fileCheckInterval);
                    this.fileCheckInterval = null;
                }

                if (newMission?.id && this.activeTab === 'files') {
                    this.loadMissionFiles();
                    this.startFileChecking();
                } else {
                    this.files = [];
                }
            }
        },
        editedContent(newContent) {
            if (this.editingFile) {
                const originalContent = this.fileContents.get(this.editingFile.path);
                this.hasUnsavedChanges = newContent !== originalContent;
            }
        },
        activeTab: {
            handler(newTab) {
                if (newTab === 'files' && this.currentMission?.id) {
                    this.loadMissionFiles();
                    this.startFileChecking();
                } else {
                    if (this.fileCheckInterval) {
                        clearInterval(this.fileCheckInterval);
                        this.fileCheckInterval = null;
                    }
                }
            }
        }
    },
    methods: {
        startFileChecking() {
            if (this.fileCheckInterval) {
                clearInterval(this.fileCheckInterval);
            }
            
            // Reset poll interval to default if it was increased
            if (this.pollInterval > 5000) {
                this.pollInterval = 5000;
            }
            
            this.fileCheckInterval = setInterval(() => {
                if (this.currentMission?.id && this.activeTab === 'files') {
                    this.checkFileModifications();
                }
            }, this.pollInterval);
        },

        setActiveTab(tabId) {
            this.activeTab = tabId;
            if (this.activeTab === 'files') {
                this.loadMissionFiles();
                this.startFileChecking();
            } else {
                if (this.fileCheckInterval) {
                    clearInterval(this.fileCheckInterval);
                    this.fileCheckInterval = null;
                }
            }
        },

        async checkFileModifications() {
            try {
                // Skip if no valid mission
                if (!this.currentMission?.id) {
                    return;
                }

                // Add exponential backoff retry logic
                const maxRetries = 3;
                let retryCount = 0;
                let success = false;

                while (!success && retryCount < maxRetries) {
                    try {
                        const response = await fetch(`/api/missions/${this.currentMission.id}/files`, {
                            // Add timeout
                            signal: AbortSignal.timeout(5000)
                        });
                        
                        if (response.ok) {
                            const newFiles = await response.json();
                            // Update files and handle modifications
                            newFiles.forEach(newFile => {
                                const existingFile = this.files.find(f => f.path === newFile.path);
                                if (existingFile && existingFile.modified !== newFile.modified) {
                                    this.flashFile(newFile.path);
                                    Object.assign(existingFile, newFile);
                                }
                            });
                            success = true;
                        } else if (response.status === 404) {
                            console.warn(`Mission ${this.currentMission.id} not found`);
                            // Clear files if mission no longer exists
                            this.files = [];
                            // Stop polling since mission doesn't exist
                            if (this.fileCheckInterval) {
                                clearInterval(this.fileCheckInterval);
                                this.fileCheckInterval = null;
                            }
                            return;
                        } else {
                            throw new Error(`Server returned ${response.status}`);
                        }
                    } catch (error) {
                        retryCount++;
                        if (retryCount < maxRetries) {
                            // Exponential backoff
                            const delay = Math.pow(2, retryCount) * 1000;
                            console.warn(`Retry attempt ${retryCount} of ${maxRetries} in ${delay}ms`);
                            await new Promise(resolve => setTimeout(resolve, delay));
                        } else {
                            // After max retries, reduce polling frequency
                            this.adjustPollingInterval();
                            throw error;
                        }
                    }
                }
            } catch (error) {
                console.error('Error checking file modifications:', error);
                // Reduce polling frequency on error
                this.adjustPollingInterval();
            }
        },

        // Add method to adjust polling interval
        adjustPollingInterval() {
            if (this.fileCheckInterval) {
                clearInterval(this.fileCheckInterval);
                // Increase interval on error (double it up to max 30 seconds)
                this.pollInterval = Math.min(this.pollInterval * 2, 30000);
                this.startFileChecking();
            }
        },

        flashFile(filePath) {
            // Add file to flashing set
            this.flashingFiles.add(filePath);
            // Remove after 2 seconds
            setTimeout(() => {
                this.flashingFiles.delete(filePath);
            }, 2000);
        },

        isFlashing(filePath) {
            return this.flashingFiles.has(filePath);
        },

        async loadMissionFiles() {
            try {
                this.loading = true;
                this.error = null; // Reset error state
                if (!this.currentMission) {
                    this.error = 'No mission selected';
                    return;
                }
                
                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (response.status === 404) {
                    this.error = `Mission ${this.currentMission.id} not found`;
                    this.files = [];
                    return;
                }
                if (!response.ok) {
                    throw new Error(`Failed to load files (${response.status})`);
                }
                
                this.files = await response.json();
            } catch (error) {
                this.error = error.message;
                console.error('Error loading files:', error);
                this.files = [];
            } finally {
                this.loading = false;
            }
        },

        getFileSize(file) {
            return this.formatSize(file.size);
        },

        formatSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        formatDate(timestamp) {
            return new Date(timestamp * 1000).toLocaleString();
        },

        async editFile(file) {
            try {
                // Load the file content if not already loaded
                if (!this.fileContents.has(file.path)) {
                    const response = await fetch(
                        `/api/missions/${this.currentMission.id}/files/${encodeURIComponent(file.relativePath || file.path)}`
                    );
                
                    if (!response.ok) {
                        throw new Error('Failed to load file content');
                    }
                
                    const content = await response.text();
                    this.fileContents.set(file.path, content);
                }

                this.editingFile = file;
                this.editedContent = this.fileContents.get(file.path);
                this.showEditModal = true;
                this.lastSavedContent = this.editedContent;
            
                // Add keyboard shortcuts
                window.addEventListener('keydown', this.handleKeyPress);
            
                // Start auto-save
                this.startAutoSave();
            
                // Apply syntax highlighting
                this.highlightCode();
            } catch (error) {
                console.error('Error loading file for edit:', error);
                this.errorMessage = error.message;
                this.showError = true;
            }
        },

        async saveFileChanges() {
            if (!this.editingFile || !this.currentMission) return;
        
            try {
                this.saving = true;
                const response = await fetch(
                    `/api/missions/${this.currentMission.id}/files/${encodeURIComponent(this.editingFile.relativePath || this.editingFile.path)}`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            content: this.editedContent
                        })
                    }
                );

                if (!response.ok) {
                    throw new Error('Failed to save file changes');
                }

                // Update local content cache
                this.fileContents.set(this.editingFile.path, this.editedContent);
                this.lastSavedContent = this.editedContent;
                this.hasUnsavedChanges = false;
            
                // Flash the file to indicate successful save
                this.flashFile(this.editingFile.path);
            
                this.errorMessage = null;
                this.showError = false;

            } catch (error) {
                console.error('Error saving file changes:', error);
                this.errorMessage = error.message;
                this.showError = true;
                setTimeout(() => {
                    this.showError = false;
                }, 5000);
            } finally {
                this.saving = false;
            }
        },

        closeEditModal() {
            if (this.hasUnsavedChanges) {
                if (!confirm('You have unsaved changes. Are you sure you want to close?')) {
                    return;
                }
            }
            window.removeEventListener('keydown', this.handleKeyPress);
            this.stopAutoSave();
            this.showEditModal = false;
            this.editingFile = null;
            this.editedContent = '';
            this.hasUnsavedChanges = false;
        },

        async toggleFile(file) {
            try {
                if (this.expandedFiles.has(file.path)) {
                    this.expandedFiles.delete(file.path);
                    return;
                }

                this.expandedFiles.add(file.path);
                
                if (!this.fileContents.has(file.path)) {
                    // Use relative path for request
                    const response = await fetch(
                        `/api/missions/${this.currentMission.id}/files/${encodeURIComponent(file.relativePath || file.path)}`
                    );
                    
                    if (!response.ok) {
                        throw new Error('Failed to load file content');
                    }
                    
                    const content = await response.text();
                    this.fileContents.set(file.path, content);
                }
            } catch (error) {
                console.error('Error loading file content:', error);
                this.expandedFiles.delete(file.path);
                this.error = `Failed to load content for ${file.name}`;
            }
        },

        isExpanded(filePath) {
            return this.expandedFiles.has(filePath);
        },

        getFileContent(filePath) {
            return this.fileContents.get(filePath) || '';
        },

        formatContent(content) {
            return marked.parse(content);
        }
    },
    template: `
        <div class="h-full flex flex-col">
            <div class="bg-white shadow px-6 py-4 mb-4">
                <div class="flex justify-between items-center">
                    <h2 class="text-2xl font-bold">Files</h2>
                    <div class="flex items-center gap-4">
                        <span class="text-sm text-gray-500">
                            {{ fileCount }} files
                        </span>
                    </div>
                </div>
            </div>

            <div v-if="loading" class="flex-1 flex items-center justify-center">
                <p class="text-gray-600">Loading files...</p>
            </div>

            <div v-else-if="error" class="flex-1 flex items-center justify-center">
                <p class="text-red-500">{{ error }}</p>
            </div>

            <div class="flex-1 overflow-hidden">
                <div class="h-full overflow-y-auto px-6">
                    <div v-if="loading" class="flex items-center justify-center py-4">
                        <p class="text-gray-600">Loading files...</p>
                    </div>

                    <div v-else-if="error" class="flex items-center justify-center py-4">
                        <p class="text-red-500">{{ error }}</p>
                    </div>

                    <div v-else class="bg-white shadow rounded-lg">
                        <div v-for="file in files" 
                             :key="file.path" 
                             class="border-b border-gray-200 last:border-b-0">
                        
                        <!-- En-tête du fichier -->
                        <div @click="toggleFile(file)"
                             class="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors duration-200"
                             :class="{ 'bg-yellow-100': isFlashing(file.path) }">
                            <div class="flex items-center">
                                <i class="mdi mdi-chevron-right text-gray-500 mr-2 transition-transform duration-200"
                                   :class="{ 'transform rotate-90': isExpanded(file.path) }"></i>
                                <i class="mdi mdi-file-document-outline text-gray-500 mr-2"></i>
                                <span class="text-sm text-gray-900">{{ file.name }}</span>
                            </div>
                            <div class="flex items-center space-x-4">
                                <button @click.stop="editFile(file)" 
                                        class="px-2 py-1 text-sm text-blue-600 hover:text-blue-800">
                                    <i class="mdi mdi-pencil"></i> Edit
                                </button>
                                <span class="text-sm text-gray-500">{{ getFileSize(file) }}</span>
                                <span class="text-sm text-gray-500">{{ formatDate(file.modified) }}</span>
                            </div>
                        </div>
                        
                        <!-- Contenu du fichier (accordéon) -->
                        <div v-if="isExpanded(file.path)" 
                             class="border-t border-gray-100 bg-gray-50">
                            <div class="p-6 overflow-x-auto">
                                <div v-if="fileContents.has(file.path)"
                                     class="prose max-w-none"
                                     v-html="formatContent(getFileContent(file.path))">
                                </div>
                                <div v-else class="text-gray-500 text-sm">
                                    Loading content...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </div>

    <!-- Edit modal -->
    <div v-if="showEditModal" 
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 w-3/4 max-h-[90vh] flex flex-col">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold">
                    Editing: {{ editingFile?.name }}
                </h3>
                <button @click="closeEditModal" 
                        class="text-gray-500 hover:text-gray-700">
                    <i class="mdi mdi-close"></i>
                </button>
            </div>
            
            <textarea v-model="editedContent"
                      class="flex-1 w-full p-4 border rounded-md font-mono text-sm mb-4"
                      style="min-height: 400px"
                      :disabled="saving">
            </textarea>
            
            <div class="relative">
                <div class="absolute bottom-0 left-0 p-4 text-sm">
                    <span v-if="hasUnsavedChanges" class="text-yellow-600">
                        <i class="mdi mdi-circle-medium animate-pulse"></i>
                        Unsaved changes
                    </span>
                    <span v-else class="text-green-600">
                        <i class="mdi mdi-check-circle"></i>
                        All changes saved
                    </span>
                    <span v-if="saving" class="ml-4 text-blue-600">
                        <i class="mdi mdi-loading mdi-spin"></i>
                        Saving...
                    </span>
                </div>
                <div class="flex justify-end space-x-2">
                    <button @click="closeEditModal"
                            :disabled="saving"
                            class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-50">
                        Cancel
                    </button>
                    <button @click="saveFileChanges"
                            :disabled="saving"
                            class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50">
                        {{ saving ? 'Saving...' : 'Save Changes' }}
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Error notification -->
        <div v-if="showError" 
             class="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {{ errorMessage }}
        </div>

        <!-- Edit Agent Modal -->
        <div v-if="showEditModal && currentEditAgent" 
             class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 w-3/4 max-h-[90vh] flex flex-col">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">
                        Editing Agent: [[ currentEditAgent.name ]]
                    </h3>
                    <button @click="closeEditModal" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="mdi mdi-close"></i>
                    </button>
                </div>

                <div class="flex-1 mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Agent Prompt
                    </label>
                    <textarea v-model="currentEditAgent.prompt"
                              class="w-full h-[400px] p-4 border rounded-md font-mono text-sm"
                              :disabled="editLoading">
                    </textarea>
                </div>

                <div class="flex justify-end space-x-2">
                    <button @click="closeEditModal"
                            :disabled="editLoading"
                            class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-50">
                        Cancel
                    </button>
                    <button @click="saveEditedPrompt"
                            :disabled="editLoading || !currentEditAgent.prompt"
                            class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50">
                        <span v-if="editLoading">
                            <i class="mdi mdi-loading mdi-spin mr-1"></i>
                            Saving...
                        </span>
                        <span v-else>Save Changes</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
    `
};
