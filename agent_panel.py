"""
AgentPanel - GUI panel for displaying agent content
"""
import tkinter as tk
from tkinter import scrolledtext
import json

class AgentPanel:
    """Panel for displaying and managing agent content"""
    def __init__(self, parent, title: str, text_widget: scrolledtext.ScrolledText):
        self.frame = parent
        self.title = title
        self.text = text_widget
        self.flash_count = 0
        self.flash_active = False
        
        # Configuration du highlighting
        self.text.tag_configure(
            "highlight",
            background="#e8f0fe"
        )
        
    def update_content(self, content: str) -> None:
        """Update panel content with smarter diff highlighting"""
        current = self.text.get("1.0", tk.END).strip()
        if content.strip() != current:
            print(f"[AgentPanel] Content changed for {self.title}")
            # Store scroll position
            current_pos = self.text.yview()
            
            # Find differences
            old_lines = current.split('\n')
            new_lines = content.split('\n')
            
            # Clear and insert new content
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            
            # Highlight changed lines
            self._highlight_changes(old_lines, new_lines)
            
            # Restore scroll position
            self.text.yview_moveto(current_pos[0])

    def _highlight_changes(self, old_lines: list, new_lines: list):
        """Highlight changed lines using difflib"""
        import difflib
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'insert'):
                start = f"{j1 + 1}.0"
                end = f"{j2 + 1}.0"
                self.text.tag_add("highlight", start, end)
            
    def highlight_changes(self) -> None:
        """Temporarily highlight changes"""
        self.text.tag_add("highlight", "1.0", tk.END)
        self.frame.after(1000, self.clear_highlight)
        
    def clear_highlight(self) -> None:
        """Remove highlighting"""
        self.text.tag_remove("highlight", "1.0", tk.END)

    def flash_tab(self):
        """Flash the tab background to indicate changes"""
        try:
            print(f"AgentPanel: Starting flash for {self.title}")
            self.flash_active = True
            self.flash_count = 0
            
            # Force immediate UI update
            self.frame.update_idletasks()
            
            # Start flash animation
            self.frame.after(0, self._do_flash)
            
        except Exception as e:
            print(f"AgentPanel Flash Error: {str(e)}")

    def _do_flash(self):
        """Handle the actual flashing animation"""
        try:
            if self.flash_count >= 6:  # 3 flashes
                self.flash_active = False
                self.frame.configure(background='SystemButtonFace')
                print(f"AgentPanel: Flash complete for {self.title}")
                return
                
            color = '#ffd700' if self.flash_count % 2 else 'SystemButtonFace'
            self.frame.configure(background=color)
            
            self.flash_count += 1
            self.frame.after(400, self._do_flash)
            
        except Exception as e:
            print(f"AgentPanel Flash Animation Error: {str(e)}")
            
    def start_flash(self):
        """Start the flashing effect"""
        # Reset any ongoing flash
        if self.flash_active:
            self.frame.configure(background='SystemButtonFace')
            self.flash_count = 0
            
        print(f"[AgentPanel] Starting flash animation for {self.title}")
            
        # Start new flash
        self.flash_active = True
        self.flash_count = 0
        self.flash_tab()
        
        # Also highlight recent changes
        self.highlight_changes()
