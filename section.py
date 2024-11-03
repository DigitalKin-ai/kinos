"""
Section - Data structure for document sections
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Section:
    """Représente une section avec ses contraintes et son contenu"""
    title: str
    constraints: str
    content: Optional[str] = None
    is_expanded: bool = False
