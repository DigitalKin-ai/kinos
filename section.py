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
"""
Section - Data class for document sections
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Section:
    """Represents a document section with title, constraints and content"""
    title: str
    constraints: Optional[str] = None
    content: Optional[str] = None
    todo: Optional[list[str]] = None
