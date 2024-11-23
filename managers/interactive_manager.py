import os
import asyncio
import openai
import requests
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
        self._init_history_files()
        
    def _init_history_files(self):
        """Initialize history files for interactive session."""
        self.history_file = '.aider.history.interactive.md'
        self.input_file = '.aider.input.interactive.md'
        
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
            # Refresh visualization
            self.logger.info("🎨 Refreshing repository visualization...")
            await self.vision_manager.generate_visualization()
            
            # Display current todolist
            if os.path.exists('todolist.md'):
                with open('todolist.md', 'r', encoding='utf-8') as f:
                    todolist = f.read()
                self.logger.info("\n📋 Current Todolist:\n")
                print(todolist)
            
            # Get multi-line user objective
            self.logger.info("\n🎯 Enter your objective (or 'quit' to exit):")
            self.logger.info("💡 Multi-line input: Enter a blank line or type 'done' to finish")
            self.logger.info("❌ Use Ctrl+C to cancel at any time")
            
            objective_lines = []
            while True:
                try:
                    line = input("> " if not objective_lines else "... ")
                    if line.strip().lower() in ('quit', 'exit', 'q'):
                        return None
                    if line.strip().lower() == 'done' or (not line.strip() and objective_lines):
                        break
                    objective_lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    # Handle Ctrl+D/Z or Ctrl+C gracefully
                    print("\nInput completed.")
                    break

            objective = "\n".join(objective_lines)
            if not objective.strip():
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
            
            # Extract and validate files from objective
            files_to_modify = []
            filtered_lines = []
            
            for line in objective.split('\n'):
                if line.strip().startswith('- ./'):
                    # Extract file path and description
                    parts = line.strip()[3:].split(' ', 1)
                    file_path = parts[0]
                    description = parts[1] if len(parts) > 1 else ""
                    
                    if os.path.exists(file_path):
                        files_to_modify.append((file_path, description))
                        filtered_lines.append(line)
                    else:
                        self.logger.warning(f"⚠️ Skipping missing file: {file_path}")
                else:
                    filtered_lines.append(line)

            if not files_to_modify:
                self.logger.error("❌ No valid files to modify")
                raise ValueError("No valid files to modify")

            # Display contents of files to be modified
            self.logger.info("\n📄 Files to be modified:")
            for file_path, description in files_to_modify:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    self.logger.info(f"\n📎 {file_path} {description}")
                    print(f"```\n{content}\n```")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read {file_path}: {str(e)}")

            # Ask for confirmation
            print("\nProceed with modifications? [Y/n]")
            confirm = input("> ").strip().lower()
            if confirm not in ('y', 'yes', ''):
                self.logger.info("❌ Operation cancelled by user")
                return

            # Update objective with only existing files
            filtered_objective = '\n'.join(filtered_lines)
            with open('.aider.objective.interactive.md', 'w', encoding='utf-8') as f:
                f.write(filtered_objective)

            await self.aider_manager.run_aider(
                objective_filepath='.aider.objective.interactive.md',
                agent_filepath=None,  # No agent file needed for interactive
                model="gpt-4o-mini"
            )
            
        except Exception as e:
            self.logger.error(f"Action phase error: {str(e)}")
            raise

    async def _research_objective(self, query):
        """Perform research using Perplexity API if needed."""
        try:
            perplexity_key = os.getenv('PERPLEXITY_API_KEY')
            if not perplexity_key:
                return None
                
            headers = {
                "Authorization": f"Bearer {perplexity_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "system", "content": "You are a helpful research assistant providing accurate, detailed information."},
                    {"role": "user", "content": query}
                ]
            }
            
            self.logger.info("🔍 Executing research query...")
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            self.logger.success("✨ Research query completed")
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                self.logger.warning(f"⚠️ Perplexity API call failed with status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.warning(f"⚠️ Research failed: {str(e)}")
            return None

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
                    
            self.logger.info("🤖 Starting objective processing...")
            self.logger.info("   - Loading mission context...")
            self.logger.info("   - Analyzing current todolist...")
            self.logger.info("   - Generating enhanced objective...")
            
            # Create the prompt
            system_prompt = """You are an AI project manager helping to process user objectives.
Your task is to analyze and enhance user objectives to align with the project mission and current state.

Format the objective to include:
1. Clear action items
2. Success criteria
3. Constraints and requirements
4. Validation steps"""

            user_prompt = f"""
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

Process this objective to be more specific and actionable while maintaining alignment with the mission."""

            # Log the prompts at debug level
            self.logger.debug("\n🔍 GPT SYSTEM PROMPT:\n" + system_prompt)
            self.logger.debug("\n🔍 GPT USER PROMPT:\n" + user_prompt)
            
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                stream=True  # Enable streaming
            )
            
            # Stream the response
            result = []
            print("\n📝 Enhanced objective:")
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    result.append(content)
                    print(content, end='', flush=True)
            print("\n")  # Add newline after streaming
            
            final_result = ''.join(result)
            self.logger.success("✨ Objective processing completed")
            return final_result
            
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
            self.logger.info("🔍 Analyzing file context with GPT...")
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            self.logger.success("✨ File context analysis completed")
            return result
            
        except Exception as e:
            self.logger.error(f"File context analysis error: {str(e)}")
            raise

    async def _should_continue(self):
        """Check if user wants to continue with another objective."""
        print("\n🔄 Would you like to work on another objective? [Y/n]")
        response = input("> ").strip().lower()
        return response in ('y', 'yes', '')
