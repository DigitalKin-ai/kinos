"""
SectionEditDialog - Dialog for editing section content
"""
import tkinter as tk
from tkinter import ttk
from section import Section

class SectionEditDialog(tk.Toplevel):
    def __init__(self, parent, section: Section):
        super().__init__(parent)
        self.section = section
        self.result = None
        
        self.title(f"Édition - {section.title}")
        self.geometry("600x400")
        
        # Constraints area (read-only)
        constraints_frame = ttk.LabelFrame(self, text="Contraintes")
        constraints_frame.pack(fill=tk.X, padx=5, pady=5)
        
        constraints_text = tk.Text(
            constraints_frame,
            height=3,
            wrap=tk.WORD,
            state="disabled"
        )
        constraints_text.pack(fill=tk.X, padx=5, pady=5)
        constraints_text.insert("1.0", section.constraints)
        
        # Content editing area
        content_frame = ttk.LabelFrame(self, text="Contenu")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.content_text = tk.Text(
            content_frame,
            wrap=tk.WORD
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        if section.content:
            self.content_text.insert("1.0", section.content)
            
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Annuler",
            command=self.cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Sauvegarder",
            command=self.save
        ).pack(side=tk.RIGHT)
        
    def save(self):
        """Save modifications"""
        self.section.content = self.content_text.get("1.0", tk.END).strip()
        self.result = True
        self.destroy()
        
    def cancel(self):
        """Cancel modifications"""
        self.result = False
        self.destroy()
