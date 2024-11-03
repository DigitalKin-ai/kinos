"""
ManagementAgent - Agent responsible for project coordination and planning
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
import time
from datetime import datetime
import openai

class ManagementAgent(ParallagonAgent):
    """Agent handling project coordination and task management"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)

    def determine_actions(self) -> None:
        """Analyze project status and coordinate tasks between agents"""
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "management": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, tentative de mise à jour...")
                temp_content = self.current_content
                sections = ["Consignes Actuelles", "TodoList", "Actions Réalisées"]
                
                for section in sections:
                    pattern = f"# {section}\n(.*?)(?=\n#|$)"
                    match = re.search(pattern, response, re.DOTALL)
                    if not match:
                        self.logger(f"[{self.__class__.__name__}] ❌ Section '{section}' non trouvée dans la réponse LLM")
                        continue
                        
                    new_section_content = match.group(1).strip()
                    result = SearchReplace.section_replace(
                        temp_content,
                        section,
                        new_section_content
                    )
                    
                    if result.success:
                        temp_content = result.new_content
                        self.logger(f"[{self.__class__.__name__}] ✓ Section '{section}' mise à jour avec succès")
                    else:
                        self.logger(f"[{self.__class__.__name__}] ❌ Échec de la mise à jour de la section '{section}': {result.message}")
                
                self.new_content = temp_content
                self.logger(f"[{self.__class__.__name__}] ✓ Mise à jour complète effectuée")
            else:
                self.logger(f"[{self.__class__.__name__}] Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for management decisions"""
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            print(f"[{self.__class__.__name__}] LLM response received")  # Debug log
            time.sleep(10)  # Pause de 10 secondes
            return response.choices[0].message.content
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")  # Error log
            import traceback
            print(traceback.format_exc())
            return context['management']

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a specific section"""
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            print(f"[{self.__class__.__name__}] Section '{section_name}' not found")
            return ""
        elif len(matches) > 1:
            print(f"[{self.__class__.__name__}] Warning: Multiple '{section_name}' sections found, using first one")
            
        return matches[0].group(1).strip()

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)

    def _build_prompt(self, context: dict) -> str:
        """Build prompt for management decisions"""
        return f"""You are the Management Agent in the Parallagon framework. Your role is to analyze the current production and provide SPECIFIC, ACTIONABLE directives.

Current management content:
{context['management']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. READ CAREFULLY the current production.md content
2. Compare it with specifications.md requirements
3. Consider evaluation.md feedback
4. Identify SPECIFIC gaps and improvements needed
5. Provide DETAILED, CONCRETE directives

Important - Your response must follow this exact structure:

# Consignes Actuelles
[SPECIFIC directives for the Production Agent, including:
- Exact sections to improve/create
- Precise content elements to add
- Specific quality improvements needed
- Clear formatting requirements
Example:
1. Add a detailed "Impact Économique" section under "Corps Principal" with:
   - Analysis of revenue models disruption
   - Specific examples of AI music monetization
   - Data on market size and growth projections
2. Expand the "Technologies Clés" section with:
   - Technical details of current AI music models
   - Specific capabilities and limitations
   - Concrete examples of applications]

# Top Priorité
🔥 [ONE specific, high-impact task from the directives above]
- Section: [Exact section name]
- Action: [Precise action required]
- Details: [Specific elements to include]
- Success criteria: [How to validate completion]

# TodoList
[Ordered list of remaining tasks, from highest to lowest priority]
- [ ] Specific task 1 with clear deliverable
- [ ] Specific task 2 with clear deliverable
[etc.]

# Actions Réalisées
- [Timestamp] Specific completed action
[etc.]

Guidelines:
- Always READ the current production.md before giving directives
- Give CONCRETE, ACTIONABLE instructions
- Specify EXACT sections and content needed
- Include CLEAR quality criteria
- Prioritize based on evaluation feedback
- Track progress with timestamps
- FOCUS ON ONE SECTION AT A TIME - do not try to fix everything at once
- Instruct to write in complete, well-structured sentences
- Avoid bullet points in the content - use proper paragraphs instead

Production Rules to Enforce:
1. Focus on ONE section at a time - complete it fully before moving to the next
2. Write in complete, grammatically correct sentences
3. Use paragraphs to develop ideas, not bullet points
4. Ensure each paragraph flows logically to the next
5. Only move to a new section once the current one is complete and validated

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content."""
