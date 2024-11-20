import os
import requests
import fnmatch
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

    def _convert_to_utf8(self, filepath):
        """
        Convert a file to UTF-8 encoding.
        
        Args:
            filepath (str): Path to file to convert
            
        Returns:
            bool: True if conversion was successful
            
        Raises:
            Exception: If file cannot be converted
        """
        try:
            # First try to detect current encoding
            import chardet
            with open(filepath, 'rb') as f:
                raw = f.read()
            detected = chardet.detect(raw)
            
            if detected['encoding']:
                self.logger.info(f"🔍 Detected {filepath} encoding as: {detected['encoding']} (confidence: {detected['confidence']})")
                
                # Read with detected encoding
                content = raw.decode(detected['encoding'])
                
                # Write back in UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.logger.success(f"✨ Converted {filepath} to UTF-8")
                return True
                
            else:
                # If detection failed, try common encodings
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        content = raw.decode(encoding)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.logger.success(f"✨ Converted {filepath} from {encoding} to UTF-8")
                        return True
                    except UnicodeDecodeError:
                        continue
                        
                raise ValueError(f"Could not detect or convert encoding for {filepath}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to convert {filepath} to UTF-8: {str(e)}")
            raise

    def convert_all_to_utf8(self):
        """Convert all text files in the project to UTF-8."""
        try:
            # Get ignore patterns
            ignore_patterns = ['.git*', '.aider*', '__pycache__', '*.pyc']
            
            # Track conversion results
            results = {
                'converted': [],
                'failed': [],
                'skipped': []
            }
            
            # Process all files
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt', '.py')):  # Add other extensions as needed
                        filepath = os.path.join(root, file)
                        
                        # Skip ignored files
                        if any(fnmatch.fnmatch(filepath, pattern) for pattern in ignore_patterns):
                            results['skipped'].append(filepath)
                            continue
                            
                        try:
                            # Check if already UTF-8
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    f.read()
                                self.logger.debug(f"✅ {filepath} is already UTF-8")
                                continue
                            except UnicodeDecodeError:
                                # Not UTF-8, convert it
                                if self._convert_to_utf8(filepath):
                                    results['converted'].append(filepath)
                        except Exception as e:
                            self.logger.error(f"❌ Failed to process {filepath}: {str(e)}")
                            results['failed'].append((filepath, str(e)))
            
            # Log summary
            self.logger.success(
                f"\n📊 Conversion Summary:\n"
                f"   - Converted: {len(results['converted'])} files\n"
                f"   - Failed: {len(results['failed'])} files\n"
                f"   - Skipped: {len(results['skipped'])} files"
            )
            
            if results['failed']:
                self.logger.warning("\n⚠️ Failed conversions:")
                for filepath, error in results['failed']:
                    self.logger.warning(f"   - {filepath}: {error}")
                    
            return results
            
        except Exception as e:
            self.logger.error(f"❌ UTF-8 conversion failed: {str(e)}")
            raise

    def _read_file(self, filepath):
        """Read content from file with robust encoding handling."""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']  # Ajout de iso-8859-1
        
        # Log attempt to read file
        self.logger.debug(f"🔍 Attempting to read {filepath}")
        
        # First try to detect encoding
        try:
            import chardet
            with open(filepath, 'rb') as f:
                raw = f.read()
            detected = chardet.detect(raw)
            if detected['encoding']:
                encodings.insert(0, detected['encoding'])
                self.logger.debug(f"📝 Detected encoding: {detected['encoding']} (confidence: {detected['confidence']})")
        except ImportError:
            self.logger.debug("⚠️ chardet not available for encoding detection")
        except Exception as e:
            self.logger.debug(f"⚠️ Error during encoding detection: {str(e)}")

        # Try each encoding
        last_error = None
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                    self.logger.debug(f"✅ Successfully read file using {encoding} encoding")
                    return content
            except UnicodeDecodeError as e:
                last_error = e
                self.logger.debug(f"⚠️ Failed to read with {encoding}: {str(e)}")
                continue
            except Exception as e:
                self.logger.error(f"❌ Unexpected error reading {filepath}: {str(e)}")
                raise

        # If we get here, none of the encodings worked
        error_msg = (
            f"Failed to read {filepath} with encodings: {', '.join(encodings)}\n"
            f"Last error: {str(last_error)}"
        )
        self.logger.error(f"❌ {error_msg}")
        raise UnicodeDecodeError(
            'utf-8',  # codec name
            b'',      # object
            0,        # start
            1,        # end
            error_msg # reason
        )

    def _generate_objective_content(self, mission_content, agent_content, agent_name):
        """Generate objective content using GPT."""
        try:
            client = openai.OpenAI()

            # Load global map content if it exists
            global_map_content = ""
            if os.path.exists("map.md"):
                try:
                    global_map_content = self._read_file("map.md")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read global map: {str(e)}")
                    # Continue without global map content

            # Load todolist if it exists
            todolist = ""
            if os.path.exists("todolist.md"):
                try:
                    todolist = self._read_file("todolist.md")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not read todolist: {str(e)}")
                    # Continue without todolist

             # Read last 80 lines from suivi.md if it exists
            suivi_content = ""
            if os.path.exists('suivi.md'):
                try:
                    with open('suivi.md', 'r', encoding='latin-1') as f:  # Use latin-1 for suivi.md
                        # Read all lines and get last
                        lines = f.readlines()
                        last_lines = lines[-80:] if len(lines) > 80 else lines
                        suivi_content = ''.join(last_lines)
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

# Current Project Map
````
{global_map_content}
````

# Logs de suivi (travail de tous les agents - 80 dernières lignes)
````
{suivi_content}
````

# Todolist
````
{todolist}
````

# Breadth-First Pattern
- Review the directives in the Mission if present
- Review the uncompleted items in the todolist
- Review the directives of your system prompt
- Review the work already being done by the other agents
- Then: Choose an item from the todolist (Maintain breadth-first exploration pattern)
- Generate an item from your system prompt, according to your specific role in the project

Required Output
================
Create two objectives in markdown format - one for production, one specific to your role. Each objective should specify:

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

Ask Aider to make the edits now, without asking for clarification.
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

    def _convert_to_utf8(self, filepath):
        """Convert a file to UTF-8 encoding."""
        try:
            # First try to detect current encoding
            import chardet
            with open(filepath, 'rb') as f:
                raw = f.read()
            detected = chardet.detect(raw)
            
            if detected['encoding']:
                self.logger.info(f"🔍 Detected {filepath} encoding as: {detected['encoding']} (confidence: {detected['confidence']})")
                
                # Read with detected encoding
                content = raw.decode(detected['encoding'])
                
                # Write back in UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.logger.success(f"✨ Converted {filepath} to UTF-8")
                
            else:
                # If detection failed, try common encodings
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        content = raw.decode(encoding)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.logger.success(f"✨ Converted {filepath} from {encoding} to UTF-8")
                        return
                    except UnicodeDecodeError:
                        continue
                        
                raise ValueError(f"Could not detect or convert encoding for {filepath}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to convert {filepath} to UTF-8: {str(e)}")
            raise

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
