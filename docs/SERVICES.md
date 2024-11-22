# KinOS v6 Service Specifications

## 1. File Structure
KinOS manages state through standardized files in the mission directory:
- `.aider.mission.md`: Core mission definition and parameters
- `.aider.agent.{agentname}.md`: Agent-specific system prompt
- `.aider.objective.{agentname}.md`: Current objective for specific agent
- `.aider.map.{agentname}.md`: Context map for agent operations

## 2. Core Services

### 2.1 agents_runner Service
- Parallel agent execution using asyncio
- Dynamic agent count management via --count parameter
- Automatic agent generation when missing
- Mission-based operation
- Synchronized resource access using locks
- Controlled agent startup (10s delay between launches)
- Dynamic task replacement for completed agents
- Comprehensive error handling and recovery
- Thread-safe agent selection and management

### 2.2 agents_manager Service
- Mission-driven agent generation
- Multi-encoding file support
- Parallel agent creation
- GPT-4o-mini integration

### 2.3 objective_manager Service
- Dynamic objective generation
- Perplexity research integration
- Multi-encoding support
- Progress tracking
- Automatic summarization

### 2.5 AiderManager Service
- Handles map maintenance operations
- Uses `kin run map` command to initiate map maintenance
- Integrates with other components for seamless operation
- Commit type detection
- Emoji-based logging
- Command validation
- History tracking

### 2.6 MapManager Service
- **Folder-Centric Operation**
  - Analyzes project structure by folder
  - Maintains folder-specific context maps
  - Tracks folder-level changes
  - Updates only on structural changes

### 2.7 VisionManager Service
- **Repository Visualization**
  - Automatic repo-visualizer installation and setup
  - Dynamic SVG generation
  - Interactive project structure visualization
  - Configurable depth and colors
  - Gitignore integration

- **Installation Management**
  - Automatic Node.js dependency check
  - Seamless repo-visualizer setup
  - Dependency installation handling
  - Build process automation

- **Configuration**
  - Customizable visualization depth
  - File extension color schemes
  - Ignore pattern management
  - Layout customization options

- **Integration**
  - Automatic map updates on changes
  - Path validation and security
  - Error handling and recovery
  - Progress logging and feedback
- **Repository Visualization**
  - Local installation of repo-visualizer
  - Automatic build process
  - Configuration management
  - SVG generation
  - Path validation

- **Installation Management**
  - Automatic dependency installation
  - Build process handling
  - Version control integration
  - Error recovery

- **Configuration**
  - Custom color schemes
  - Depth control
  - File exclusions
  - Layout options

- **Integration**
  - Node.js compatibility check
  - Build verification
  - Path management
  - Error handling
  - Analyzes project structure by folder
  - Maintains folder-specific context maps
  - Tracks folder-level changes
  - Updates only on structural changes

- **Change Detection**
  - Monitors file creation/deletion
  - Ignores content-only changes
  - Maintains folder integrity
  - Updates parent folder contexts

- **Context Analysis**
  - Evaluates folder purpose
  - Analyzes file grouping logic
  - Maps inter-folder relationships
  - Documents structural dependencies

- **Map Generation**
  - Creates folder-specific maps
  - Includes folder purpose explanation
  - Documents file relationships
  - Maintains hierarchical context

- **File Categories**
  - Core Project Files (📊 PRIMARY, 📋 SPEC, ⚙️ IMPL, 📚 DOCS)
  - Support Files (⚡ CONFIG, 🛠️ UTIL, 🧪 TEST, 📦 BUILD)
  - Working Files (✍️ WORK, 📝 DRAFT, 📄 TEMPLATE, 📂 ARCHIVE)
  - Data Files (💾 SOURCE, ⚡ GEN, 💫 CACHE, 💿 BACKUP)

- **Integration**
  - Works with git for change detection
  - Coordinates with redundancy manager
  - Supports agent operations
  - Maintains global project context

## 3. Service Integration

### 3.1 Communication
- File-based state sharing
- Clear state boundaries
- Atomic operations
- Validated transitions
- Multi-encoding support

### 3.2 Error Handling
- Clear error states
- Comprehensive logging
- Success tracking
- Automatic file logging
- Emoji-based status

### 3.3 Cache System
- LRU memory cache
- File content caching
- Prompt caching
- Distributed caching support

### 3.4 Notification System
- Real-time updates
- WebSocket support
- Priority queuing
- Message persistence
- Automatic logging to suivi.md

Note: le modèle LLM à appeler est "gpt-4o-mini" de OpenAI. "o" est pour "Omni", c'est le seul modèle qui doit être appelé
