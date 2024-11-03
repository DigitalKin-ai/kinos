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
            self.logger("Début de l'analyse...")
            
            context = {
                "evaluation": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger("Modifications détectées, tentative de mise à jour...")
                temp_content = self.current_content

                # Validation du format des évaluations
                section_pattern = r'\[section: (.+?)\]\n\[evaluation: (VALIDATED|NEEDS_WORK|REJECTED)\]\n\[details: (.+?)\]'
                criteria_pattern = r'- (\w+): \[(✓|⚠️|❌)\] (.+)$'
                
                # Extraire et valider les évaluations
                evaluations_section = re.search(r'# Évaluations en Cours\n(.*?)(?=\n#|$)', response, re.DOTALL)
                if evaluations_section:
                    sections = re.finditer(section_pattern, evaluations_section.group(1), re.MULTILINE | re.DOTALL)
                    valid_evaluations = []
                    
                    for section in sections:
                        section_name = section.group(1)
                        evaluation = section.group(2)
                        details = section.group(3)
                        
                        # Extraire les critères
                        criteria = re.finditer(criteria_pattern, details, re.MULTILINE)
                        criteria_list = []
                        for criterion in criteria:
                            name = criterion.group(1)
                            status = criterion.group(2)
                            justification = criterion.group(3)
                            criteria_list.append(f"- {name}: [{status}] {justification}")
                        
                        # Construire l'évaluation formatée
                        valid_evaluations.append(
                            f"[section: {section_name}]\n"
                            f"[evaluation: {evaluation}]\n"
                            f"[details: {details}]\n"
                            f"{chr(10).join(criteria_list)}"
                        )
                    
                    # Mettre à jour la section des évaluations
                    if valid_evaluations:
                        result = SearchReplace.section_replace(
                            temp_content,
                            "Évaluations en Cours",
                            '\n\n'.join(valid_evaluations)
                        )
                        if result.success:
                            temp_content = result.new_content
                            self.logger("✓ Évaluations mises à jour")

                # Validation et mise à jour de la vue d'ensemble
                overview_pattern = (
                    r'\[progression: (\d+)%\]\n'
                    r'\[status: (IN_PROGRESS|COMPLETED|BLOCKED)\]\n'
                    r'\[critical_issues: (.+?)\]\n'
                    r'\[next_steps: (.+?)\]'
                )
                
                overview_section = re.search(r'# Vue d\'Ensemble\n(.*?)(?=\n#|$)', response, re.DOTALL)
                if overview_section and re.search(overview_pattern, overview_section.group(1), re.DOTALL):
                    result = SearchReplace.section_replace(
                        temp_content,
                        "Vue d'Ensemble",
                        overview_section.group(1).strip()
                    )
                    if result.success:
                        temp_content = result.new_content
                        self.logger("✓ Vue d'ensemble mise à jour")

                self.new_content = temp_content
                self.logger("✓ Mise à jour complète effectuée")
            else:
                self.logger("Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def _get_llm_response(self, context: dict) -> str:
        """
        Get LLM response for quality evaluation.
        
        Process:
        1. Analyzes content against quality criteria
        2. Identifies issues and improvements
        3. Generates detailed evaluation report
        4. Validates evaluation format
        
        Args:
            context: Current content and specifications
            
        Returns:
            str: Validated evaluation report
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
