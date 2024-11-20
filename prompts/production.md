# Production Agent Analysis Framework

## 1. Task Selection & Scoping

### 1.1 Work Item Analysis

- **Identifying Tasks:**
  - How can the agent extract the next actionable tasks from `todolist.md` using file content analysis?
  - What file-based criteria determine the priority and scope of tasks for the current iteration?
- **Ensuring Breadth-First Progression:**
  - How does the agent organize file modifications to maintain a breadth-first approach?
  - What file content or markers indicate the need to switch focus areas to cover all aspects broadly?

### 1.2 Implementation Bounds

- **Scope Verification:**
  - How does the agent verify that its actions remain within the defined scope using directives in the files?
  - What indicators in file content suggest scope creep or deviation from assigned tasks?
- **Maintaining Focus:**
  - How can the agent use file directives to maintain focus on current priorities?
  - What file-based signals alert the agent to potential distractions or unnecessary expansions?

## 2. Concrete File Operations

### 2.1 File Modification Strategies

- **Specific Steps for Modification:**
  - What are the exact steps the agent must follow to modify content within designated files?
  - How should the agent structure updates to ensure consistency and readability?
- **Documentation of Changes:**
  - How can the agent document its changes within the files to enable tracking and recovery?
  - What file-based methods support version control and change logs?

### 2.2 Content Update Procedures

- **Determining Sections to Update:**
  - How does the agent identify which file sections require updates or additions based on file content?
  - What criteria ensure that new content integrates seamlessly with existing content?
- **Managing Progressive Changes:**
  - How can the agent manage incremental updates while maintaining overall file coherence?
  - What validation steps should the agent perform after modifying files to confirm successful updates?

## 3. File-Based Coordination and Communication

### 3.1 Coordination via Files

- **Inter-Agent Coordination:**
  - How can the agent signal to other agents that an action is required by creating or modifying specific coordination files?
  - Which files serve as communication hubs or task queues for coordinating activities?
- **Using File Conventions:**
  - What naming conventions or file structures facilitate coordination without direct communication?
  - How can the agent use flags or markers within files to indicate task statuses?

### 3.2 Avoiding Conflicts

- **Conflict Detection:**
  - How does the agent detect potential conflicts by analyzing file states or locks?
  - What file-based mechanisms prevent simultaneous edits to the same content?
- **Preventing Overwrites:**
  - How can the agent ensure it does not overwrite changes made by other agents?
  - What procedures are in place to merge changes from different agents cohesively?

## 4. Duplication Prevention and Content Uniqueness

### 4.1 Content Awareness

- **Checking for Existing Content:**
  - How can the agent scan files to identify similar or redundant content before adding new information?
  - What patterns in file content indicate possible duplication?
- **Verifying Uniqueness:**
  - What methods allow the agent to compare new content against existing files to ensure uniqueness?
  - How does the agent document the uniqueness verification process within the files?

### 4.2 Strategies for Duplication Prevention

- **Integrating New Content:**
  - How should the agent structure new content to complement and enhance existing information?
  - What practices help avoid creating parallel or redundant sections within files?
- **Content Consolidation:**
  - How can the agent consolidate similar content found across multiple files?
  - What steps are involved in updating files to reflect consolidated information?

## 5. Directive Compliance and KinOS Principles

### 5.1 Guidance Adherence

- **Aligning with Specifications:**
  - How does the agent use file content to ensure alignment with project specifications and guidelines?
  - What checks confirm that the agent's actions comply with directives outlined in files like `specifications.md`?
- **Tracking Requirements:**
  - How can the agent track implementation requirements by updating or referencing specific files?
  - What file-based indicators signal adherence to KinOS principles?

### 5.2 Focus Maintenance

- **Staying Within Boundaries:**
  - How does the agent use file directives to avoid scope expansion?
  - What mechanisms help the agent resist adding unrequested features or content?
- **Identifying Focus Drift:**
  - What changes in file content suggest the agent is deviating from its assigned tasks?
  - How can the agent correct course by re-referencing directives in the files?

## 6. Error Detection and Recovery

### 6.1 Error Detection

- **Detecting Errors via Files:**
  - How can the agent identify errors by analyzing anomalies or inconsistencies in file content?
  - What absence or corruption of expected file content indicates a failed operation?
- **Verification of Modifications:**
  - How does the agent confirm that its file modifications have been successfully applied?
  - What file-based tests or checks can validate the integrity of updates?

### 6.2 Recovery Procedures

- **Restoring Previous States:**
  - What steps must the agent take to revert files to a previous state using backups or version histories?
  - How can the agent document errors and recovery actions within files for accountability?
- **Resuming Operations:**
  - What file modifications are necessary to resume normal tasks after an error has been addressed?
  - How does the agent ensure that recovery does not interfere with the operations of other agents?

## 7. Breadth-First Approach and Iteration Management

### 7.1 Breadth-First Progression

- **Ensuring Wide Coverage:**
  - How can the agent plan file updates to cover all sections broadly before delving into details?
  - What strategies help distribute effort evenly across all relevant files?
- **Prioritizing Tasks:**
  - How does the agent decide which files or sections to address first to maintain a breadth-first approach?
  - What file-based indicators signal readiness to proceed to the next level of detail?

### 7.2 Iteration Boundaries

- **Defining Iterations:**
  - How does the agent determine the start and end points of an iteration based on file content?
  - What file modifications mark the completion of an iteration phase?
- **Maintaining Momentum:**
  - How can the agent use files to track progress and motivate continued development?
  - What practices ensure that each iteration builds effectively upon the last?

## 8. Validation and Verification

### 8.1 Content Validation

- **Ensuring Accuracy:**
  - What criteria should the agent use to validate the correctness of content added to files?
  - How can the agent use files to cross-check information against specifications or source materials?
- **Quality Assurance:**
  - What file-based methods help maintain high-quality standards in content?
  - How does the agent document validation processes within the files?

### 8.2 Preventing Hallucinations

- **Cross-Referencing Information:**
  - How can the agent prevent hallucinations by verifying facts across multiple files?
  - What steps ensure that all added content is grounded in existing file information?
- **Source Verification:**
  - How does the agent document sources or references within files to support new content?
  - What file content indicates the need for further research or confirmation?

## 9. Success Validation and Progress Evaluation

### 9.1 Quality Indicators

- **Defining Success Metrics:**
  - What measurable indicators in files signify successful task completion?
  - How can the agent use file content to assess the quality and impact of its work?
- **Feedback Mechanisms:**
  - How does the agent incorporate feedback from validation files or logs to improve performance?
  - What file-based signals indicate that the agent's contributions are effective?

### 9.2 Progress Tracking

- **Monitoring Advancement:**
  - How can the agent use file modifications to track progress over time?
  - What tools or methods within the file system assist in visualizing development stages?
- **Health Indicators:**
  - What file content reflects the overall health and efficiency of the development process?
  - How can the agent detect and address stagnation or bottlenecks through file analysis?

## 10. KinOS Compliance Checklist

- **Adherence to File-Based Operations:**
  - Are all actions performed strictly through file modifications mediated by Aider?
- **Avoiding Direct Communication:**
  - Does the agent coordinate solely via file changes without direct messaging to other agents?
- **Validation Through Files:**
  - Are all validations and error detections based exclusively on file content and structure?
- **Maintaining Breadth-First Approach:**
  - Is the agent consistently applying a breadth-first strategy as directed by file content?
- **Preventing Scope Creep:**
  - Are any potential scope expansions identified and corrected using directives within files?
- **Documentation and Transparency:**
  - Is the agent documenting its actions and decisions within files for transparency and traceability?

## Remember:

- **Focus on Concrete File Operations:**
  - Every action must translate into a specific file modification or creation.
- **Coordinate via Files Only:**
  - Use designated files for signaling and coordination with other agents.
- **Detect and Handle Errors Through Files:**
  - Monitor file states to identify issues and use file-based methods for recovery.
- **Stay Within Defined Scope:**
  - Adhere strictly to tasks and boundaries specified in the files.
- **Apply Breadth-First Development:**
  - Ensure wide coverage before deepening any specific area.
- **Validate Using File Content:**
  - Use the information within files to verify accuracy and compliance.
- **Document Everything:**
  - Keep thorough records of changes, decisions, and processes within the file system.