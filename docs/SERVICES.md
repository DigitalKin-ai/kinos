# KinOS v6 Service Specifications

## 1. File Structure
KinOS manages state through standardized files in the mission directory:
- `.aider.mission.md`: Core mission definition and parameters
- `.aider.agent.{agentname}.md`: Agent-specific system prompt
- `.aider.objective.{agentname}.md`: Current objective for specific agent
- `.aider.map.{agentname}.md`: Context map for agent operations

## 2. Core Services

### 2.1 agents_runner Service
**Command**: `kin run agents`

#### Purpose
Primary execution loop managing agent selection and execution cycle.

#### Operation Flow
1. **Agent Generation Check**
   - Verify existence of agent files
   - Generate missing agents if needed

2. **Random Agent Selection**
   - Select available agent randomly

3. **Execution Cycle**
   - Generate new objective for selected agent
   - Calculate context map
   - Execute aider operation

### 2.2 agents_manager Service
**Command**: `kin generate agents --mission MISSIONFILEPATH`

#### Purpose
Generates mission-specific agent prompts.

#### Operation Flow
1. **Mission Analysis**
   - Load mission specification
   - Analyze requirements
   - Determine agent needs

2. **Agent Generation**
   - Make 8 distinct GPT-4o-mini calls
   - Generate specialized agent configurations
   - Each call uses agent-specific prompts

3. **State Storage**
   - Create `.aider.agent.{name}.md` files
   - Store agent configurations

#### Agent Types
- Each agent gets specialized prompt
- Unique prompt per agent type

### 2.3 objective_manager Service
**Command**: `kin generate objective --mission MISSIONFILEPATH --agent AGENTFILEPATH --map MAPFILEPATH(*)`

#### Purpose
Generates current objective for specific agent.

#### Operation Flow
1. **Context Analysis**
   - Load mission
   - Consider current context

2. **Objective Generation**
   - Make GPT-4o-mini call
   - Generate specific objective
   - Consider agent capabilities

3. **State Storage**
   - Create `.aider.objective.{agentname}.md`
   - Store objective details
   - Update agent state

### 2.4 map_manager Service
**Command**: `kin generate map --mission MISSIONFILEPATH(*) --objective OBJECTIVEFILEPATH --agent AGENTFILEPATH(*)`

#### Purpose
Generates context map for agent operations.

#### Operation Flow
1. **Context Analysis**
   - Analyze available files

2. **Map Generation**
   - Make GPT-4o-mini call
   - Generate context mapping
   - Optimize for objective

3. **State Storage**
   - Create `.aider.map.{agentname}.md`
   - Store context mappings

### 2.5 aider_manager Service
**Command**: `kin run aider --objective OBJECTIVEFILEPATH --MAP MAPFILEPATH --agent AGENTFILEPATH`

#### Purpose
Executes aider operations with defined context.

#### Operation Flow
1. **Context Setup**
   - Load objective details
   - Process context map
   - Prepare agent prompt

2. **Aider Execution**
   - Configure aider command
   - Pass mapped files as context
   - Set agent file as read-only
   - Execute operation

3. **Result Management**
   - Capture operation results
   - Log commits

## 3. Service Integration

### 3.1 Communication
- File-based state sharing
- Clear state boundaries
- Atomic operations
- Validated transitions

### 3.2 Error Handling
- Clear error states
- Error logging

Note: le modèle LLM à appeler est "gpt-4o-mini" de OpenAI. "o" est pour "Omni", c'est le seul modèle qui doit être appelé