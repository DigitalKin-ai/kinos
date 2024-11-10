export default {
    name: 'Header',
    props: {
        currentMission: {
            type: Object,
            default: () => null
        }
    },
    delimiters: ['${', '}'],
    template: `
        <div class="bg-black shadow">
            <div class="max-w-full mx-auto px-6 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-white">⚫ KinOS</h1>
                        <div v-if="currentMission" class="ml-6 flex items-center">
                            <span class="text-sm text-gray-400">Mission:</span>
                            <span class="ml-2 text-sm font-medium text-white">\${currentMission.name}</span>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <a href="/agents" class="text-gray-400 hover:text-white">
                            <i class="mdi mdi-robot"></i>
                            Agents
                        </a>
                        <a href="/teams" class="text-gray-400 hover:text-white">
                            <i class="mdi mdi-account-group"></i>
                            Teams
                        </a>
                        <a href="/files" class="text-gray-400 hover:text-white">
                            <i class="mdi mdi-folder"></i>
                            Files
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `
};
