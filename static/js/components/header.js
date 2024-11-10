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
        <div class="bg-black shadow h-16 flex items-center justify-center">
            <div class="max-w-full mx-auto px-6 w-full h-full flex items-center">
                <div class="flex justify-between items-center w-full">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-white flex items-center">
                            <span class="flex items-center">⚫ KinOS</span>
                        </h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <a href="/agents" class="text-gray-400 hover:text-white flex items-center gap-2">
                            <i class="mdi mdi-robot"></i>
                            Agents
                        </a>
                        <a href="/teams" class="text-gray-400 hover:text-white flex items-center gap-2">
                            <i class="mdi mdi-account-group"></i>
                            Équipes
                        </a>
                        <a href="/files" class="text-gray-400 hover:text-white flex items-center gap-2">
                            <i class="mdi mdi-folder"></i>
                            Fichiers
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `
};
