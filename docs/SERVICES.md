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

### 2.4 map_manager Service
- Context-aware file mapping
- Gitignore integration
- Intelligent file selection
- Path validation

### 2.5 aider_manager Service
- Commit type detection
- Emoji-based logging
- Command validation
- History tracking

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
