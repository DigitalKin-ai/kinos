"""
ProductionAgent - Agent responsible for content creation and implementation.

Key responsibilities:
- Creates and updates content based on specifications
- Implements changes requested by management
- Maintains content quality and consistency 
- Responds to evaluation feedback

Workflow:
1. Monitors specifications and management directives
2. Creates/updates content sections as needed
3. Validates content against requirements
4. Maintains document structure integrity
"""
import os
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import anthropic
import openai
import re
from datetime import datetime
from functools import wraps

from functools import wraps

def error_handler(func):
    """Decorator for handling errors in agent methods"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Error: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return args[0].get('production', '') if args else ''
    return wrapper

class ProductionAgent(ParallagonAgent):
    """Agent handling code production and implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        # Verify OpenAI API key is present and valid
        if not config.get("openai_api_key") or config["openai_api_key"] == "your-api-key-here":
            raise ValueError("OpenAI API key invalide dans la configuration")
        
        # Initialize OpenAI client with config key
        self.openai_client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)

        # S'assurer que le chemin est absolu et que le dossier existe
        if not os.path.isabs(config["file_path"]):
            config["file_path"] = os.path.abspath(config["file_path"])
        self.file_path = config["file_path"]
        
        # Créer le dossier parent si nécessaire
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # Convertir tous les watch_files en chemins absolus
        if "watch_files" in config:
            self.watch_files = [
                os.path.abspath(f) if not os.path.isabs(f) else f
                for f in config["watch_files"]
            ]
            
        # Log initial pour debug
        self.logger(f"[{self.__class__.__name__}] Initialisé avec:")
        self.logger(f"- Fichier principal: {self.file_path}")
        self.logger(f"- Fichiers surveillés: {self.watch_files}")

        # S'assurer que le chemin est absolu
        self.file_path = os.path.abspath(config["file_path"])
        self.logger(f"[{self.__class__.__name__}] Initialisé avec fichier: {self.file_path}")

    def _needs_update(self, section_name: str) -> bool:
        """Check if a section needs updating"""
        try:
            with open("production.md", 'r', encoding='utf-8') as f:
                content = f.read()
                
            pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                return True
                
            section_content = match.group(1).strip()
            return section_content == "" or section_content == "[En attente de contenu]"
            
        except Exception:
            return True
            
    def _generate_content(self, section_name: str, constraints: str) -> str:
        """Generate new content for a section"""
        try:
            context = {
                "section_name": section_name,
                "constraints": constraints,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            if response and response.strip():
                return response.strip()
                
            return "[En attente de contenu]"
            
        except Exception as e:
            self.logger(f"❌ Error generating content: {str(e)}")
            return "[En attente de contenu]"
            
    def _validate_diff_format(self, content: str) -> bool:
        """
        Valide que le contenu suit le format de diff avec une grande permissivité.
        Cherche simplement la présence des marqueurs essentiels dans le bon ordre.
        """
        # Vérifier simplement la présence des marqueurs clés dans le bon ordre
        markers = [
            "<<<<<<< ANCIEN",
            "=======",
            ">>>>>>> NOUVEAU"
        ]
        
        pos = -1
        for marker in markers:
            new_pos = content.find(marker, pos + 1)
            if new_pos == -1:
                self.logger(f"[{self.__class__.__name__}] ❌ Format invalide: marqueur '{marker}' manquant")
                # Log la réponse complète pour debug
                self.logger(f"[{self.__class__.__name__}] Réponse reçue:\n{content}")
                return False
            pos = new_pos
        
        return True

    def determine_actions(self) -> None:
        """Logique principale de l'agent"""
        try:
            self.logger(f"[{self.__class__.__name__}] Analyse du contenu...")
            
            # Vérifier que le chemin du fichier est correct
            if not os.path.exists(self.file_path):
                self.logger(f"[{self.__class__.__name__}] ❌ Chemin de fichier invalide: {self.file_path}")
                return

            context = {
                "production": self.current_content,
                "other_files": self.other_files,
                "file_path": self.file_path  # Ajouter le chemin pour debug
            }
            
            # Log du contexte pour debug
            self.logger(f"[{self.__class__.__name__}] Utilisation du fichier: {self.file_path}")
            
            response = self._get_llm_response(context)
            if not response:
                self.logger(f"[{self.__class__.__name__}] ❌ Pas de réponse du LLM")
                return
                
            # Vérifier et écrire le nouveau contenu
            if response.strip():
                try:
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        f.write(response)
                    self.current_content = response
                    self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour: {self.file_path}")
                except Exception as write_error:
                    self.logger(f"[{self.__class__.__name__}] ❌ Erreur d'écriture: {str(write_error)}")
                    raise
                    
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

    def write_file(self, content: str) -> bool:
        """Write content to file with path validation"""
        try:
            if not self.validate_file_path():
                return False
                
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.current_content = content
            self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour: {self.file_path}")
            return True
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur écriture: {str(e)}")
            return False

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response with standardized error handling"""
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            
            # Try OpenAI first
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",  # Modèle standard de openai (ne pas remplacer)
                    messages=[{
                        "role": "user",
                        "content": self._build_prompt(context)
                    }],
                    temperature=0,
                    max_tokens=4000
                )
                return response.choices[0].message.content
                
            except Exception as openai_error:
                self.logger(f"[{self.__class__.__name__}] OpenAI error, falling back to Anthropic: {str(openai_error)}")
                
                # Fallback to Anthropic
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": self._build_prompt(context)
                    }]
                )
                return response.content
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return context.get('production', '')  # Return current content as fallback

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract content of a specific management section.
        
        Used for:
        - Isolating current directives
        - Accessing task lists
        - Retrieving action history
        - Maintaining document structure
        - Processing section-specific updates
        - Preserving content organization
        
        Args:
            content: Full management content
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

    def _format_other_files(self, files: dict) -> str:
        """
        Format other files content for production context.
        
        Organizes:
        - Specifications requirements
        - Management directives
        - Evaluation feedback
        - Related content references
        
        Args:
            files: Dictionary of file contents
            
        Returns:
            str: Formatted context for content decisions
        """
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)

    def _build_prompt(self, context: dict) -> str:
        return f"""Vous êtes l'agent de production. Votre rôle est de produire le contenu selon les spécifications.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Contenu actuel :
{context['production']}

Votre tâche :
1. Analyser les spécifications et la demande
2. Produire ou mettre à jour le contenu
3. Respecter le format markdown

Format de réponse attendu :
- Contenu markdown direct (pas de commande aider)
- Sections avec titres de niveau 1 (#)
- Contenu structuré et formaté
- Pas de métadonnées ou commandes

IMPORTANT:
- Retourner uniquement le contenu markdown
- Conserver la structure existante si pertinente
- Mettre à jour ou ajouter du contenu selon les besoins
- Ne pas inclure de commandes ou instructions"""
    def _extract_sections(self, content: str) -> dict:
        """
        Extract sections from content while preserving hierarchy.
        
        Used for:
        - Maintaining document structure
        - Processing section-specific updates
        - Preserving content organization
        
        Args:
            content: Full document content
            
        Returns:
            dict: Mapping of section names to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('# '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)
                
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections

    def _extract_diff_parts(self, content: str) -> list[tuple[str, str]]:
        """
        Extrait les parties ancien/nouveau du format diff avec une grande permissivité.
        Accepte tout type de séparateur et d'espacement.
        """
        import re
        # Pattern très permissif qui accepte tout type d'espacement
        pattern = r'<{3,}\s*ANCIEN\s*([^=~]*?)\s*[=~]{3,}\s*(.*?)\s*>{3,}\s*NOUVEAU'
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        
        # Nettoyer les résultats
        cleaned_matches = []
        for old_text, new_text in matches:
            # Enlever les crochets si présents
            old_clean = old_text.strip('[]')
            new_clean = new_text.strip()
            
            # Nettoyer les espaces tout en préservant la structure
            old_clean = '\n'.join(line.strip() for line in old_clean.splitlines())
            new_clean = '\n'.join(line.strip() for line in new_text.splitlines())
            
            if old_clean and new_clean:  # Garder seulement si les deux parties ont du contenu
                cleaned_matches.append((old_clean, new_clean))
                
        return cleaned_matches

    def _apply_diffs(self, current_content: str, diffs: list[tuple[str, str]]) -> str:
        """
        Applique les diffs au contenu actuel en utilisant SearchReplace
        """
        modified_content = current_content
        for old_text, new_text in diffs:
            # Nettoyer les textes
            old_text = old_text.strip()
            new_text = new_text.strip()
            
            # Utiliser SearchReplace pour faire la modification
            result = SearchReplace.section_replace(modified_content, old_text, new_text)
            if result.success and result.content:  # Vérifier que content existe
                modified_content = result.content  # Utiliser content au lieu de new_content
                self.logger(f"✓ Remplacement effectué: '{old_text}' -> '{new_text}'")
            else:
                self.logger(f"❌ Échec du remplacement: {result.message}")
                
        return modified_content

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Analyse du contenu...")
            
            context = {
                "production": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            if not response:
                self.logger(f"[{self.__class__.__name__}] ❌ Pas de réponse du LLM")
                return
                
            # Vérifier que la réponse contient bien du contenu de production
            if not response.strip():
                self.logger(f"[{self.__class__.__name__}] ❌ Réponse vide")
                return
                
            # Écrire le nouveau contenu de production
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(response)
            self.current_content = response
            self.logger(f"[{self.__class__.__name__}] ✓ Fichier production.md mis à jour")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")
