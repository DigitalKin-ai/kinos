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
