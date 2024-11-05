"""
LLMService - Handles LLM interactions for change summaries
"""
from typing import Dict
import openai
import time

class LLMService:
    """Service for handling LLM interactions"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def get_changes_summary(self, changes: Dict[str, Dict[str, str]]) -> str:
        """Generate a summary of changes using LLM with better error handling"""
        try:
            # Prepare context with better formatting
            context_parts = []
            for panel, content in changes.items():
                old_snippet = self._truncate_text(content["old"], 200)
                new_snippet = self._truncate_text(content["new"], 200)
                context_parts.append(
                    f"\nDans {panel}:\n"
                    f"Ancien: {old_snippet}\n"
                    f"Nouveau: {new_snippet}\n"
                )
            
            context = "Changements détectés:" + "".join(context_parts)
            prompt = self._build_summary_prompt(context)

            response = self._make_api_call(prompt)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return self._build_fallback_summary(changes)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis if needed"""
        return text[:max_length] + "..." if len(text) > max_length else text

    def _build_summary_prompt(self, context: str) -> str:
        """Build a standardized prompt for change summaries"""
        return f"""{context}
Résumez en une phrase précise ce qui a changé. Soyez factuel et concis."""

    def _make_api_call(self, prompt: str):
        """Make API call with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Modèle standard de openai (ne pas remplacer)
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=100
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (attempt + 1))

    def _build_fallback_summary(self, changes: Dict[str, Dict[str, str]]) -> str:
        """Build a basic summary when LLM fails"""
        return f"Mise à jour : {', '.join(changes.keys())}"
