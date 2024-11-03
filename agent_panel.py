"""
AgentPanel - GUI panel for displaying agent content
"""
import tkinter as tk
from tkinter import scrolledtext

class AgentPanel:
    """Panel for displaying and managing agent content"""
    def __init__(self, parent, title: str, text_widget: scrolledtext.ScrolledText):
        self.frame = parent
        self.title = title
        self.text = text_widget
        
        # Configuration du highlighting
        self.text.tag_configure(
            "highlight",
            background="#e8f0fe"
        )
        
    def update_content(self, content: str) -> None:
        """Update panel content with highlighting"""
        current = self.text.get("1.0", tk.END).strip()
        if content.strip() != current:
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.highlight_changes()
            
    def highlight_changes(self) -> None:
        """Temporarily highlight changes"""
        self.text.tag_add("highlight", "1.0", tk.END)
        self.frame.after(1000, self.clear_highlight)
        
    def clear_highlight(self) -> None:
        """Remove highlighting"""
        self.text.tag_remove("highlight", "1.0", tk.END)
