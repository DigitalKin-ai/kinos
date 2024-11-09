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
            pollInterval: 5000
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
    `
};
