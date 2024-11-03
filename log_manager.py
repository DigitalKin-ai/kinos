"""
LogManager - Centralized logging management for Parallagon GUI
"""
from datetime import datetime
import tkinter as tk
from typing import Dict

class LogManager:
    """Manages logging display and formatting in the GUI"""
    
    # Color configurations for different log levels
    TAG_COLORS = {
        'timestamp': '#a0a0a0',  # Gris plus clair pour l'horodatage
        'success': '#4CAF50',    # Vert pour les succès
        'error': '#f44336',      # Rouge pour les erreurs
        'info': '#2196F3',       # Bleu pour les infos
        'reset': '#FF9800',      # Orange pour les resets
        'changes': '#9C27B0',    # Violet pour les résumés de changements
        'no_changes': '#808080'  # Gris pour les messages "aucun changement"
    }
    
    def __init__(self, text_widget: tk.Text):
        """Initialize the log manager with a text widget"""
        self.text_widget = text_widget
        self.setup_tags()
    
    def setup_tags(self):
        """Configure text tags for different message types"""
        for tag, color in self.TAG_COLORS.items():
            self.text_widget.tag_config(tag, foreground=color)
    
    def log(self, message: str):
        """Add a formatted log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine message type and tag
        if "❌" in message:
            tag = 'error'
        elif "✓" in message:
            if "Aucun changement" in message:
                tag = 'no_changes'
            elif any(panel in message for panel in ["Specification", "Evaluation", "Management", "Production", "Demande"]):
                tag = 'changes'
            else:
                tag = 'success'
        elif "✨" in message:
            tag = 'reset'
        else:
            tag = 'info'
            
        # Insert formatted message
        self.text_widget.insert(tk.END, f"[", 'timestamp')
        self.text_widget.insert(tk.END, timestamp, 'timestamp')
        self.text_widget.insert(tk.END, f"] ", 'timestamp')
        self.text_widget.insert(tk.END, f"{message}\n", tag)
        
        # Auto-scroll to latest message
        self.text_widget.see(tk.END)
    
    def clear(self):
        """Clear all log messages"""
        self.text_widget.delete("1.0", tk.END)
    
    def export_logs(self, filepath: str):
        """Export logs to a file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.text_widget.get("1.0", tk.END))
            return True
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return False
"""
LogManager - Centralized logging management for Parallagon GUI
"""
from datetime import datetime
import tkinter as tk
from typing import Dict

class LogManager:
    """Manages logging display and formatting in the GUI"""
    
    # Color configurations for different log levels
    TAG_COLORS = {
        'timestamp': '#a0a0a0',  # Gris plus clair pour l'horodatage
        'success': '#4CAF50',    # Vert pour les succès
        'error': '#f44336',      # Rouge pour les erreurs
        'info': '#2196F3',       # Bleu pour les infos
        'reset': '#FF9800',      # Orange pour les resets
        'changes': '#9C27B0',    # Violet pour les résumés de changements
        'no_changes': '#808080'  # Gris pour les messages "aucun changement"
    }
    
    def __init__(self, text_widget: tk.Text):
        """Initialize the log manager with a text widget"""
        self.text_widget = text_widget
        self.setup_tags()
    
    def setup_tags(self):
        """Configure text tags for different message types"""
        for tag, color in self.TAG_COLORS.items():
            self.text_widget.tag_config(tag, foreground=color)
    
    def log(self, message: str):
        """Add a formatted log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine message type and tag
        if "❌" in message:
            tag = 'error'
        elif "✓" in message:
            if "Aucun changement" in message:
                tag = 'no_changes'
            elif any(panel in message for panel in ["Specification", "Evaluation", "Management", "Production", "Demande"]):
                tag = 'changes'
            else:
                tag = 'success'
        elif "✨" in message:
            tag = 'reset'
        else:
            tag = 'info'
            
        # Insert formatted message
        self.text_widget.insert(tk.END, f"[", 'timestamp')
        self.text_widget.insert(tk.END, timestamp, 'timestamp')
        self.text_widget.insert(tk.END, f"] ", 'timestamp')
        self.text_widget.insert(tk.END, f"{message}\n", tag)
        
        # Auto-scroll to latest message
        self.text_widget.see(tk.END)
    
    def clear(self):
        """Clear all log messages"""
        self.text_widget.delete("1.0", tk.END)
    
    def export_logs(self, filepath: str):
        """Export logs to a file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.text_widget.get("1.0", tk.END))
            return True
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return False
"""
LogManager - Centralizes logging functionality for the GUI
"""
import tkinter as tk
from datetime import datetime

class LogManager:
    """Manages logging display and formatting in the GUI"""
    
    def __init__(self, text_widget: tk.Text):
        """Initialize with a text widget"""
        self.text_widget = text_widget
        self.setup_tags()
        
    def setup_tags(self):
        """Configure text display tags"""
        self.text_widget.tag_configure('timestamp', foreground='#a0a0a0')
        self.text_widget.tag_configure('error', foreground='#ff0000')
        self.text_widget.tag_configure('success', foreground='#00aa00')
        self.text_widget.tag_configure('warning', foreground='#ff8800')
        self.text_widget.tag_configure('info', foreground='#0088ff')
        
    def log(self, message: str):
        """Add a timestamped message to logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Déterminer le niveau de log basé sur les émojis/symboles
        level = 'info'
        if '❌' in message:
            level = 'error'
        elif '✓' in message or '✨' in message:
            level = 'success'
        elif '⚠️' in message:
            level = 'warning'
            
        # Insérer le message
        self.text_widget.insert('end', f"[{timestamp}] ", 'timestamp')
        self.text_widget.insert('end', f"{message}\n", level)
        self.text_widget.see('end')  # Auto-scroll
        
    def clear(self):
        """Clear all logs"""
        self.text_widget.delete('1.0', 'end')
