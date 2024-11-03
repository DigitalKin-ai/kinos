"""
ParallagonGUI - Interface graphique pour le framework Parallagon
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from search_replace import SearchReplace

class ParallagonGUI:
    def __init__(self, config: Dict[str, Any]):
        self.root = tk.Tk()
        self.root.title("⚫ Parallagon")
        self.running = False
        self.update_interval = 1000  # ms
        self.config = config
        
        # Configuration des couleurs et du thème
        self.colors = {
            'bg': '#f0f2f5',
            'panel_bg': '#ffffff',
            'accent': '#1a73e8',
            'text': '#202124',
            'secondary_text': '#5f6368',
            'border': '#dadce0',
            'highlight': '#e8f0fe'
        }

        # Configuration des styles
        style = ttk.Style()
        style.configure('Modern.TButton', 
            padding=10, 
            font=('Segoe UI', 10),
            background=self.colors['accent']
        )
        style.configure('Modern.TLabelframe', 
            background=self.colors['panel_bg'],
            padding=10
        )
        style.configure('Modern.TLabel', 
            font=('Segoe UI', 10),
            background=self.colors['bg']
        )
        style.configure('Updating.TLabelframe', 
            background=self.colors['highlight']
        )

        # Configuration de la fenêtre
        self.root.configure(bg=self.colors['bg'])
        
        # Configuration de la fenêtre principale
        self.root.state('zoomed')  # Pour Windows
        # self.root.attributes('-zoomed', True)  # Pour Linux
        self.setup_ui()
        self.init_agents()
        
    def init_agents(self):
        """Initialisation des agents"""
        from specifications_agent import SpecificationsAgent
        from management_agent import ManagementAgent
        from production_agent import ProductionAgent
        from evaluation_agent import EvaluationAgent
        
        base_config = {
            "check_interval": 5,
            "anthropic_api_key": self.config["anthropic_api_key"]
        }
        
        self.agents = {
            "Specification": SpecificationsAgent({
                **base_config,
                "file_path": "specifications.md",
                "watch_files": ["demande.md", "management.md", "production.md", "evaluation.md"]
            }),
            "Management": ManagementAgent({
                **base_config,
                "file_path": "management.md",
                "watch_files": ["demande.md", "specifications.md", "production.md", "evaluation.md"]
            }),
            "Production": ProductionAgent({
                **base_config,
                "file_path": "production.md",
                "watch_files": ["demande.md", "specifications.md", "management.md", "evaluation.md"]
            }),
            "Evaluation": EvaluationAgent({
                **base_config,
                "file_path": "evaluation.md",
                "watch_files": ["demande.md", "specifications.md", "management.md", "production.md"]
            })
        }


        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Panneau de contrôle
        self.control_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.start_button = ttk.Button(
            self.control_frame, 
            text="Start", 
            command=self.start_agents,
            style='Modern.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            self.control_frame, 
            text="Stop", 
            command=self.stop_agents,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(
            self.control_frame, 
            text="Reset Files", 
            command=self.reset_files
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            self.control_frame, 
            text="● Stopped", 
            foreground="red"
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Création d'un frame horizontal pour la demande et les logs
        self.horizontal_frame = ttk.Frame(self.root)
        self.horizontal_frame.pack(fill=tk.X, padx=20, pady=10)

        # Zone de demande interactive (à gauche)
        self.request_frame = ttk.LabelFrame(
            self.horizontal_frame, 
            text="Demande",
            style='Modern.TLabelframe'
        )
        self.request_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.demand_text = scrolledtext.ScrolledText(
            self.request_frame, 
            height=4,  # Réduit la hauteur pour correspondre aux logs
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg=self.colors['panel_bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            selectbackground=self.colors['accent'],
            relief='flat',
            padx=10,
            pady=10
        )
        self.demand_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ajouter un binding pour sauvegarder automatiquement
        self.demand_text.bind('<KeyRelease>', self.auto_save_demand)

        # Zone de logs (à droite)
        self.log_frame = ttk.LabelFrame(
            self.horizontal_frame, 
            text="Logs",
            style='Modern.TLabelframe'
        )
        self.log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=4,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg=self.colors['panel_bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            selectbackground=self.colors['accent'],
            relief='flat',
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Style pour les zones de texte
        text_style = {
            'font': ('Segoe UI', 10),
            'bg': self.colors['panel_bg'],
            'fg': self.colors['text'],
            'insertbackground': self.colors['text'],
            'selectbackground': self.colors['accent'],
            'relief': 'flat',
            'padx': 10,
            'pady': 10
        }

        # Application du style aux widgets de texte
        self.request_text.configure(**text_style)
        self.demand_display.configure(**text_style)
        self.log_text.configure(**text_style)
        
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
        
        # Démarrage des agents
        self.log_message("🚀 Démarrage des agents...")
        for name, agent in self.agents.items():
            threading.Thread(target=agent.run, daemon=True).start()
            self.log_message(f"✓ Agent {name} démarré")
        
        # Démarrage de la boucle de mise à jour
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        self.log_message("✓ Boucle de mise à jour démarrée")
        
    def stop_agents(self):
        """Arrêt des agents"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Stopped", foreground="red")
        self.log_message("🛑 Arrêt des agents")
        
    def update_loop(self):
        """Boucle de mise à jour des panneaux"""
        while self.running:
            try:
                self.root.after(0, self.update_all_panels)
                self.log_message("🔄 Cycle de mise à jour")  # Log de debug
                time.sleep(self.update_interval / 1000)
            except Exception as e:
                self.log_message(f"❌ Erreur dans la boucle de mise à jour: {e}")
            
    def update_all_panels(self):
        """Mise à jour de tous les panneaux d'agents"""
        file_mapping = {
            "Specification": "specifications.md",
            "Management": "management.md",
            "Production": "production.md",
            "Evaluation": "evaluation.md"
        }
        
        # Mise à jour de l'affichage de la demande
        try:
            with open("demande.md", 'r', encoding='utf-8') as f:
                demand_content = f.read()
            current_demand = self.demand_text.get("1.0", tk.END).strip()
            if demand_content.strip() != current_demand:
                # Sauvegarder la position du curseur
                cursor_pos = self.demand_text.index(tk.INSERT)
                self.demand_text.delete("1.0", tk.END)
                self.demand_text.insert("1.0", demand_content)
                # Restaurer la position du curseur
                self.demand_text.mark_set(tk.INSERT, cursor_pos)
        except Exception as e:
            self.log_message(f"❌ Erreur lors de la mise à jour de la demande: {e}")
        
        update_count = 0
        for name, panel in self.agent_panels.items():
            try:
                # Indicateur visuel de mise à jour
                panel.frame.configure(style='Updating.TLabelframe')
                self.root.update_idletasks()
                
                file_path = file_mapping[name]
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Vérifie si le contenu a changé
                old_content = panel.text.get("1.0", tk.END).strip()
                if content.strip() != old_content:
                    panel.update_content(content)
                    update_count += 1
                    self.log_message(f"Mise à jour du panneau {name}")
                
                # Réinitialise le style après la mise à jour
                panel.frame.configure(style='TLabelframe')
                
            except Exception as e:
                error_msg = f"Error updating {name} panel: {e}"
                print(error_msg)
                self.log_message(f"❌ {error_msg}")
        
        if update_count > 0:
            self.log_message(f"✓ {update_count} panneau(x) mis à jour")
                
    def auto_save_demand(self, event=None):
        """Sauvegarde automatique du contenu de la demande"""
        try:
            current_content = self.demand_text.get("1.0", tk.END).strip()
            
            with open("demande.md", 'w', encoding='utf-8') as f:
                f.write(current_content)
                
            self.log_message("✓ Demande mise à jour")
        except Exception as e:
            self.log_message(f"❌ Erreur lors de la sauvegarde : {str(e)}")
            
    def log_message(self, message: str):
        """Ajoute un message horodaté aux logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "✨" if "réinitialisés" in message else "🔄" if "mise à jour" in message else "ℹ️"
        log_entry = f"{icon} [{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # Auto-scroll

    def reset_files(self):
        """Reset all files to their initial state"""
        try:
            # Initial content for each file
            initial_contents = {
                "demande.md": """# Demande Actuelle
[timestamp: {}]
[status: NEW]

Écrivez votre demande ici...

# Historique des Demandes""".format(datetime.now().strftime("%Y-%m-%d %H:%M")),

                "specifications.md": """# Spécification de Sortie
En attente de nouvelles demandes...

# Critères de Succès
- Critère principal 1
  * Sous-critère A
  * Sous-critère B
- Critère principal 2
  * Sous-critère A
  * Sous-critère B""",

                "management.md": """# Consignes Actuelles
En attente de nouvelles directives...

# TodoList
- [ ] En attente de demandes

# Actions Réalisées
- [{}] Création du fichier""".format(datetime.now().strftime("%Y-%m-%d %H:%M")),

                "production.md": """En attente de contenu à produire...""",

                "evaluation.md": """# Évaluations en Cours
- Critère 1: [⚠️] En attente
- Critère 2: [⚠️] En attente

# Vue d'Ensemble
- Progression: 0%
- Points forts: À déterminer
- Points à améliorer: À déterminer
- Statut global: EN_ATTENTE"""
            }

            # Write initial content to files
            for filename, content in initial_contents.items():
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Update GUI panels
            self.update_all_panels()
            self.log_message("✨ Tous les fichiers ont été réinitialisés")

        except Exception as e:
            self.log_message(f"❌ Erreur lors de la réinitialisation : {str(e)}")

    def run(self):
        """Démarrage de l'interface"""
        self.root.mainloop()


class AgentPanel:
    """Panneau d'affichage pour un agent"""
    def __init__(self, parent, title):
        self.frame = ttk.LabelFrame(
            parent, 
            text=title,
            style='Modern.TLabelframe'
        )
        
        self.text = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=('Segoe UI', 10),
            bg='#ffffff',
            fg='#202124',
            insertbackground='#202124',
            selectbackground='#1a73e8',
            relief='flat',
            padx=10,
            pady=10
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configuration du highlighting
        self.text.tag_configure(
            "highlight",
            background="#e8f0fe"
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
    config = {
        "anthropic_api_key": "your-api-key-here"
    }
    gui = ParallagonGUI(config)
    gui.run()
