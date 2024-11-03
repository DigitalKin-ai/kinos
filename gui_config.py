"""
Configuration settings for Parallagon GUI
"""
from dataclasses import dataclass, field
from typing import Dict

@dataclass(frozen=True)
class GUIConfig:
    """Configuration settings for the GUI"""
    colors: Dict[str, str] = field(default_factory=lambda: {
        'bg': '#f0f2f5',
        'panel_bg': '#ffffff',
        'accent': '#1a73e8',
        'text': '#202124',
        'secondary_text': '#5f6368',
        'border': '#dadce0',
        'highlight': '#e8f0fe'
    })
    update_interval: int = 1000  # ms
    max_log_lines: int = 1000
    font_family: str = 'Segoe UI'
    font_size: int = 10
    
    def __post_init__(self):
        if self.colors is None:
            # Use object.__setattr__ to modify frozen class attributes
            object.__setattr__(self, 'colors', {
                'bg': '#f0f2f5',
                'panel_bg': '#ffffff',
                'accent': '#1a73e8',
                'text': '#202124',
                'secondary_text': '#5f6368',
                'border': '#dadce0',
                'highlight': '#e8f0fe'
            })
