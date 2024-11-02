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
from search_replace import SearchReplace

class ParallagonGUI:
    def __init__(self, config: Dict[str, Any]):
        self.root = tk.Tk()
        self.root.title("⚫ Parallagon")
        self.running = False
        self.update_interval = 1000  # ms
        self.config = config
        
        # Ajout des styles
        style = ttk.Style()
        style.configure('Updating.TLabelframe', background='#fff7e6')
        
        # Configuration de la fenêtre principale
        self.root.geometry("1200x800")
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
        
        # Ajouter une zone de logs
        self.log_frame = ttk.LabelFrame(self.root, text="Logs")
        self.log_frame.pack(fill=tk.X, padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=4,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
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
            
    def log_message(self, message: str):
        """Ajoute un message horodaté aux logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
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

Entrez votre demande ici...

# Historique des Demandes
- [INIT] Création du fichier""".format(datetime.now().strftime("%Y-%m-%d %H:%M")),

                "specifications.md": """# État Actuel
[status: ACTIVE]
En attente de nouvelles demandes.

# Signaux
- Aucun signal

# Contenu Principal
Spécifications du projet...

# Historique
- [INIT] Création du fichier""",

                "management.md": """# État Actuel
[status: ACTIVE]
En attente de tâches à coordonner.

# Signaux
- Aucun signal

# Contenu Principal
## TodoList du Projet
- [ ] En attente de demandes

## Priorités Actuelles
1. Traiter les nouvelles demandes

## Blocages Potentiels
- Aucun blocage

# Historique
- [INIT] Création du fichier""",

                "production.md": """# État Actuel
[status: READY]
En attente de tâches de développement.

# Signaux
- Aucun signal

# Contenu Principal
En attente de spécifications techniques...

# Historique
- [INIT] Création du fichier""",

                "evaluation.md": """# État Actuel
[status: READY]
En attente de contenu à évaluer.

# Signaux
- Aucun signal

# Contenu Principal
## Critères de Validation
- Qualité du code
- Tests unitaires
- Documentation

# Historique
- [INIT] Création du fichier"""
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
    config = {
        "anthropic_api_key": "your-api-key-here"
    }
    gui = ParallagonGUI(config)
    gui.run()
