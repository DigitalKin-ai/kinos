# Interactive Manager Specification

## Overview
The Interactive Manager provides a user-controlled agent experience, allowing direct interaction with KinOS's AI capabilities while maintaining structured workflows and mission context.

## Core Components

### 1. Command Interface
- Triggered via `kin interactive`
- Operates independently from autonomous agents
- Maintains separate history and context files
- Uses dedicated chat sessions

### 2. Operation Phases

#### 2.1 Planning Phase
1. **Context Display**
   - Shows current todolist.md content
   - Displays mission context if relevant
   - Shows current project status

2. **Objective Setting**
   - User inputs desired objective
   - System processes input through two GPT analyses:
     1. **Objective Analysis**
        - Input: User objective + todolist + mission
        - Output: Mission-contextualized objective
        - Purpose: Align user intent with mission goals
     2. **File Context Analysis**
        - Input: Processed objective + todolist + mission + repo structure
        - Output: List of relevant files for context
        - Purpose: Identify required files for changes

3. **Validation**
   - Display processed objective
   - Show selected context files
   - User confirms (Y/N):
     - Yes: Save to .aider.objective.interactive.md
     - No: Return to objective input

#### 2.2 Action Phase
1. **Aider Session**
   - Launches interactive aider terminal
   - Configuration:
     - Uses --sonnet mode
     - Restores chat history
     - Loads selected context files
     - Applies objective context

2. **Session Management**
   - Maintains history in .aider.history.interactive.md
   - Allows natural interaction with aider
   - Preserves context between sessions
   - Handles CTRL+C for clean exit

3. **Cycle Control**
   - Session ends on CTRL+C
   - Returns to Planning Phase
   - Maintains continuous workflow

## File Structure

### Configuration Files
```
.aider.objective.interactive.md  # Current objective and context
.aider.history.interactive.md    # Session history
```

### File Handling
- Read-only access to mission and todolist
- Write access to specified target files
- Automatic backup of modified files
- Git integration for changes

## Workflow

### 1. Session Initialization
```bash
kin interactive
```

### 2. Planning Loop
```
1. Display todolist
2. Prompt for objective
3. Process objective (GPT)
4. Analyze file context (GPT)
5. User validation
6. Save or repeat
```

### 3. Action Loop
```
1. Launch aider session
2. Load context files
3. User interaction
4. Save on exit
5. Return to planning
```

## Implementation Requirements

### 1. Core Features
- Clean terminal interface
- Robust input handling
- Error recovery
- Session persistence
- Git integration

### 2. GPT Integration
- Objective processing
- Context analysis
- File selection
- Mission alignment

### 3. File Management
- Safe file operations
- Context preservation
- History tracking
- Change validation

### 4. User Experience
- Clear prompts
- Status feedback
- Error messages
- Help system
- Progress tracking

## Success Criteria

### 1. Functionality
- Successful objective processing
- Accurate file context selection
- Reliable aider integration
- Clean session management

### 2. User Experience
- Clear workflow progression
- Intuitive interactions
- Helpful feedback
- Error resilience

### 3. System Integration
- Mission alignment
- Project consistency
- History preservation
- Git compatibility

## Error Handling

### 1. Input Validation
- Objective format checking
- File path validation
- Context verification
- Permission checking

### 2. Recovery Procedures
- Session restoration
- Context preservation
- Change rollback
- History recovery

### 3. User Guidance
- Error explanations
- Correction suggestions
- Recovery options
- Help resources

## Future Enhancements

### 1. Planned Features
- Multiple objective tracking
- Enhanced context analysis
- Advanced file selection
- Progress visualization

### 2. Integration Options
- Team coordination
- Progress sharing
- Context expansion
- Enhanced validation

## Usage Examples

### 1. Basic Workflow
```bash
$ kin interactive
Current todolist:
[display todolist content]

Enter objective: Update user authentication
Processing objective...
Contextualized objective: Implement secure user authentication following project security requirements

Selected files:
- auth/user.py (📝 Main authentication logic)
- tests/test_auth.py (🧪 Test suite)
- config/security.yml (⚙️ Security configuration)

Proceed? [Y/n]: y
Launching aider session...
```

### 2. Complex Changes
```bash
$ kin interactive
[...]
Enter objective: Refactor database schema
[Process shows affected files across multiple components]
[User confirms]
[Aider session with comprehensive context]
```

## Implementation Notes

### 1. Code Organization
- Separate manager class
- Clean interface separation
- Modular components
- Clear dependencies

### 2. Performance
- Efficient file handling
- Smart context loading
- Optimized GPT usage
- Resource management

### 3. Maintenance
- Clear logging
- State tracking
- Error monitoring
- Version control
