"""
EvaluationAgent - Agent responsible for quality control and validation
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
import time
from datetime import datetime
import openai

class EvaluationAgent(ParallagonAgent):
    """Agent handling quality control and validation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)

    def determine_actions(self) -> None:
        """
        Analyze project status and coordinate tasks between agents.
        
        Process:
        1. Reviews current project state and progress
        2. Identifies blockers and dependencies
        3. Prioritizes tasks across sections
        4. Updates management directives
        5. Coordinates agent activities
        """
        try:
            self.logger("Début de l'analyse...")
            
            context = {
                "evaluation": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger("Modifications détectées, tentative de mise à jour...")
                temp_content = self.current_content
                sections = ["Évaluations en Cours", "Vue d'Ensemble"]
                
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
        """
        Get LLM response for management decisions.
        
        Process:
        1. Analyzes project context and agent status
        2. Determines optimal task distribution
        3. Generates coordinated action plans
        4. Validates response format
        
        Args:
            context: Current project state and agent status
            
        Returns:
            str: Validated management directives
        """
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
            return response.choices[0].message.content
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")  # Error log
            import traceback
            print(traceback.format_exc())
            return context['evaluation']

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

    def _update_status(self, new_content: str) -> None:
        """Update status if changed"""
        old_status_match = re.search(r'\[status: (\w+)\]', self.current_content)
        new_status_match = re.search(r'\[status: (\w+)\]', new_content)
        
        if (old_status_match and new_status_match and 
            old_status_match.group(1) != new_status_match.group(1)):
            result = SearchReplace.exact_replace(
                self.current_content,
                f"[status: {old_status_match.group(1)}]",
                f"[status: {new_status_match.group(1)}]"
            )
            if result.success:
                self.current_content = result.new_content

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)

    def _build_prompt(self, context: dict) -> str:
        """
        Build prompt for management coordination.
        
        Includes:
        - Current project status
        - Agent activities and needs
        - Task priorities and dependencies
        - Coordination requirements
        - Resource allocation guidance
        
        Args:
            context: Current project state
            
        Returns:
            str: Management coordination prompt
        """
        return f"""You are the Evaluation Agent in the Parallagon framework, working in parallel with 3 other agents.

Your role is to be an extremely thorough and critical quality controller. You must evaluate ONLY the content present in production.md - this is the COMPLETE deliverable to evaluate. Any element not present in production.md should be considered missing, regardless of mentions in other files.

Requirements to evaluate against (from specifications.md):
{context['other_files'].get('specifications.md', '')}

Content to evaluate (COMPLETE deliverable from production.md):
{context['other_files'].get('production.md', '')}

Your task:
1. Evaluate ONLY the actual content in production.md against the specifications by:
   - Checking every requirement point by point
   - Marking as MISSING any required element not explicitly present in production.md
   - Scrutinizing only the text and elements that are actually there
   - Evaluating the quality of what exists, not what should exist
   - Identifying gaps between what's required and what's delivered

2. Document precisely:
   - Missing required elements (anything not in production.md)
   - Quality issues in existing content
   - Format/structure deviations
   - Incomplete sections
   - Weak or unsupported arguments
   - Technical inaccuracies
   - Writing quality issues
   - Logic flaws

3. Provide specific feedback:
   - Exact quotes from production.md when discussing issues
   - Clear identification of missing elements
   - Detailed explanation of each problem
   - Concrete improvement suggestions
   - Priority level for corrections

Important:
- Return ONLY the markdown content with exactly these 2 sections:

# Évaluations en Cours
[Detailed evaluation of ONLY what exists in production.md]
- Format Compliance: [Status] [Details with exact quotes]
- Content Completeness: [Status] [List of missing elements]
- Technical Accuracy: [Status] [Issues in existing content]
- Logical Consistency: [Status] [Problems in argumentation]
- Writing Quality: [Status] [Style and clarity issues]
- Documentation: [Status] [Citation and support issues]

# Vue d'Ensemble
[Critical overview based ONLY on production.md content]
- Overall Assessment (of what exists)
- Major Gaps (required vs delivered)
- Quality Issues (in existing content)
- Missing Elements (not in production.md)
- Specific Recommendations
- Completion Status
- Critical Issues
- Priority Actions

Remember:
- Evaluate ONLY what is actually in production.md
- Consider anything not in production.md as missing
- Be extremely critical and detailed
- Quote exact text when discussing issues
- Focus on concrete evidence from the deliverable
- Accept nothing less than excellence

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content."""
