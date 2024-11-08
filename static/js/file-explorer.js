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
            fileContents: new Map()
        }
    },
    computed: {
        fileCount() {
            return this.files ? this.files.length : 0;
        }
    },
    created() {
        // Start periodic file checking
        this.startFileWatcher();
    },
    beforeUnmount() {
        // Cleanup interval when component is destroyed
        if (this.fileCheckInterval) {
            clearInterval(this.fileCheckInterval);
        }
    },
    watch: {
        currentMission: {
            immediate: true,
            handler(newMission) {
                if (newMission?.id) { // Vérifier l'existence d'un ID valide
                    this.loadMissionFiles();
                    // Redémarrer le watcher avec la nouvelle mission
                    this.startFileWatcher();
                } else {
                    // Réinitialiser les fichiers si pas de mission
                    this.files = [];
                }
            }
        }
    },
    methods: {
        startFileWatcher() {
            // Arrêter l'intervalle existant si présent
            if (this.fileCheckInterval) {
                clearInterval(this.fileCheckInterval);
            }
            
            this.fileCheckInterval = setInterval(() => {
                if (this.currentMission?.id) { // Vérifier l'existence d'un ID valide
                    this.checkFileModifications();
                }
            }, 2000); // Check every 2 seconds
        },

        async checkFileModifications() {
            try {
                // Skip if no valid mission
                if (!this.currentMission?.id) {
                    return;
                }

                // Add error handling and retry logic
                const maxRetries = 3;
                let retryCount = 0;
                let success = false;

                while (!success && retryCount < maxRetries) {
                    try {
                        const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                        
                        if (response.ok) {
                            const newFiles = await response.json();
                            // Compare modification timestamps
                            newFiles.forEach(newFile => {
                                const existingFile = this.files.find(f => f.path === newFile.path);
                                if (existingFile && existingFile.modified !== newFile.modified) {
                                    this.flashFile(newFile.path);
                                    Object.assign(existingFile, newFile);
                                }
                            });
                            success = true;
                        } else if (response.status === 404) {
                            console.warn('Mission files not found, skipping check');
                            return;
                        }
                    } catch (error) {
                        retryCount++;
                        if (retryCount < maxRetries) {
                            // Wait before retrying (exponential backoff)
                            await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
                            console.warn(`Retry attempt ${retryCount} of ${maxRetries}`);
                        } else {
                            throw error;
                        }
                    }
                }
            } catch (error) {
                console.error('Error checking file modifications:', error);
                // Reduce polling frequency on error
                if (this.fileCheckInterval) {
                    clearInterval(this.fileCheckInterval);
                    this.fileCheckInterval = setInterval(() => {
                        if (this.currentMission?.id) {
                            this.checkFileModifications();
                        }
                    }, 5000); // Increase interval to 5 seconds on error
                }
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
                if (!this.currentMission) return;
                
                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) {
                    throw new Error('Failed to load files');
                }
                
                this.files = await response.json();
            } catch (error) {
                this.error = error.message;
                console.error('Error loading files:', error);
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
                    const response = await fetch(
                        `/api/missions/${this.currentMission.id}/files/${encodeURIComponent(file.path)}`
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

            <div v-else class="flex-1 overflow-auto">
                <div class="bg-white shadow">
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
    `
};
