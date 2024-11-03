"""
CollapsibleSection - Collapsible section widget for Parallagon GUI
"""
import tkinter as tk
from tkinter import ttk
from section import Section

class CollapsibleSection(ttk.Frame):
    """Widget d'accordéon pour afficher une section"""
    def __init__(self, parent, section: Section, **kwargs):
        super().__init__(parent, **kwargs)
        self.section = section
        
        # Frame pour le titre et le bouton d'expansion
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Bouton d'expansion
        self.toggle_button = ttk.Button(
            self.header_frame,
            text="▼" if section.is_expanded else "▶",
            width=2,
            command=self.toggle
        )
        self.toggle_button.pack(side=tk.LEFT, padx=(0,5))
        
        # Titre de la section
        self.title_label = ttk.Label(
            self.header_frame,
            text=section.title,
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X)
        
        # Contenu expandable
        self.content_frame = ttk.Frame(self)
        if section.is_expanded:
            self.content_frame.pack(fill=tk.BOTH, padx=20, pady=5)
            
        # Zone des contraintes
        self.constraints_frame = ttk.LabelFrame(self.content_frame, text="Contraintes")
        self.constraints_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.constraints_text = tk.Text(
            self.constraints_frame,
            height=3,
            wrap=tk.WORD,
            state="disabled"
        )
        self.constraints_text.pack(fill=tk.X, padx=5, pady=5)
        self.update_constraints(section.constraints)
        
        # Zone du contenu
        self.content_frame_inner = ttk.LabelFrame(self.content_frame, text="Contenu")
        self.content_frame_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.content_text = tk.Text(
            self.content_frame_inner,
            height=5,
            wrap=tk.WORD,
            state="normal" if section.content else "disabled"
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        if section.content:
            self.content_text.insert("1.0", section.content)
            
    def toggle(self):
        """Bascule l'état d'expansion de la section"""
        self.section.is_expanded = not self.section.is_expanded
        if self.section.is_expanded:
            self.toggle_button.configure(text="▼")
            self.content_frame.pack(fill=tk.BOTH, padx=20, pady=5)
        else:
            self.toggle_button.configure(text="▶")
            self.content_frame.pack_forget()
            
    def update_constraints(self, constraints: str):
        """Met à jour les contraintes"""
        self.constraints_text.configure(state="normal")
        self.constraints_text.delete("1.0", tk.END)
        self.constraints_text.insert("1.0", constraints)
        self.constraints_text.configure(state="disabled")
        
    def update_content(self, content: str):
        """Met à jour le contenu"""
        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", content)
"""
CollapsibleSection - Collapsible section widget for Parallagon GUI
"""
import tkinter as tk
from tkinter import ttk
from section import Section

class CollapsibleSection(ttk.Frame):
    def __init__(self, parent, section: Section, callbacks=None):
        super().__init__(parent)
        self.section = section
        self.callbacks = callbacks or {}
        self.expanded = True
        
        # Header with expand/collapse
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill=tk.X)
        
        self.toggle_button = ttk.Button(
            self.header_frame,
            text="▼",
            width=3,
            command=self.toggle
        )
        self.toggle_button.pack(side=tk.LEFT)
        
        ttk.Label(
            self.header_frame,
            text=section.title
        ).pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        self.actions_frame = ttk.Frame(self.header_frame)
        self.actions_frame.pack(side=tk.RIGHT)
        
        self.edit_button = ttk.Button(
            self.actions_frame,
            text="✎",
            width=3,
            command=self._on_edit
        )
        self.edit_button.pack(side=tk.LEFT, padx=2)
        
        # Content
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.X, padx=20)
        
        if section.constraints:
            ttk.Label(
                self.content_frame,
                text=f"Contraintes: {section.constraints}",
                wraplength=400
            ).pack(fill=tk.X)
            
        self.content_text = tk.Text(
            self.content_frame,
            height=4,
            wrap=tk.WORD
        )
        self.content_text.pack(fill=tk.X)
        
        if section.content:
            self.content_text.insert("1.0", section.content)
        self.content_text.config(state="disabled")
        
    def toggle(self):
        """Toggle section expansion"""
        self.expanded = not self.expanded
        if self.expanded:
            self.content_frame.pack(fill=tk.X, padx=20)
            self.toggle_button.config(text="▼")
        else:
            self.content_frame.pack_forget()
            self.toggle_button.config(text="▶")
            
    def _on_edit(self):
        """Trigger edit callback"""
        if 'on_edit' in self.callbacks:
            self.callbacks['on_edit'](self.section)
            
    def update_content(self, content: str):
        """Update section content"""
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", content)
        self.content_text.config(state="disabled")
        self.section.content = content
