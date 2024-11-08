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
            flashingFiles: new Set() // Track flashing files
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
                if (newMission) {
                    this.loadMissionFiles();
                }
            }
        }
    },
    methods: {
        startFileWatcher() {
            this.fileCheckInterval = setInterval(() => {
                if (this.currentMission) {
                    this.checkFileModifications();
                }
            }, 2000); // Check every 2 seconds
        },

        async checkFileModifications() {
            try {
                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) {
                    throw new Error('Failed to check files');
                }
                
                const newFiles = await response.json();
                
                // Compare modification timestamps
                newFiles.forEach(newFile => {
                    const existingFile = this.files.find(f => f.path === newFile.path);
                    if (existingFile && existingFile.modified !== newFile.modified) {
                        // File modified - trigger flash
                        this.flashFile(newFile.path);
                        // Update file data
                        Object.assign(existingFile, newFile);
                    }
                });
                
            } catch (error) {
                console.error('Error checking file modifications:', error);
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
        }
    },
    template: `
        <div class="h-full flex flex-col">
            <div class="bg-white shadow px-6 py-4 mb-4">
                <h2 class="text-2xl font-bold">Files</h2>
            </div>

            <div v-if="loading" class="flex-1 flex items-center justify-center">
                <p class="text-gray-600">Loading files...</p>
            </div>

            <div v-else-if="error" class="flex-1 flex items-center justify-center">
                <p class="text-red-500">{{ error }}</p>
            </div>

            <div v-else class="flex-1 overflow-auto">
                <div class="bg-white shadow overflow-hidden">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modified</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            <tr v-for="file in files" 
                                :key="file.path" 
                                class="hover:bg-gray-50 transition-colors duration-200"
                                :class="{ 'bg-yellow-100': isFlashing(file.path) }">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <i class="mdi mdi-file-document-outline text-gray-500 mr-2"></i>
                                        <span class="text-sm text-gray-900">{{ file.name }}</span>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {{ getFileSize(file) }}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {{ formatDate(file.modified) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `
};
