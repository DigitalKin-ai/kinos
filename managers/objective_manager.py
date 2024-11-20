import os
import requests
from utils.logger import Logger
import openai
from dotenv import load_dotenv

class ObjectiveManager:
    """Manager class for generating agent-specific objectives."""
    
    def __init__(self):
        self.logger = Logger()
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
            self.logger.info(f"🎯 Generating objective for agent: {agent_filepath}")
            
            # Validate input files
            if not all(self._validate_file(f) for f in [mission_filepath, agent_filepath]):
                raise ValueError("Invalid or missing input files")
                
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
        """Read content from file with fallback encoding support."""
        encodings = ['utf-8', 'latin-1', 'cp1252']  # Common encodings for French text
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content
            except UnicodeDecodeError:
                continue  # Try next encoding
            except Exception as e:
                self.logger.error(f"Error reading file {filepath}: {str(e)}")
                raise
                
        # If we get here, none of the encodings worked
        raise UnicodeDecodeError(
            f"Failed to read {filepath} with any of these encodings: {', '.join(encodings)}"
        )

    def _generate_objective_content(self, mission_content, agent_content, agent_name):
        """Generate objective content using GPT."""
        try:
            client = openai.OpenAI()
            
            # Load recent chat history from both history files
            chat_history = ""
            history_files = [
                f".aider.history.{agent_name}.md",
                f".aider.input.{agent_name}.md"
            ]
            
            for history_file in history_files:
                try:
                    if os.path.exists(history_file):
                        with open(history_file, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                            # Get last 5000 chars from each history file
                            chat_history += content[-5000:] if len(content) > 5000 else content
                            chat_history += "\n\n"
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not load chat history from {history_file}: {str(e)}")
                    continue  # Try next file
            
            if not chat_history:
                self.logger.debug(f"No chat history found for agent {agent_name}")
                chat_history = "No previous chat history available."

            # Load global map content if it exists
            global_map_content = ""
            if os.path.exists("map.md"):
                try:
                    with open("map.md", 'r', encoding='utf-8') as f:
                        global_map_content = f.read()
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read global map: {str(e)}")
                    # Continue without global map content

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

            prompt = f"""
Based on the following contexts, generate a clear specific next step for the {agent_name} agent.

Reference Materials
================
# Mission
````
{mission_content}
````

# Global Project Map
````
{global_map_content}
````

# Logs de suivi (travail de tous les agents - 50 dernières lignes)
````
{suivi_content}
````

# Recent Chat History (agent {agent_name} & aider)
````
{chat_history}
````

# Breadth-First Pattern
- Follow the directives in the Mission if present
- Review previous steps from chat history
- Review the work being done by other agents
- Generate a step that explores a NEW aspect of the mission
- Avoid repeating or deepening previous work
- Focus on unexplored areas of responsibility
- Maintain breadth-first exploration pattern

Required Output
================
Create an objective in markdown format that specifies:

1. **Action Statement**
   - Single, specific task to accomplish
   - Clear relation to current mission state
   - Within agent's documented capabilities

2. **Source Files**
   - Which specific files to analyze (use global map for context)
   - Which sections are relevant
   - Which dependencies matter

3. **Target Changes**
   - Which files to modify
   - Nature of expected changes
   - Impact on system state

4. **Validation Points**
   - How to verify success
   - What output to check
   - Which states to validate

5. **Operation Bounds**
   - Resource limitations
   - Scope restrictions
   - Dependency requirements

6. **Search**
   - If the task requires a search on Perplexity, add a "Search:" line with the specific search to be performed
   - Do not include this line if no research is necessary

The objective must be:
- Limited to one clear operation
- Executable with current capabilities
- Specific about file changes based on global map
- Clear on completion checks
- Self-contained (no follow-up needed)
- Different from previous objectives

Ask Aider to make the edits now, without asking for clarification, and using the required SEARCH/REPLACE format.
"""
            self.logger.info(f"OBJECTIVE PROMPT: {prompt}")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
{agent_content}
                     
# Planning
Your planning:
1. Prioritizes explicit mission instructions
2. Does not repeats previous actions, or work done by the other agents
3. Maintains clear progression
"""},
                    {"role": "user", "content": prompt}
                ],
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
