"""
EvaluationAgent - Agent responsible for quality control and validation
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
from datetime import datetime
import openai

class EvaluationAgent(ParallagonAgent):
    """Agent handling quality control and validation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])

    def determine_actions(self) -> None:
        """Analyze current context and determine if validation/evaluation is needed."""
        context = {
            "evaluation": self.current_content,
            "other_files": self.other_files
        }
        
        response = self._get_llm_response(context)
        
        if response != self.current_content:
            temp_content = self.current_content
            sections = ["Évaluations en Cours", "Vue d'Ensemble"]
            
            for section in sections:
                pattern = f"# {section}\n(.*?)(?=\n#|$)"
                match = re.search(pattern, response, re.DOTALL)
                if not match:
                    print(f"[{self.__class__.__name__}] {section} section not found in LLM response")
                    continue
                    
                new_section_content = match.group(1).strip()
                result = SearchReplace.section_replace(
                    temp_content,
                    section,
                    new_section_content
                )
                if result.success:
                    temp_content = result.new_content
                    
            self.new_content = temp_content

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for evaluation tasks"""
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            response = self.client.chat.completions.create(
                model="gpt-4",
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
        """Build prompt for evaluation decisions"""
        return f"""You are the Evaluation Agent in the Parallagon framework, working in parallel with 3 other agents:
- Management Agent: coordinates overall progress
- Specifications Agent: defines the criteria you use for evaluation
- Production Agent: creates the content you must evaluate

Your role is to be an extremely thorough and critical quality controller. You must scrutinize every aspect of the production with meticulous attention to detail.

Current evaluation content:
{context['evaluation']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Conduct a rigorous evaluation of all outputs against specifications by:
   - Checking every single requirement point by point
   - Verifying exact compliance with format specifications
   - Scrutinizing writing quality (clarity, coherence, precision)
   - Validating all technical claims and examples
   - Ensuring proper citation and attribution where needed
   - Checking for logical consistency throughout the document
   - Verifying accuracy of all facts and figures
   - Assessing the depth and thoroughness of analysis

2. Identify and document:
   - Even minor deviations from requirements
   - Potential logical flaws or weak arguments
   - Missing or incomplete elements
   - Inconsistencies in terminology or style
   - Areas needing more detailed explanation
   - Questionable assumptions or claims
   - Format or structure issues
   - Quality gaps versus best practices

3. Provide specific, actionable feedback:
   - Exact location of each issue
   - Detailed explanation of the problem
   - Concrete suggestions for improvement
   - Priority level for each correction needed

Important:
- Return ONLY the markdown content with exactly these 2 sections:

# Évaluations en Cours
[Detailed point-by-point evaluation status]
- Format Compliance: [Status] [Details]
- Content Requirements: [Status] [Details]
- Technical Accuracy: [Status] [Details]
- Logical Consistency: [Status] [Details]
- Writing Quality: [Status] [Details]
- Documentation: [Status] [Details]
[Include specific issues and recommendations for each category]

# Vue d'Ensemble
[Critical overview of current state]
- Overall Quality Assessment
- Major Issues Requiring Attention
- Minor Issues to Address
- Specific Recommendations
- Progress Tracking
- Quality Metrics
- Risk Areas
- Improvement Priorities

Remember:
- Be extremely detail-oriented
- Accept nothing less than excellence
- Question everything
- Provide evidence for all assessments
- Be constructive but uncompromising
- Focus on precision and accuracy
- Maintain high quality standards

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content."""
