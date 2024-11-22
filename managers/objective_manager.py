import os
import requests
from utils.logger import Logger
from utils.encoding_utils import EncodingUtils
from utils.fs_utils import FSUtils
import openai
from dotenv import load_dotenv

class ObjectiveManager:
    """Manager class for generating agent-specific objectives."""
    
    def __init__(self):
        self.logger = Logger()
        self.encoding_utils = EncodingUtils()
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")

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
            summary = self._generate_summary(objective, agent_name)
            self.logger.success(summary)
        
            # Save objective
            output_path = f".aider.objective.{agent_name}.md"
            self._save_objective(output_path, objective)
        
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
        try:
            # First try UTF-8
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try to convert the file
            self._convert_to_utf8(filepath)
            # Try reading again with UTF-8
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

    def _generate_objective_content(self, mission_content, agent_content, agent_name):
        """Generate objective content using GPT."""
        try:
            client = openai.OpenAI()

            # Generate complete tree structure
            fs_utils = FSUtils()
            root_files = fs_utils.get_folder_files(".")
            root_subfolders = fs_utils.get_subfolders(".")
            tree_structure = fs_utils.build_tree_structure(
                current_path=".",
                files=root_files,
                subfolders=root_subfolders,
                max_depth=None  # No depth limit to get full tree
            )
            tree_text = "\n".join(tree_structure)

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

            # Read and encode diagram.svg if it exists
            diagram_content = None
            if os.path.exists('./diagram.svg'):
                try:
                    with open('./diagram.svg', 'rb') as f:
                        diagram_content = f.read()
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read diagram.svg: {str(e)}")

            # Check for Perplexity API key
            perplexity_key = os.getenv('PERPLEXITY_API_KEY')
            if perplexity_key:
                search_instruction = """

4. **Search**
   - If research needed, add "Search:" line with query"""
            else:
                search_instruction = ""

            prompt = f"""
Based on the following, generate a clear specific next step for the {agent_name} agent.

# Mission
````
{mission_content}
````

# Project Structure
````
{tree_text}
````
(In the image attached is a visualization of the repository, showing file sizes and structure, that you can use to enhance your decision-making)

# Recent Activity (last 80 lines)
````
{suivi_content}
````

# Todolist
````
{todolist}
````

Required Output
================
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
            self.logger.info(f"OBJECTIVE PROMPT: {prompt}")

            messages = [
                {"role": "system", "content": """
{agent_content}
                     
# Planning
Your planning:
1. Prioritizes explicit mission instructions
2. Does not repeats previous actions, or work done by the other agents
3. Maintains clear progression
"""}
            ]

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
                                    "url": f"data:image/svg+xml;base64,{encoded_bytes}"
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
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"GPT API call failed: {str(e)}")
            raise

    def _generate_summary(self, objective, agent_name):
        """Generate a one-line summary of the objective."""
        try:
            # Read last 50 lines from suivi.md if it exists
            suivi_content = ""
            if os.path.exists('suivi.md'):
                try:
                    with open('suivi.md', 'r', encoding='utf-8') as f:
                        # Read all lines and get last 50
                        lines = f.readlines()
                        last_50_lines = lines[-50:] if len(lines) > 50 else lines
                        suivi_content = ''.join(last_50_lines)
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read suivi.md: {str(e)}")
                    # Continue without suivi content

            client = openai.OpenAI()
            prompt = f"""
# Logs de suivi précédents (50 dernières lignes)
````
{suivi_content}
````

# Objectif
````
{objective}
````

A partir de l'Objectif, résume en une seule phrase ce que l'agent fait maintenant dans le cadre de la mission, en suivant strictement ce format :
"L'agent {agent_name} [action] [objectif] [détail optionnel] [fichiers modifiés]"

Consignes :
- Ne répète pas la mission (qui est connue de l'utilisateur), mais seulement ce que l'agent fait précisément dans le cadre de celle-ci
- Ne répète pas les informations déjà présentes dans les logs de suivi
- Utilise des emojis appropriés en fonction du type d'action

Réponds uniquement avec la phrase formatée, rien d'autre.
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui résume des actions au sein d'un projet en une phrase concise avec des emojis appropriés. Ces résumés serviront de logs de suivi au sein de la mission."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {str(e)}")
            # Return a basic fallback summary
            return f"L'agent {agent_name} 🤖 va exécuter une nouvelle tâche"

    def _generate_research_summary(self, query, result, agent_name):
        """Generate a summary of the Perplexity research results."""
        try:
            client = openai.OpenAI()
            prompt = f"""
Résume en une seule phrase ce qui a été trouvé par la recherche Perplexity, en suivant ce format:
"L'agent {agent_name} effectue une recherche sur [sujet] : [résumé des découvertes principales]"

Query de recherche : {query}

Résultats complets :
{result}

Réponds uniquement avec la phrase formatée, rien d'autre.
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui résume des résultats de recherche de manière concise. Ces résumés seront utilisés pour des logs de suivi de projet."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate research summary: {str(e)}")
            # Return a basic fallback summary with agent name
            return f"L'agent {agent_name} 🤖 a recherché sur : {query}"


    def _save_objective(self, filepath, content):
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
                            research_summary = self._generate_research_summary(research_query, research_result, agent_name)
                            self.logger.success(research_summary)
                            
                            # Add research results to objective
                            content += "\n\n## Informations complémentaires\n"
                            content += f"Résultats de la recherche Perplexity pour : {research_query}\n\n"
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
