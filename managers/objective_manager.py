import os
import requests
from utils.logger import Logger
from utils.encoding_utils import EncodingUtils
from utils.fs_utils import FSUtils
import openai
from dotenv import load_dotenv

class ObjectiveManager:
    """Manager class for generating agent-specific objectives."""
    
    def __init__(self, model="gpt-4o-mini"):
        self.logger = Logger()
        self.encoding_utils = EncodingUtils()
        self.model = model
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Load mission content
        self.mission_content = self._load_mission_content()

    def generate_objective(self, mission_filepath=".aider.mission.md", agent_filepath=None):
        """
        Generate a specific objective for an agent based on mission and agent configuration.
        
        Args:
            mission_filepath (str): Path to mission specification file
            agent_filepath (str): Path to agent configuration file
            
        Raises:
            ValueError: If required files are invalid or missing
            IOError: If there are file operation issues
        """
        try:
            if not agent_filepath:
                raise ValueError("agent_filepath parameter is required")
                
            self.logger.info(f"🎯 Generating objective for agent: {agent_filepath}")
            
            # Validate input files exist and are readable
            if not os.path.exists(mission_filepath):
                raise ValueError(f"Mission file not found: {mission_filepath}")
                
            if not os.path.exists(agent_filepath):
                raise ValueError(f"Agent file not found: {agent_filepath}")
                
            if not os.access(mission_filepath, os.R_OK):
                raise ValueError(f"Cannot read mission file: {mission_filepath}")
                
            if not os.access(agent_filepath, os.R_OK):
                raise ValueError(f"Cannot read agent file: {agent_filepath}")
                
            # Extract agent name from filepath
            agent_name = self._extract_agent_name(agent_filepath)
            
            # Load content from files
            mission_content = self._read_file(mission_filepath)
            agent_content = self._read_file(agent_filepath)
            
            # Generate objective via GPT
            objective = self._generate_objective_content(mission_content, agent_content, agent_name)
        
            # Generate summary for logging
            summary = self._generate_summary(objective, agent_name, agent_content)  # Pass agent_content
            self.logger.success(summary)
        
            # Save objective
            output_path = f".aider.objective.{agent_name}.md"
            self._save_objective(output_path, objective, agent_name, agent_content)  # Pass agent_content
        
            self.logger.info(f"✅ Successfully generated objective for {agent_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Objective generation failed: {str(e)}")
            raise

    def _validate_file(self, filepath):
        """Validate file exists and is readable."""
        return filepath and os.path.exists(filepath) and os.access(filepath, os.R_OK)

    def _extract_agent_name(self, agent_filepath):
        """Extract agent name from filepath."""
        basename = os.path.basename(agent_filepath)
        return basename.replace('.aider.agent.', '').replace('.md', '')


    def _read_file(self, filepath):
        """Read content from file with robust encoding handling."""
        return self.encoding_utils.read_file_safely(filepath)

    def _generate_objective_content(self, mission_content, agent_content, agent_name):
        """Generate objective content using GPT."""
        try:
            client = openai.OpenAI()

            # Build list of all file paths
            files = []
            for root, _, filenames in os.walk('.'):
                # Skip any folder that starts with .
                if not any(part.startswith('.') for part in root.split(os.sep)[1:]):
                    for filename in filenames:
                        # Skip files that start with . or .aider
                        if not (filename.startswith('.') or filename.startswith('.aider')):
                            full_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(full_path, '.').replace(os.sep, '/')
                            files.append(f"- ./{rel_path}")

            # Create sorted list of paths
            tree_text = "\n".join(sorted(files)) if files else "No existing files"

            # Read last 80 lines from suivi.md if it exists
            suivi_content = ""
            if os.path.exists('suivi.md'):
                try:
                    with open('suivi.md', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        last_lines = lines[-80:] if len(lines) > 80 else lines
                        suivi_content = ''.join(last_lines)
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read suivi.md: {str(e)}")

            # Read todolist.md if it exists
            todolist = ""
            if os.path.exists('todolist.md'):
                try:
                    with open('todolist.md', 'r', encoding='utf-8') as f:
                        todolist = f.read()
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read todolist.md: {str(e)}")

            # Read and encode diagram.png if it exists
            diagram_content = None
            if os.path.exists('./diagram.png'):
                try:
                    with open('./diagram.png', 'rb') as f:
                        diagram_content = f.read()
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read diagram.png: {str(e)}")

            # Check for Perplexity API key
            perplexity_key = os.getenv('PERPLEXITY_API_KEY')
            if perplexity_key:
                search_instruction = """

4. **Search**
   - If research needed, add "Search:" line with query"""
            else:
                search_instruction = ""

            prompt = f"""
Mission
================
````
{mission_content}
````

Project Structure Diagram
================
The image attached is a visualization of the repository showing folders, file sizes and structure, that you can use to enhance your decision-making.

Recent Activity (last 80 lines)
================
````
{suivi_content}
````

Todolist
================
````
{todolist}
````

Instructions
================
Based on the provided info, generate a clear specific single next step for the {agent_name} agent.
Create two objectives in markdown format - one for production, one specific to your role. Each objective should specify:

1. **Action Statement**
   - Single, specific task to accomplish
   - Clear relation to current mission state
   - Within agent's documented capabilities

2. **Operation Type**
   - What kind of changes will be needed
   - Expected impact on system
   - Required capabilities

3. **Validation Points**
   - How to verify success
   - What output to check
   - Which states to validate{search_instruction}
"""
            #self.logger.info(f"OBJECTIVE PROMPT: {prompt}")

            # First get the main objective
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""
# Context

## KinOS Operation Parameters
You are an agent in KinOS v6, operating with these key capabilities:
- File operations through aider interface
- Single-step actions using GPT-4o-mini
- Directory-based scope (current working directory)
- Git integration for tracking changes

## Core Limitations
- One operation per planning cycle
- Cannot access external resources
- Must work through documented interfaces
- Changes limited to project files

## Action Requirements
Your proposals must be:
- Achievable in one aider operation
- Verifiable through file changes
- Within project directory scope

# Planning
Your planning:
- Prioritizes explicit mission instructions
- Follows the todolist
- Avoids repeating previous work
- Maintains clear progression
- Focuses on single, achievable steps                     

                     
# System Prompt
{agent_content}
"""}
                ],
                temperature=0.5,
                max_tokens=2000
            )

            # Get initial objective content
            objective = response.choices[0].message.content

            # Get file context for objective
            # Create file context prompt with logged tree text
            file_context_prompt = f"""
Objectives
================
````
{objective}
````

Project structure
================
````
{tree_text}
````

Instructions
================
"""
            # Log the complete prompt being sent to GPT
            self.logger.debug(f"File context prompt:\n{file_context_prompt}")

            # Add instructions to prompt
            file_context_prompt += """
Based on the objectives and the project structure, list the files needed to achieve both objectives, in this exact format:

# Context Files (read-only)
- path/to/file1 (emoji) File Role
- path/to/file2 (emoji) File Role

# Write Files (to be modified)
- path/to/file3 (emoji) File Role
- path/to/file4 (emoji) File Role

Rules:
1. Include directly relevant files
2. Context files = files needed for understanding/reference, or that could add interesting complementary info
3. Write files = files that will be modified
4. Use exact paths from project structure
5. Do not include files that don't exist
6. Include explanation about the role of each file, and a relevant emoji
7. Aim for 8 to 12 files

Respond only with the file lists in the format shown above.
"""

            try:
                file_context_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": """
{agent_content}
                         
In this context, you are a precise file context analyzer for AI development tasks.
"""},
                        {"role": "user", "content": file_context_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                file_context = file_context_response.choices[0].message.content.strip()
                # Log the response received
                self.logger.debug(f"File context response:\n{file_context}")
                
                # Add file context to objective
                objective += "\n\n# Required Files\n" + file_context

            except Exception as e:
                self.logger.warning(f"⚠️ Could not generate file context: {str(e)}")
                # Continue without file context

            # Initialize messages list
            messages = []
            
            # Add diagram if available
            if diagram_content:
                try:
                    import base64
                    # Encode bytes to base64
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
                                "text": "Above is the current project structure visualization. Use it to inform your objective planning."
                            }
                        ]
                    })
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not encode diagram: {str(e)}")

            # Add main prompt
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.5,
                max_tokens=2000
            )
            
            return objective
            
        except Exception as e:
            self.logger.error(f"GPT API call failed: {str(e)}")
            raise

    def _generate_summary(self, objective, agent_name, agent_content):
        """Generate a one-line summary of the objective."""
        try:
            client = openai.OpenAI()
            prompt = f'''
Mission Context
================
````
{self.mission_content}
````

Objective
================
````
{objective}
````

Instructions
================
Based on the Objective, summarize in a single sentence what the agent is currently doing as part of the mission, strictly following this format:
"Agent {agent_name}: I'm [action] [objective] [optional detail] [files to be modified]"

Guidelines:
- Don't repeat the mission (which is known to the user), but only what the agent is precisely doing within it
- Don't repeat information already present in the tracking logs
- Use appropriate emojis based on the type of action
- Phrase it from your agent point of view

Reply only with the formatted sentence, nothing else.
'''
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f'''
{agent_content}
                     
In this context, you are an assistant who summarizes project actions in a concise sentence with appropriate emojis. These summaries will serve as tracking logs within the mission.'''},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {str(e)}")
            # Return a basic fallback summary
            return f"Agent {agent_name} 🤖 will execute a new task"

    def _generate_research_summary(self, query, result, agent_name, agent_content):
        """Generate a summary of the Perplexity research results."""
        try:
            client = openai.OpenAI()
            prompt = f'''
Search Query 
================
````
{query}
````

Complete Results
================
````
{result}
````

Instructions
================
Summarize in a single sentence what was found by the Perplexity search, following this format:
"Agent {agent_name}: I'm conducting a search on [topic]: [summary of main findings]"

Reply only with the formatted sentence, nothing else.
'''
             
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f'''
{agent_content}

In this context, you are an assistant who summarizes project actions in a concise sentence with appropriate emojis. These summaries will serve as tracking logs within the mission.
'''},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate research summary: {str(e)}")
            # Return a basic fallback summary with agent name
            return f"Agent {agent_name} 🤖 searched for: {query}"


    def _load_mission_content(self):
        """Load mission content from .aider.mission.md file."""
        try:
            if os.path.exists('.aider.mission.md'):
                return self.encoding_utils.read_file_safely('.aider.mission.md')
            return ""
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load mission file: {str(e)}")
            return ""

    def _save_objective(self, filepath, content, agent_name, agent_content):
        """Save objective content to file, including Perplexity research results if needed."""
        try:
            # Extract agent name from filepath
            agent_name = os.path.basename(filepath).replace('.aider.objective.', '').replace('.md', '')
            
            # Check for research requirement
            if "Search:" in content:
                # Extract research query
                research_lines = [line.strip() for line in content.split('\n') 
                                if line.strip().startswith("Search:")]
                if research_lines:
                    research_query = research_lines[0].replace("Search:", "").strip()
                    
                    # Call Perplexity API
                    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
                    if not perplexity_key:
                        raise ValueError("Perplexity API key not found in environment variables")
                        
                    # Make Perplexity API call with correct format
                    headers = {
                        "Authorization": f"Bearer {perplexity_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [
                            {"role": "system", "content": "You are a helpful research assistant providing accurate, detailed information."},
                            {"role": "user", "content": research_query}
                        ]
                    }
                    
                    try:
                        response = requests.post(
                            "https://api.perplexity.ai/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=30  # Add timeout
                        )
                        
                        if response.status_code == 200:
                            research_result = response.json()["choices"][0]["message"]["content"]
                            
                            # Generate summary of research results with agent name
                            research_summary = self._generate_research_summary(
                                research_query, 
                                research_result, 
                                agent_name,
                                agent_content
                            )
                            self.logger.success(research_summary)
                            
                            # Add research results to objective
                            content += "\n\n## Additional Information\n"
                            content += f"Perplexity search results for: {research_query}\n\n"
                            content += research_result
                        else:
                            error_msg = f"Perplexity API call failed with status {response.status_code}"
                            if response.text:
                                error_msg += f": {response.text}"
                            self.logger.warning(f"⚠️ {error_msg}")
                            # Continue without research results
                    except requests.exceptions.RequestException as e:
                        self.logger.warning(f"⚠️ Perplexity API request failed: {str(e)}")
                        # Continue without research results
            
            # Save updated content with UTF-8 encoding
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            self.logger.error(f"Error saving objective to {filepath}: {str(e)}")
            raise
