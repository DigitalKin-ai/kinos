"""
LLMService - Handles LLM interactions for change summaries
"""
from typing import Dict
import openai

class LLMService:
    """Service for handling LLM interactions"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def get_changes_summary(self, changes: Dict[str, Dict[str, str]]) -> str:
        """Generate a summary of changes using LLM"""
        try:
            # Prepare context
            context = "Changements détectés:\n"
            for panel, content in changes.items():
                context += f"\nDans {panel}:\n"
                old_snippet = content["old"][:200] + "..." if len(content["old"]) > 200 else content["old"]
                new_snippet = content["new"][:200] + "..." if len(content["new"]) > 200 else content["new"]
                context += f"Ancien: {old_snippet}\nNouveau: {new_snippet}\n"

            prompt = f"""{context}

Résumez en une phrase précise ce qui a changé. Soyez factuel et concis."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Mise à jour : {', '.join(changes.keys())}"
