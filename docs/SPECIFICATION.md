# KinOS v6 - Core Specifications

## 1. Foundational Principles

### Core Vision
KinOS v6 represents a fundamental shift towards true AI autonomy, implementing:
- Directory-based autonomous operation
- Simplified deployment and configuration
- Enhanced inter-agent collaboration
- Dynamic resource management
- Self-organizing team structures

### Key Innovations
1. **Context-Aware Operation**
   - Uses current directory as mission context
   - No complex configuration required
   - Dynamic permission management
   - Automatic resource discovery

2. **Team-Based Architecture**
   - Pre-configured specialized teams
   - Dynamic team formation
   - Role-based collaboration
   - Automatic resource allocation

3. **Resource Autonomy**
   - Self-managed compute resources
   - Dynamic scaling capabilities
   - Optimized resource sharing
   - Automatic cleanup and maintenance

## 2. Core Components

### 2.1 Agent System

#### Parallel Execution Framework
- Asynchronous agent execution using asyncio
- Configurable parallel agent count (--count parameter)
- Controlled agent startup with 10s delay between launches
- Dynamic task replacement when agents complete
- Lock-based synchronization for shared resources
- Comprehensive error handling and task recovery
- Automatic agent regeneration when missing

#### Base Agent Framework
- Autonomous file management
- Directory-based operation
- Dynamic resource allocation
- Self-monitoring capabilities
- Map maintenance using AiderManager

#### Core Agent Types
1. **SpecificationAgent**
   - Requirements analysis
   - Specification generation
   - Consistency validation
   - Documentation management

2. **ManagementAgent**
   - Project coordination
   - Resource allocation
   - Progress tracking
   - Team optimization

3. **writingAgent**
   - Content creation
   - Documentation writing
   - Style consistency
   - Format validation

4. **EvaluationAgent**
   - Quality assurance
   - Performance testing
   - Metrics analysis
   - Improvement suggestions

5. **DeduplicationAgent**
   - Content analysis and redundancy detection
   - Pattern matching and similarity scoring
   - Intelligent content splitting:
     - Directory-based organization
     - Section/subsection detection
     - Automatic file naming
     - Reference updating
   - Validation and error handling:
     - Content validation rules
     - Duplicate prevention
     - Git integration
     - Reference maintenance
   - Optimization suggestions:
     - Redundancy reports
     - Consolidation recommendations
     - Structure improvements
     - Cross-file analysis

6. **chroniclerAgent**
   - Progress tracking
   - History maintenance
   - Event logging
   - Timeline management

7. **redundancyAgent**
   - Backup verification
   - Redundancy management
   - Data consistency
   - Recovery planning

8. **ProductionAgent**
   - Code/content generation
   - Quality optimization
   - Dependency management
   - Testing integration

9. **researcherAgent**
   - Research coordination
   - Data gathering
   - Analysis synthesis
   - Knowledge integration

10. **IntegrationAgent**
    - System integration
    - Component linking
    - Interface management
    - Deployment coordination

### 2.2 Team System

#### Pre-configured Teams
1. **Book Writing Team**
   - Content creation focus
   - Documentation emphasis
   - Quality control integration
   - Version management

2. **Literature Review Team**
   - Research orientation
   - Analysis capabilities
   - Source management
   - Citation handling

3. **Coding Team**
   - Development focus
   - Testing integration
   - Documentation automation
   - Code quality control

#### Team Management
- Unified control interface
- Real-time status monitoring
- Performance metrics
- Resource optimization

### 2.3 Service Layer

#### Core Services
1. **AgentService**
   - Lifecycle management
   - Configuration handling
   - Status monitoring
   - Error recovery

2. **TeamService**
   - Team coordination
   - Resource allocation
   - Performance tracking
   - Load balancing

3. **NotificationService**
   - Real-time updates
   - Priority management
   - Message queuing
   - Status broadcasting

4. **CacheService**
   - Multi-level caching
   - Invalidation management
   - Resource optimization
   - Performance monitoring

## 3. Technical Infrastructure

### 3.1 Error Management
- Centralized error handling
- Automatic retry mechanisms
- Circuit breaker patterns
- Error recovery protocols

### 3.2 File Operations
- Thread-safe access
- Automatic locking
- Path validation
- Permission management

### 3.3 Cache System
- LRU memory cache
- File content caching
- Prompt caching
- Distributed caching support

### 3.3 Logging System
- Colored console output
- Multi-level logging (DEBUG to ERROR)
- Automatic tracking in suivi.md
- Agent-specific emoji tagging
- Success tracking for key operations

### 3.4 Notification System
- Real-time updates
- WebSocket support
- Priority queuing
- Message persistence
- Automatic logging to suivi.md for SUCCESS+ level events

## 4. Deployment & Configuration

### 4.1 System Requirements
- Python 3.9+
- 4GB RAM minimum
- 2 CPU cores
- Network access

### 4.2 Core Configuration
```env
# Essential Configuration
OPENAI_API_KEY=required
PERPLEXITY_API_KEY=required
DEBUG=boolean

# Model Configuration
DEFAULT_MODEL=gpt-4o-mini  # Default AI model to use
# Model can be overridden with --model flag

# Performance Settings
CACHE_DURATION=3600
RETRY_ATTEMPTS=3
NOTIFICATION_QUEUE_SIZE=500
```

### 4.3 Security Measures
- Path validation
- Permission checking
- Access control
- Error sanitization

### 4.4 AI Model
- Uses OpenAI's gpt-4o-mini model exclusively
- Consistent model usage across all components

## 5. Development Guidelines

### 5.1 Adding Components
1. **New Agents**
   - Inherit from AiderAgent
   - Implement core methods
   - Configure paths
   - Register in system

2. **New Services**
   - Inherit from BaseService
   - Implement standard methods
   - Add error handling
   - Register service

### 5.2 Best Practices
- Use safe operations
- Implement proper error handling
- Maintain thread safety
- Document changes

## 6. Usage Patterns

### 6.1 Basic Operation
```bash
# Launch with default team
kin

# Launch specific team
kin book-writing

# Custom path launch
kin book-writing -p /path/to/project
```

### 6.2 Team Management
```python
# Start team
team_service.start_team("book-writing")

# Monitor status
team_service.get_status()

# Stop team
team_service.stop_team()
```

## 7. Implementation Rules

### 7.1 Core Principles

#### Validation First
1. **Input Validation**
   - Validate all required fields before processing
   - Check resource availability upfront
   - Verify agent capabilities immediately
   - Surface validation errors clearly
   - No processing without complete validation

2. **State Validation**
   - Verify current state validity for each action
   - Check state transition permissions
   - Validate operation outcomes
   - Surface state errors immediately
   - Maintain clear state boundaries

#### Clear States
1. **Explicit State Management**
   - Define clear system states
   - Document all valid state transitions
   - Track state changes comprehensively
   - Maintain state history
   - Surface state conflicts immediately

2. **Error Handling**
   - Log all errors immediately
   - Update system state on errors
   - Notify relevant components
   - Attempt recovery when possible
   - Document error resolution

### 7.2 Development Flow

#### Quick Cycles
1. **Rapid Testing**
   - Create quick prototypes
   - Test immediately
   - Validate results fast
   - Detect patterns early
   - Document findings promptly

2. **Pattern Recognition**
   - Identify known patterns
   - Document new patterns
   - Validate pattern effectiveness
   - Share pattern insights
   - Apply patterns systematically

#### Continuous Enhancement
1. **Pattern Application**
   - Apply relevant patterns
   - Validate improvements
   - Document effectiveness
   - Share successful patterns
   - Iterate on failures

2. **Progress Tracking**
   - Monitor pattern usage
   - Track error rates
   - Measure performance
   - Assess stability
   - Document improvements
