"""
EvaluationAgent - Agent responsible for quality control and validation.

Key responsibilities:
- Evaluates content quality and completeness
- Validates compliance with specifications
- Provides detailed feedback and recommendations
- Tracks overall project quality status

Workflow:
1. Reviews content against specifications
2. Performs quality checks and validations
3. Generates detailed evaluation reports
4. Updates quality status and metrics
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
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "evaluation": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            if response and response != self.current_content:
                # Écrire directement dans le fichier
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(response)
                self.current_content = response
                self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response with standardized error handling"""
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modèle standardisé pour tous les agents
                messages=[{
                    "role": "user",
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            self.logger(f"[{self.__class__.__name__}] LLM response received")
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return context.get(self.__class__.__name__.lower().replace('agent', ''), '')

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract content of a specific evaluation section.
        
        Used for:
        - Accessing current evaluations
        - Retrieving quality metrics
        - Tracking evaluation history
        
        Args:
            content: Full evaluation content
            section_name: Name of section to extract
            
        Returns:
            str: Content of specified section
        """
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            print(f"[{self.__class__.__name__}] Section '{section_name}' not found")
            return ""
        elif len(matches) > 1:
            print(f"[{self.__class__.__name__}] Warning: Multiple '{section_name}' sections found, using first one")
            
        return matches[0].group(1).strip()

    def _update_status(self, new_content: str) -> None:
        """
        Update evaluation status based on findings.
        
        Updates:
        - Overall quality status
        - Section-specific ratings
        - Completion metrics
        - Critical issues flags
        
        Args:
            new_content: Updated evaluation content
        """
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
        """
        Format other files content for evaluation context.
        
        Organizes:
        - Content to evaluate
        - Quality requirements
        - Previous evaluations
        - Related feedback
        
        Args:
            files: Dictionary of file contents
            
        Returns:
            str: Formatted context for evaluation
        """
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)

    def _build_prompt(self, context: dict) -> str:
        """
        Build prompt for quality evaluation.
        
        Includes:
        - Quality criteria and standards
        - Content requirements
        - Evaluation metrics
        - Feedback guidelines
        - Rating system
        
        Args:
            context: Current project state
            
        Returns:
            str: Quality evaluation prompt
        """
        return f"""En tant qu'évaluateur qualité, vous devez analyser chaque section et produire une évaluation structurée.

Contexte actuel :
{self._format_other_files(context)}

Format STRICT à respecter pour chaque section :

# Évaluations en Cours
[section: Nom Section]
[evaluation: VALIDATED|NEEDS_WORK|REJECTED]
[details: description détaillée]
- Cohérence: [✓|⚠️|❌] justification
- Complétude: [✓|⚠️|❌] justification
- Clarté: [✓|⚠️|❌] justification
- Respect des critères: [✓|⚠️|❌] justification

# Vue d'Ensemble
[progression: pourcentage]
[status: IN_PROGRESS|COMPLETED|BLOCKED]
[critical_issues: liste des problèmes majeurs]
[next_steps: actions prioritaires]

Règles STRICTES de formatage :
1. L'attribut [evaluation:] doit être un des trois états : VALIDATED, NEEDS_WORK, REJECTED
2. Les indicateurs de statut doivent être exactement : ✓, ⚠️, ou ❌
3. Chaque section doit avoir tous les attributs et critères listés
4. La progression doit être un pourcentage entre 0 et 100
5. Le status global doit être un des trois états définis"""
