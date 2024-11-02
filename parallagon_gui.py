"""
ParallagonGUI - Interface graphique pour le framework Parallagon
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class ParallagonGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("⚫ Parallagon")
        self.running = False
        self.update_interval = 1000  # ms
        
        # Configuration de la fenêtre principale
        self.root.geometry("1200x800")
        self.setup_ui()
        
        # Initialisation des agents (à implémenter)
        self.agents = {}
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Panneau de contrôle
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(
            self.control_frame, 
            text="Start", 
            command=self.start_agents
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            self.control_frame, 
            text="Stop", 
            command=self.stop_agents,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            self.control_frame, 
            text="● Stopped", 
            foreground="red"
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Zone de demande
        self.request_frame = ttk.LabelFrame(self.root, text="Demande")
        self.request_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.request_text = scrolledtext.ScrolledText(
            self.request_frame, 
            height=4
        )
        self.request_text.pack(fill=tk.X, padx=5, pady=5)
        
        self.submit_button = ttk.Button(
            self.request_frame, 
            text="Soumettre", 
            command=self.submit_request
        )
        self.submit_button.pack(pady=5)
        
        # Panneaux des agents
        self.agents_frame = ttk.Frame(self.root)
        self.agents_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configuration du grid 2x2 pour les agents
        self.agents_frame.columnconfigure(0, weight=1)
        self.agents_frame.columnconfigure(1, weight=1)
        self.agents_frame.rowconfigure(0, weight=1)
        self.agents_frame.rowconfigure(1, weight=1)
        
        # Création des panneaux d'agents
        self.agent_panels = {}
        agents_config = [
            ("Specification", 0, 0),
            ("Management", 0, 1),
            ("Production", 1, 0),
            ("Evaluation", 1, 1)
        ]
        
        for name, row, col in agents_config:
            panel = AgentPanel(self.agents_frame, name)
            panel.frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            self.agent_panels[name] = panel
            
    def start_agents(self):
        """Démarrage des agents"""
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="● Running", foreground="green")
        
        # Démarrage de la boucle de mise à jour
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
    def stop_agents(self):
        """Arrêt des agents"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Stopped", foreground="red")
        
    def update_loop(self):
        """Boucle de mise à jour des panneaux"""
        while self.running:
            self.root.after(0, self.update_all_panels)
            time.sleep(self.update_interval / 1000)
            
    def update_all_panels(self):
        """Mise à jour de tous les panneaux d'agents"""
        for name, panel in self.agent_panels.items():
            try:
                file_path = f"{name.lower()}.md"
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                panel.update_content(content)
            except Exception as e:
                print(f"Error updating {name} panel: {e}")
                
    def submit_request(self):
        """Soumission d'une nouvelle demande"""
        request_text = self.request_text.get("1.0", tk.END).strip()
        if not request_text:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_request = f"""# Demande Actuelle
[timestamp: {timestamp}]
[status: EN_COURS]

{request_text}

# Historique des Demandes"""
            
            with open("demande.md", 'r+', encoding='utf-8') as f:
                content = f.read()
                result = SearchReplace.section_replace(
                    content,
                    "Demande Actuelle",
                    new_request
                )
                if result.success:
                    f.seek(0)
                    f.write(result.new_content)
                    f.truncate()
                    
            self.request_text.delete("1.0", tk.END)
            
        except Exception as e:
            print(f"Error submitting request: {e}")
            
    def run(self):
        """Démarrage de l'interface"""
        self.root.mainloop()


class AgentPanel:
    """Panneau d'affichage pour un agent"""
    def __init__(self, parent, title):
        self.frame = ttk.LabelFrame(parent, text=title)
        
        self.text = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            width=50,
            height=20
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configuration des tags pour le highlighting
        self.text.tag_configure(
            "highlight",
            background="yellow"
        )
        
    def update_content(self, content: str):
        """Mise à jour du contenu avec highlighting des changements"""
        current = self.text.get("1.0", tk.END).strip()
        if content.strip() != current:
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.highlight_changes()
            
    def highlight_changes(self):
        """Mise en évidence temporaire des changements"""
        self.text.tag_add("highlight", "1.0", tk.END)
        self.frame.after(1000, self.clear_highlight)
        
    def clear_highlight(self):
        """Suppression du highlighting"""
        self.text.tag_remove("highlight", "1.0", tk.END)


if __name__ == "__main__":
    gui = ParallagonGUI()
    gui.run()
