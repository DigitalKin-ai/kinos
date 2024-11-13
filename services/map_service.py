"""
MapService - Service for generating and managing project documentation map
"""
import os
from datetime import datetime
from typing import Dict, List, Tuple
from services.base_service import BaseService
from anthropic import Anthropic
from utils.logger import Logger

class MapService(BaseService):
    """Manages project documentation mapping and size monitoring"""

    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        self.logger = Logger()
        self.map_file = "map (readonly).md"
        self.size_limits = {
            'warning': 6000,  # Tokens triggering warning (6k)
            'error': 12000    # Tokens triggering error (12k)
        }
        # Initialize Anthropic client for tokenization
        self.anthropic = Anthropic()
        
        # Initialize phase_service as None - will be loaded on demand
        self.phase_service = None

    def _ensure_phase_service(self):
        """Lazy initialization of phase service"""
        if self.phase_service is None:
            # Import locally to avoid circular import
            from services.phase_service import PhaseService
            self.phase_service = PhaseService(None)

    def generate_map(self) -> bool:
        """Generate project map file"""
        try:
            print("[DEBUG] Starting map generation")
            tree_content, warnings, total_tokens = self._scan_directory(os.getcwd())
            
            print(f"[DEBUG] Scan complete - Total tokens: {total_tokens}")
            
            # Ensure phase service is initialized
            self._ensure_phase_service()
            
            print("[DEBUG] Phase service initialized")
            
            # Update phase service with total tokens
            self.phase_service.determine_phase(total_tokens)
            
            print("[DEBUG] Phase determined")
            
            map_content = self._format_map_content(tree_content, warnings)
            
            success = self._write_map_file(map_content)
            print(f"[DEBUG] Map written: {success}")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] Error generating map: {str(e)}")
            self.logger.log(f"Error generating map: {str(e)}", 'error')
            return False

    def _scan_directory(self, path: str, prefix: str = "") -> Tuple[List[str], List[str], int]:
        """Scan directory recursively and return tree structure, warnings and total tokens"""
        try:
            tree_lines = []
            warnings = []
            total_tokens = 0

            # Load ignore patterns from .gitignore
            gitignore_path = os.path.join(os.getcwd(), '.gitignore')
            ignore_patterns = []
            if os.path.exists(gitignore_path):
                try:
                    with open(gitignore_path, 'r', encoding='utf-8') as f:
                        ignore_patterns = [
                            line.strip() for line in f.readlines()
                            if line.strip() and not line.startswith('#')
                        ]
                except Exception:
                    pass

            # Create PathSpec for pattern matching
            from pathspec import PathSpec
            from pathspec.patterns import GitWildMatchPattern
            spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns)

            # Get and sort directory contents
            items = sorted(os.listdir(path))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = prefix + ("└── " if is_last else "├── ")
                full_path = os.path.join(path, item)
                rel_path = os.path.relpath(full_path, os.getcwd())

                # Skip if matches ignore patterns
                if spec.match_file(rel_path):
                    continue
                
                if os.path.isdir(full_path):
                    tree_lines.append(f"{current_prefix}📁 {item}/")
                    sub_prefix = prefix + ("    " if is_last else "│   ")
                    sub_tree, sub_warnings, sub_tokens = self._scan_directory(full_path, sub_prefix)
                    
                    if sub_tree:
                        tree_lines.extend(sub_tree)
                        warnings.extend(sub_warnings)
                        total_tokens += sub_tokens
                    else:
                        tree_lines.pop()
                    
                elif item.endswith('.md'):
                    token_count = self._count_tokens(full_path)
                    total_tokens += token_count
                    status_icon = self._get_status_icon(token_count)
                    
                    size_k = token_count / 1000
                    tree_lines.append(
                        f"{current_prefix}📄 {item} ({size_k:.1f}k tokens) {status_icon}"
                    )
                    
                    warning = self._check_file_size(item, token_count)
                    if warning:
                        warnings.append(warning)
                        
            return tree_lines, warnings, total_tokens
            
        except Exception as e:
            self.logger.log(f"Error scanning directory: {str(e)}", 'error')
            return [], [], 0

    def _count_tokens(self, file_path: str) -> int:
        """Count number of tokens in a file using Anthropic tokenizer"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Use Anthropic's tokenizer to count tokens
                return self.anthropic.count_tokens(content)
        except Exception:
            return 0

    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored in map"""
        ignore_patterns = [
            '.git/',
            '__pycache__/',
            'node_modules/',
            '.env',
            '.aider*',
            '*.pyc',
            '*.log'
        ]
        
        for pattern in ignore_patterns:
            if pattern in file_path:
                return True
        return False

    def _get_status_icon(self, token_count: int) -> str:
        """Get status icon based on token count"""
        if token_count > self.size_limits['error']:
            return "🔴"
        elif token_count > self.size_limits['warning']:
            return "⚠️"
        return "✓"

    def _check_file_size(self, filename: str, token_count: int) -> str:
        """Generate warning message if file exceeds size limits"""
        if token_count > self.size_limits['error']:
            return f"🔴 {filename} needs consolidation (>{self.size_limits['error']/1000:.1f}k tokens)"
        elif token_count > self.size_limits['warning']:
            return f"⚠️ {filename} approaching limit (>{self.size_limits['warning']/1000:.1f}k tokens)"
        return ""

    def _get_phase_description(self, phase_status: dict) -> str:
        """Get descriptive text about current phase and its implications"""
        phase = phase_status['phase']
        
        if phase == "EXPANSION":
            return (
                "🌱 EXPANSION PHASE\n"
                "In this phase, agents focus on content creation and development:\n"
                "- Free to create new content and sections\n"
                "- Normal operation of all agents\n"
                "- Regular token monitoring\n"
                f"- Will transition to CONVERGENCE at {self.phase_service.CONVERGENCE_TOKENS/1000:.1f}k tokens"
            )
        else:  # CONVERGENCE
            return (
                "🔄 CONVERGENCE PHASE\n"
                "In this phase, agents focus on optimization and consolidation:\n"
                "- Limited new content creation\n"
                "- Focus on reducing token usage\n"
                "- Emphasis on content optimization\n"
                f"- Can return to EXPANSION below {self.phase_service.EXPANSION_TOKENS/1000:.1f}k tokens"
            )

    def _format_map_content(self, tree_content: List[str], warnings: List[str]) -> str:
        """Format complete map (readonly).md content with introduction and phase information"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure phase service is initialized
        self._ensure_phase_service()
        
        # Get phase status from PhaseService
        phase_status = self.phase_service.get_status_info()
        
        content = [
            "# Project Map",
            "\nCe document est une carte dynamique du projet qui est automatiquement mise à jour pour fournir une vue d'ensemble de la structure et de l'état du projet. Il surveille notamment :",
            "- L'arborescence complète des fichiers",
            "- La taille de chaque document en tokens",
            "- La phase actuelle du projet (EXPANSION/CONVERGENCE)",
            "- Les alertes et recommandations d'optimisation",
            "\nLa map est automatiquement mise à jour par le MapService à chaque :",
            "- Modification de fichier markdown",
            "- Changement de phase du projet",
            "- Création ou suppression de fichier",
            "\nLes indicateurs visuels (✓, ⚠️, 🔴) permettent d'identifier rapidement les fichiers nécessitant une attention particulière.",
            f"\nGenerated: {timestamp}\n",
            "## Project Phase",
            self._get_phase_description(phase_status),
            "\n## Token Usage",
            f"Total: {phase_status['total_tokens']/1000:.1f}k/{self.phase_service.MODEL_TOKEN_LIMIT/1000:.0f}k ({phase_status['usage_percent']:.1f}%)",
            f"Convergence at: {self.phase_service.CONVERGENCE_TOKENS/1000:.1f}k ({self.phase_service.CONVERGENCE_THRESHOLD*100:.0f}%)\n",
            "## Phase Status",
            f"{phase_status['status_icon']} {phase_status['status_message']}",
            f"Headroom: {phase_status['headroom']/1000:.1f}k tokens\n",
            "## Document Tree",
            "📁 Project"
        ]
        
        # Add tree structure
        content.extend(tree_content)
        
        # Add warnings if any
        if warnings:
            content.extend([
                "\n## Warnings",
                *warnings
            ])
            
        return "\n".join(content)

    def _write_map_file(self, content: str) -> bool:
        """Write content to map file"""
        try:
            with open(self.map_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.log(f"Error writing map file: {str(e)}", 'error')
            return False

    def update_map(self) -> bool:
        """Update map after file changes"""
        return self.generate_map()

    def get_map_content(self) -> str:
        """Get current map content"""
        try:
            if os.path.exists(self.map_file):
                with open(self.map_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            self.logger.log(f"Error reading map file: {str(e)}", 'error')
            return ""

    def get_map_content(self) -> str:
        """Get current map content"""
        try:
            if os.path.exists(self.map_file):
                with open(self.map_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            self.logger.log(f"Error reading map file: {str(e)}", 'error')
            return ""
