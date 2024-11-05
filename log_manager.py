"""
LogManager - Centralized logging management for Parallagon GUI
"""
from datetime import datetime
import tkinter as tk
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum, auto

class LogLevel(Enum):
    """Log levels with their associated symbols and colors"""
    SUCCESS = ("✓", "#4CAF50")
    ERROR = ("❌", "#f44336")
    INFO = ("ℹ", "#2196F3")
    RESET = ("✨", "#FF9800")
    CHANGES = ("↻", "#9C27B0")
    NO_CHANGES = ("≡", "#808080")
    WARNING = ("⚠️", "#FFC107")

@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    message: str
    level: LogLevel
    agent: Optional[str] = None
from enum import Enum, auto

class LogLevel(Enum):
    """Log levels with their associated symbols and colors"""
    SUCCESS = ("✓", "#4CAF50")
    ERROR = ("❌", "#f44336")
    INFO = ("ℹ", "#2196F3")
    RESET = ("✨", "#FF9800")
    CHANGES = ("↻", "#9C27B0")
    NO_CHANGES = ("≡", "#808080")
    WARNING = ("⚠️", "#FFC107")

@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    message: str
    level: LogLevel
    agent: Optional[str] = None

class LogManager:
    """Manages logging display and formatting in the GUI"""
    
    MAX_LOGS = 1000  # Maximum number of logs to keep in memory
    COLORS = {
        'timestamp': '#a0a0a0',
        'success': '#4CAF50',
        'error': '#f44336',
        'info': '#2196F3',
        'warning': '#FFC107'
    }
    
    def __init__(self, text_widget: tk.Text):
        """Initialize the log manager with a text widget"""
        self.text_widget = text_widget
        
        # Configure widget to display more content
        self.text_widget.configure(
            height=10,         # Increased height
            width=120,        # Increased width
            background='#f8f9fa',
            fg='#666666',
            font=('TkDefaultFont', 9),  # Slightly larger font
            padx=10,          # More horizontal padding
            pady=5,
            wrap='word'       # Add word wrap to prevent word breaks
        )
        
        # Position with more space
        self.text_widget.pack(
            side='left',
            anchor='sw',
            padx=5,
            pady=5,
            expand=True,      # Allow expansion
            fill='both',      # Fill in both directions
            in_=self.text_widget.master
        )
        
        # Allow resizing
        self.text_widget.pack_propagate(True)
        
        self.logs: list[LogEntry] = []
        self.setup_tags()
        
    def setup_tags(self):
        """Configure text tags for different message types"""
        # Tag for timestamps - more discrete
        self.text_widget.tag_config('timestamp', 
            foreground='#999999',  # Light gray
            font=('TkDefaultFont', 7)  # Even smaller
        )
        
        # Animation tag - more subtle
        self.text_widget.tag_config('fade_in', 
            background='#f8f9fa'   # Barely visible
        )
        
        # Tags for each log level - softer colors
        colors = {
            'SUCCESS': '#66bb6a',  # Softer green
            'ERROR': '#ef5350',    # Softer red
            'INFO': '#78909c',     # Blueish gray, discrete
            'RESET': '#ffa726',    # Softer orange
            'CHANGES': '#ab47bc',  # Softer purple
            'NO_CHANGES': '#90a4ae',  # Softer gray
            'WARNING': '#ffd54f'   # Softer yellow
        }
        
        for level in LogLevel:
            self.text_widget.tag_config(
                level.name.lower(),
                foreground=colors.get(level.name, '#666666'),
                font=('TkDefaultFont', 8)  # Uniform font
            )
    
    def _determine_log_level(self, message: str) -> LogLevel:
        """Determine the log level based on message content"""
        if "❌" in message:
            return LogLevel.ERROR
        elif "⚠️" in message:
            return LogLevel.WARNING
        elif "✓" in message:
            return LogLevel.SUCCESS if "Aucun changement" not in message else LogLevel.NO_CHANGES
        elif "✨" in message:
            return LogLevel.RESET
        elif any(panel in message for panel in [
            "Specification", "Evaluation", "Management", 
            "Production", "Demande"
        ]):
            return LogLevel.CHANGES
        return LogLevel.INFO

    def _extract_agent_name(self, message: str) -> Optional[str]:
        """Extract agent name from message if present"""
        import re
        match = re.search(r'\[([\w]+Agent)\]', message)
        return match.group(1) if match else None

    def _format_log_entry(self, entry: LogEntry) -> str:
        """Format a log entry for display"""
        agent_prefix = f"[{entry.agent}] " if entry.agent else ""
        return f"[{entry.timestamp}] {agent_prefix}{entry.message}\n"

    def log(self, message: str):
        """Add a formatted log message with timestamp"""
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            message=message,
            level=self._determine_log_level(message),
            agent=self._extract_agent_name(message)
        )
        
        # Add to logs list and manage size
        self.logs.append(entry)
        self._manage_log_size()
        
        # Display the log entry
        self._display_log(entry)
        
        # Auto-scroll to latest message
        self.text_widget.see(tk.END)

    def _manage_log_size(self):
        """Manage log size to prevent memory issues"""
        if len(self.logs) > self.MAX_LOGS:
            # Remove oldest logs while keeping important ones
            important_logs = [log for log in self.logs 
                            if log.level in (LogLevel.ERROR, LogLevel.WARNING)]
            regular_logs = [log for log in self.logs 
                          if log.level not in (LogLevel.ERROR, LogLevel.WARNING)]
            
            # Keep all important logs and trim regular logs
            keep_regular = max(0, self.MAX_LOGS - len(important_logs))
            self.logs = important_logs + regular_logs[-keep_regular:]
            
            # Update text widget
            self.text_widget.delete("1.0", tk.END)
            for log in self.logs:
                self._display_log(log)

    def _display_log(self, log: LogEntry):
        """Display a single log entry with proper formatting and animation"""
        # Supprimer d'abord tous les tags fade_in existants
        self.text_widget.tag_remove('fade_in', "1.0", tk.END)
        
        # Configure animation tag
        self.text_widget.tag_config('fade_in', background='#e8f0fe')
        
        # Add timestamp
        timestamp_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, f"[{log.timestamp}] ", 'timestamp')
        
        # Add agent name if present
        if log.agent:
            self.text_widget.insert(tk.END, f"[{log.agent}] ", log.level.name.lower())
        
        # Add message with proper tag and animation
        # Utiliser le message complet sans le couper
        message_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, f"{log.message}\n", (log.level.name.lower(), 'fade_in'))
        message_end = self.text_widget.index(tk.END)
        
        # Configurer le widget pour permettre un affichage complet
        self.text_widget.configure(
            wrap='word',       # Activer le word wrap
            width=120,         # Augmenter la largeur pour plus de contenu
        )
        
        # Schedule animation removal with specific range
        def remove_fade():
            try:
                self.text_widget.tag_remove('fade_in', "1.0", tk.END)  # Supprimer pour tout le texte
            except Exception:
                pass  # Handle case where text widget might be destroyed
                
        # Utiliser after_idle pour garantir l'exécution après l'affichage
        self.text_widget.after_idle(lambda: self.text_widget.after(1000, remove_fade))
    
    def clear(self):
        """Clear all log messages"""
        self.logs.clear()
        self.text_widget.delete("1.0", tk.END)
    
    def get_logs_by_level(self, level: LogLevel) -> list[LogEntry]:
        """Get all logs of a specific level"""
        return [log for log in self.logs if log.level == level]
    
    def get_logs_by_agent(self, agent_name: str) -> list[LogEntry]:
        """Get all logs from a specific agent"""
        return [log for log in self.logs if log.agent == agent_name]
