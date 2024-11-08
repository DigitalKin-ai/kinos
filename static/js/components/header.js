export default {
    name: 'Header',
    props: {
        currentMission: {
            type: Object,
            default: null
        }
    },
    template: `
        <div class="bg-white shadow">
            <div class="max-w-full mx-auto px-6 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-gray-900">⚫ Parallagon</h1>
                        <div v-if="currentMission" class="ml-6 flex items-center">
                            <span class="text-sm text-gray-500">Mission:</span>
                            <span class="ml-2 text-sm font-medium text-gray-900">\${ currentMission.name }</span>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <a href="/editor" class="text-gray-500 hover:text-gray-900">
                            <i class="mdi mdi-pencil"></i>
                            Editor
                        </a>
                        <a href="/files" class="text-gray-500 hover:text-gray-900">
                            <i class="mdi mdi-folder"></i>
                            Files
                        </a>
                        <a href="/agents" class="text-gray-500 hover:text-gray-900">
                            <i class="mdi mdi-robot"></i>
                            Agents
                        </a>
                        <a href="/clean" class="text-gray-500 hover:text-gray-900">
                            <i class="mdi mdi-eye"></i>
                            Clean
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `
};
