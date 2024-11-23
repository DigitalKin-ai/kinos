import os
import asyncio
import openai
from utils.logger import Logger
from utils.fs_utils import FSUtils
from managers.aider_manager import AiderManager
from managers.vision_manager import VisionManager

class InteractiveManager:
    """Manager class for interactive agent sessions."""
    
    def __init__(self):
        """Initialize the interactive manager."""
        self.logger = Logger()
        self.aider_manager = AiderManager()
        self.vision_manager = VisionManager()
        self.fs_utils = FSUtils()
        
    async def start_session(self):
        """Start an interactive session."""
        try:
            while True:  # Main interaction loop
                # Planning Phase
                objective = await self._planning_phase()
                if not objective:
                    break
                    
                # Action Phase 
                await self._action_phase(objective)
                
                # Ask to continue
                if not await self._should_continue():
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("\n👋 Interactive session ended by user")
        except Exception as e:
            self.logger.error(f"❌ Session error: {str(e)}")
            raise

    async def _planning_phase(self):
        """Execute the planning phase of interaction."""
        try:
            # Display current todolist
            if os.path.exists('todolist.md'):
                with open('todolist.md', 'r', encoding='utf-8') as f:
                    todolist = f.read()
                self.logger.info("\n📋 Current Todolist:\n")
                print(todolist)
            
            # Get user objective
            print("\n🎯 Enter your objective (or 'quit' to exit):")
            objective = input("> ").strip()
            
            if objective.lower() in ('quit', 'exit', 'q'):
                return None
                
            # Process objective with GPT
            processed_objective = await self._process_objective(objective)
            
            # Get file context
            file_context = await self._analyze_file_context(processed_objective)
            
            # Display and confirm
            self.logger.info("\n📝 Processed Objective:")
            print(processed_objective)
            
            self.logger.info("\n📁 Selected Files:")
            for file_info in file_context.split('\n'):
                if file_info.strip():
                    print(file_info)
                    
            # Get user confirmation
            print("\nProceed with this objective? [Y/n]")
            confirm = input("> ").strip().lower()
            
            if confirm in ('y', 'yes', ''):
                # Save objective
                with open('.aider.objective.interactive.md', 'w', encoding='utf-8') as f:
                    f.write(f"# Interactive Session Objective\n\n{processed_objective}\n\n## File Context\n\n{file_context}")
                return processed_objective
                
            return await self._planning_phase()  # Retry if not confirmed
            
        except Exception as e:
            self.logger.error(f"Planning phase error: {str(e)}")
            raise

    async def _action_phase(self, objective):
        """Execute the action phase with aider."""
        try:
            self.logger.info("\n🚀 Starting aider session...")
            
            await self.aider_manager.run_aider(
                objective_filepath='.aider.objective.interactive.md',
                agent_filepath=None,  # No agent file needed for interactive
                model="gpt-4o-mini"
            )
            
        except Exception as e:
            self.logger.error(f"Action phase error: {str(e)}")
            raise

    async def _process_objective(self, objective):
        """Process user objective through GPT."""
        try:
            # Load mission if available
            mission_content = ""
            if os.path.exists('.aider.mission.md'):
                with open('.aider.mission.md', 'r', encoding='utf-8') as f:
                    mission_content = f.read()
            
            # Load todolist if available
            todolist_content = ""
            if os.path.exists('todolist.md'):
                with open('todolist.md', 'r', encoding='utf-8') as f:
                    todolist_content = f.read()
                    
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """You are an AI project manager helping to process user objectives.
Your task is to analyze and enhance user objectives to align with the project mission and current state.

Format the objective to include:
1. Clear action items
2. Success criteria
3. Constraints and requirements
4. Validation steps"""},
                    {"role": "user", "content": f"""
Mission Context:
```
{mission_content}
```

Current Todolist:
```
{todolist_content}
```

User Objective:
{objective}

Process this objective to be more specific and actionable while maintaining alignment with the mission."""}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Objective processing error: {str(e)}")
            raise

    async def _analyze_file_context(self, processed_objective):
        """Analyze and select relevant files for the objective."""
        try:
            # Get complete repository structure
            files = self.fs_utils.get_folder_files(".")
            subfolders = self.fs_utils.get_subfolders(".")
            tree_structure = self.fs_utils.build_tree_structure(
                current_path=".",
                files=files,
                subfolders=subfolders,
                max_depth=None  # No depth limit
            )
            tree_text = "\n".join(tree_structure)

            # Generate fresh visualization
            await self.vision_manager.generate_visualization()
            
            # Read diagram if available
            diagram_content = None
            if os.path.exists('./diagram.png'):
                try:
                    with open('./diagram.png', 'rb') as f:
                        diagram_content = f.read()
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read diagram.png: {str(e)}")

            # Initialize messages list
            messages = [
                {"role": "system", "content": """You are a technical analyst selecting relevant files for a development objective.
List files in two categories:
1. Context Files (read-only, needed for understanding)
2. Write Files (to be modified)

Format:
# Context Files (read-only)
- path/to/file1 (emoji) Purpose
- path/to/file2 (emoji) Purpose

# Write Files (to be modified)
- path/to/file3 (emoji) Purpose
- path/to/file4 (emoji) Purpose"""}
            ]

            # Add diagram if available
            if diagram_content:
                try:
                    import base64
                    encoded_bytes = base64.b64encode(diagram_content).decode('utf-8')
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded_bytes}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Above is the current project structure visualization. Use it to inform your file selection."
                            }
                        ]
                    })
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not encode diagram: {str(e)}")

            # Add main analysis prompt
            messages.append({
                "role": "user", 
                "content": f"""
Objective:
```
{processed_objective}
```

Project Structure:
```
{tree_text}
```

Select relevant files for this objective, following the format above."""
            })
            
            # Make API call with enhanced context
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"File context analysis error: {str(e)}")
            raise

    async def _should_continue(self):
        """Check if user wants to continue with another objective."""
        print("\n🔄 Would you like to work on another objective? [Y/n]")
        response = input("> ").strip().lower()
        return response in ('y', 'yes', '')
