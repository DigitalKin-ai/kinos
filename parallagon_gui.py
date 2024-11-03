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
from log_manager import LogManager
from agent_panel import AgentPanel
from gui_config import GUIConfig
from llm_service import LLMService
from file_manager import FileManager
from specifications_agent import SpecificationsAgent
from management_agent import ManagementAgent
from production_agent import ProductionAgent
from evaluation_agent import EvaluationAgent
import openai

class ParallagonGUI:
    # Class constants
    UPDATE_INTERVAL = 1000  # ms
    FILE_PATHS = {
        "demande": "demande.md",
        "specifications": "specifications.md", 
        "management": "management.md",
        "production": "production.md",
        "evaluation": "evaluation.md"
    }
    TAB_NAMES = ["Specification", "Evaluation", "Management", "Demande", "Suivi Mission"]

    TEST_DATA = """# Demande de Revue de Connaissances LLM : L'Impact de l'IA Générative sur l'Industrie Musicale

## 1. Contexte de la demande

### Demandeur de la revue
- Nom, prénom : Dupont, Marie
- Fonction : Responsable Innovation
- Département : R&D
- Mail : m.dupont@entreprise.com

### Destinataire principal
[x] Équipe/service spécifique : Division Innovation & Stratégie Digitale

### But d'usage
[x] Support pour prise de décision
*Précision : Aide à la définition de notre stratégie d'intégration des IA génératives dans notre processus de production musicale*

### Qualité principale attendue
[x] Rigueur du raisonnement
*Critère de succès : La revue permet d'identifier clairement les opportunités et risques liés à l'IA générative en musique, avec une argumentation solide pour chaque point.*

### Niveau de profondeur
[x] Approfondi (10-15 pages)

## 2. Spécification de la demande

### Sujet de synthèse
Réaliser une revue approfondie des impacts actuels et potentiels de l'IA générative sur l'industrie musicale, en se concentrant sur les aspects créatifs, économiques et juridiques.

### Objectif principal
Être capable de comprendre et d'anticiper les transformations majeures que l'IA générative apportera à l'industrie musicale dans les 5 prochaines années.

### Axes d'analyse spécifiques
- Axe 1 : Être capable d'identifier les principales technologies d'IA générative en musique et leurs capacités actuelles/futures
- Axe 2 : Être capable d'évaluer l'impact économique sur les différents acteurs de l'industrie musicale (artistes, labels, plateformes)
- Axe 3 : Être capable de comprendre les enjeux juridiques et éthiques liés à l'utilisation de l'IA en création musicale

### Domaines de connaissances
1. Technologies de l'IA
2. Industrie musicale
3. Économie numérique
4. Droit de la propriété intellectuelle
5. Éthique des technologies

## 3. Contraintes de format

### Structure demandée
1. Executive Summary
   - Synthèse des technologies clés
   - Impacts majeurs identifiés
   - Recommandations stratégiques

2. Corps principal structuré par axes
   - Technologies et capacités
   - Impact économique
   - Enjeux juridiques et éthiques

3. Annexes
   - Glossaire technique
   - Scénarios prospectifs

### Spécifications formelles
- Respect de toutes les contraintes de format standard du template
- Maximum 3 figures illustratives par axe
- Inclusion d'un tableau récapitulatif par section

### Éléments spécifiques requis
- Matrice SWOT pour l'industrie musicale face à l'IA
- Timeline prévisionnelle des évolutions technologiques
- Framework d'évaluation des risques et opportunités

## 4. Limitations et avertissements

### Précisions sur la nature des connaissances
Je comprends que cette synthèse sera basée uniquement sur les connaissances intégrées du LLM, sans recherche externe. Une attention particulière est demandée pour :
- Identifier clairement les zones d'incertitude
- Distinguer les faits établis des projections
- Signaler les domaines nécessitant une validation externe

### Validation requise
[x] Vérification des concepts clés
[x] Confirmation des conclusions principales
[x] Identification des zones d'incertitude

### Notes additionnelles
- Privilégier les exemples concrets pour illustrer les concepts
- Inclure des points de vue contradictoires quand ils existent
- Mettre en évidence les questions ouvertes et débats en cours"""

    # Class constants
    UPDATE_INTERVAL = 1000  # ms
    FILE_PATHS = {
        "demande": "demande.md",
        "specifications": "specifications.md",
        "management": "management.md",
        "production": "production.md",
        "evaluation": "evaluation.md"
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.root = tk.Tk()
        self.root.title("⚫ Parallagon")
        self.running = False
        self.updating = False
        self.config = config
        self.gui_config = GUIConfig()
        
        # Use update interval from gui_config
        self.update_interval = self.gui_config.update_interval
        
        # Initialize services
        self.llm_service = LLMService(config["openai_api_key"])
        self.file_manager = FileManager(self.FILE_PATHS)
        self.agent_threads = {}  # Store agent threads
        self.tab_states = {
            "Specification": False,
            "Evaluation": False,
            "Management": False,
            "Demande": False,
            "Suivi Mission": False
        }
        self.tab_flash_tasks = {}

        self._setup_styles()
        
        # Configuration de la fenêtre
        self.root.configure(bg=self.gui_config.colors['bg'])
        
        # Configuration de la fenêtre principale
        self.root.state('zoomed')  # Pour Windows
        # self.root.attributes('-zoomed', True)  # Pour Linux
        self.setup_ui()
        
        # Charger le contenu initial de la demande
        try:
            with open("demande.md", 'r', encoding='utf-8') as f:
                initial_content = f.read()
                self.demand_text.delete("1.0", tk.END)
                self.demand_text.insert("1.0", initial_content)
        except Exception as e:
            self.log_message(f"❌ Erreur lors du chargement initial de la demande: {str(e)}")
        
        self.init_agents()
        
    def init_agents(self):
        """Initialisation des agents avec une configuration standardisée"""
        base_config = {
            "check_interval": 5,
            "anthropic_api_key": self.config["anthropic_api_key"],
            "openai_api_key": self.config["openai_api_key"],
            "logger": self.log_message
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


        
    def _setup_styles(self):
        """Configure les styles de l'interface"""
        style = ttk.Style()
        style.configure('Modern.TButton', 
            padding=10, 
            font=('Segoe UI', 10),
            background=self.gui_config.colors['accent']
        )
        style.configure('Modern.TLabelframe', 
            background=self.gui_config.colors['panel_bg'],
            padding=10
        )
        style.configure('Modern.TLabel', 
            font=('Segoe UI', 10),
            background=self.gui_config.colors['bg']
        )
        style.configure('Updating.TLabelframe', 
            background=self.gui_config.colors['highlight']
        )

    def _create_text_widget(self, parent) -> scrolledtext.ScrolledText:
        """Create a standardized text widget"""
        return scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=(self.gui_config.font_family, self.gui_config.font_size),
            bg=self.gui_config.colors['panel_bg'],
            fg=self.gui_config.colors['text']
        )

    def _create_agent_panel(self, parent, title: str) -> AgentPanel:
        """Create a standardized agent panel"""
        text_widget = self._create_text_widget(parent)
        text_widget.pack(fill=tk.BOTH, expand=True)
        return AgentPanel(parent, title, text_widget)

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

        self.test_data_button = ttk.Button(
            self.control_frame, 
            text="Données de test", 
            command=self.load_test_data
        )
        self.test_data_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            self.control_frame, 
            text="● Stopped", 
            foreground="red"
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        self.update_indicator = ttk.Label(
            self.control_frame,
            text="○",  # cercle vide quand pas de mise à jour
            foreground="blue"
        )
        self.update_indicator.pack(side=tk.RIGHT, padx=2)
        
        # Création du conteneur principal
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panneau gauche avec tabs
        self.left_frame = ttk.Frame(self.main_container)
        self.tab_control = ttk.Notebook(self.left_frame)
        
        # Création des tabs
        self.tabs = {}
        self.agent_panels = {}
        for tab_name in ["Specification", "Evaluation", "Management", "Demande", "Suivi Mission"]:
            tab = ttk.Frame(self.tab_control)
            self.tabs[tab_name] = tab
            self.tab_control.add(tab, text=tab_name)
            
            # Création du contenu pour chaque tab
            if tab_name == "Demande":
                self.demand_text = scrolledtext.ScrolledText(
                    tab, wrap=tk.WORD, font=('Segoe UI', 10),
                    bg=self.gui_config.colors['panel_bg'], fg=self.gui_config.colors['text']
                )
                self.demand_text.pack(fill=tk.BOTH, expand=True)
                self.demand_text.bind('<KeyRelease>', self.auto_save_demand)
            elif tab_name == "Suivi Mission":
                self.log_text = scrolledtext.ScrolledText(
                    tab, 
                    wrap=tk.WORD, 
                    font=('Segoe UI', 12),  # Police plus grande
                    bg=self.gui_config.colors['panel_bg'],  # Use configured color
                    fg=self.gui_config.colors['text'],      # Use configured color
                    padx=15,               # Padding horizontal plus important
                    pady=15                # Padding vertical plus important
                )
                self.log_text.pack(fill=tk.BOTH, expand=True)
                self.log_manager = LogManager(self.log_text)
            else:
                text_widget = scrolledtext.ScrolledText(
                    tab, wrap=tk.WORD, font=('Segoe UI', 10),
                    bg=self.gui_config.colors['panel_bg'], fg=self.gui_config.colors['text']
                )
                text_widget.pack(fill=tk.BOTH, expand=True)
                self.agent_panels[tab_name] = AgentPanel(tab, tab_name, text_widget)

        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Panneau droit (Production)
        self.right_frame = ttk.LabelFrame(self.main_container, text="Production")
        self.production_text = scrolledtext.ScrolledText(
            self.right_frame, wrap=tk.WORD, font=('Segoe UI', 10),
            bg=self.gui_config.colors['panel_bg'], fg=self.gui_config.colors['text']
        )
        self.production_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.agent_panels["Production"] = AgentPanel(self.right_frame, "Production", self.production_text)

        # Ajout des panneaux au conteneur principal
        self.main_container.add(self.left_frame, weight=1)
        self.main_container.add(self.right_frame, weight=1)
            
    def start_agents(self):
        """Démarrage des agents"""
        self.running = True
        self.updating = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="● Running", foreground="green")
        
        # Démarrage des agents
        self.log_message("🚀 Démarrage des agents...")
        for name, agent in self.agents.items():
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()
            self.agent_threads[name] = thread  # Store the thread
            self.log_message(f"✓ Agent {name} démarré")
        
        # Démarrage de la boucle de mise à jour
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        self.log_message("✓ Boucle de mise à jour démarrée")
        
    def stop_agents(self):
        """Arrêt des agents"""
        # D'abord arrêter les flags
        self.running = False
        self.updating = False
        
        # Arrêter chaque agent et attendre qu'il s'arrête
        for name, agent in self.agents.items():
            try:
                agent.stop()  # Arrête l'agent
                if name in self.agent_threads:
                    # Attendre que le thread se termine avec un timeout
                    thread = self.agent_threads[name]
                    thread.join(timeout=5)  # Augmenter le timeout à 5 secondes
                    
                    # Vérifier si le thread tourne encore
                    if thread.is_alive():
                        self.log_message(f"⚠️ L'agent {name} ne répond pas, forçage de l'arrêt...")
                        # Ici on pourrait implémenter un forçage plus agressif si nécessaire
                    else:
                        self.log_message(f"✓ Agent {name} arrêté")
            except Exception as e:
                self.log_message(f"❌ Erreur lors de l'arrêt de l'agent {name}: {e}")
        
        # Attendre que la boucle de mise à jour se termine
        if hasattr(self, 'update_thread'):
            self.update_thread.join(timeout=5)
            if self.update_thread.is_alive():
                self.log_message("⚠️ La boucle de mise à jour ne répond pas")
        
        # Nettoyer les threads
        self.agent_threads.clear()
        
        # Mettre à jour l'interface
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Stopped", foreground="red")
        self.update_indicator.config(text="○")
        
        self.log_message("🛑 Tous les agents ont été arrêtés")
        
    def update_loop(self):
        """Boucle de mise à jour des panneaux"""
        while self.running and self.updating:
            try:
                # Utiliser after() au lieu d'appels directs pour éviter le blocage de l'interface
                self.root.after(0, self._do_update)
                time.sleep(self.update_interval / 1000)  # Convert ms to seconds
            except Exception as e:
                self.log_message(f"❌ Erreur dans la boucle de mise à jour: {e}")

    def _do_update(self):
        """Effectue la mise à jour sans bloquer l'interface"""
        try:
            self.update_indicator.config(text="●")
            self.update_all_panels()
            self.root.after(100, lambda: self.update_indicator.config(text="○"))
        except Exception as e:
            self.log_message(f"❌ Erreur lors de la mise à jour: {e}")
            
    def flash_tab(self, tab_name):
        """Fait flasher un tab pour indiquer une mise à jour"""
        if tab_name not in self.tab_flash_tasks:
            style = ttk.Style()
            tab_style = f"Flash.{tab_name}.TFrame"
            
            def flash_cycle(count=0):
                if count >= 6 or tab_name not in self.tab_flash_tasks:  # 3 flashs complets
                    if tab_name in self.tab_flash_tasks:
                        self.tab_flash_tasks.pop(tab_name)
                    self.tab_states[tab_name] = False
                    return
                    
                new_color = "#e8f0fe" if count % 2 == 0 else "white"
                style.configure(tab_style, background=new_color)
                
                self.tab_flash_tasks[tab_name] = self.root.after(
                    100,  # Plus rapide pour plus de fluidité
                    lambda: flash_cycle(count + 1)
                )
                
            flash_cycle()

    def update_all_panels(self):
        """Mise à jour de tous les panneaux d'agents"""
        def read_file_content(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None

        try:
            updated_panels = []
            changes = {}

            # Lecture des fichiers en parallèle
            file_contents = {}
            threads = []
            
            for name, file_path in self.FILE_PATHS.items():
                def read_for_file(n=name, p=file_path):
                    file_contents[n] = read_file_content(p)
                thread = threading.Thread(target=read_for_file)
                thread.start()
                threads.append(thread)

            # Attendre la fin des lectures
            for thread in threads:
                thread.join(timeout=0.1)  # Court timeout pour éviter le blocage

            # Mise à jour de l'interface
            for name, content in file_contents.items():
                if content is None:
                    continue
                    
                # Traitement spécial pour le panneau Demande
                if name == "demande":
                    old_content = self.demand_text.get("1.0", tk.END).strip()
                    if content.strip() != old_content:
                        self.demand_text.delete("1.0", tk.END)
                        self.demand_text.insert("1.0", content)
                        updated_panels.append("Demande")
                        changes["Demande"] = {"old": old_content, "new": content}
                        self.flash_tab("Demande")
                # Traitement normal pour les autres panneaux
                elif name in self.agent_panels:
                    old_content = self.agent_panels[name].text.get("1.0", tk.END).strip()
                    if content.strip() != old_content:
                        self.agent_panels[name].update_content(content)
                        updated_panels.append(name)
                        changes[name] = {"old": old_content, "new": content}
                        if name != "Production":
                            self.flash_tab(name)

            if updated_panels:
                self._get_changes_summary(changes)

        except Exception as e:
            self.log_message(f"❌ Erreur lors de la mise à jour des panneaux: {str(e)}")

    def _background_task(self, task, callback=None):
        """Execute heavy tasks in background thread"""
        def wrapper():
            try:
                result = task()
                if callback:
                    self.root.after(0, lambda: callback(result))
            except Exception as e:
                self.log_message(f"❌ Erreur dans la tâche en arrière-plan: {str(e)}")
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    def _get_changes_summary(self, changes: dict) -> None:
        """Get summary of changes using LLM service asynchronously"""
        def task():
            return self.llm_service.get_changes_summary(changes)
            
        def callback(summary):
            if summary:
                self.log_message(f"✓ {summary}")
        
        self._background_task(task, callback)
                
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
        """Add a timestamped message to logs"""
        if hasattr(self, 'log_manager'):
            self.log_manager.log(message)
        else:
            print(f"Log: {message}")  # Fallback if log_manager not initialized

    def reset_files(self):
        """Reset all files to their initial state"""
        if self.file_manager.reset_files():
            self.update_all_panels()
            self.log_message("✨ Tous les fichiers ont été réinitialisés")
        else:
            self.log_message("❌ Erreur lors de la réinitialisation des fichiers")

    def load_test_data(self):
        """Charge les données de test dans la zone de demande"""
        try:
            # Mise à jour du widget de texte
            self.demand_text.delete("1.0", tk.END)
            self.demand_text.insert("1.0", self.TEST_DATA)
            
            # Sauvegarde dans le fichier
            with open("demande.md", 'w', encoding='utf-8') as f:
                f.write(self.TEST_DATA)
                
            self.log_message("✨ Données de test chargées")
            
        except Exception as e:
            self.log_message(f"❌ Erreur lors du chargement des données de test : {str(e)}")
            if self.file_manager.reset_files():
                self.update_all_panels()
                self.log_message("✨ Tous les fichiers ont été réinitialisés")
            else:
                self.log_message("❌ Erreur lors de la réinitialisation des fichiers")

        except Exception as e:
            self.log_message(f"❌ Erreur lors de la réinitialisation : {str(e)}")

    def _create_text_widget(self, parent) -> scrolledtext.ScrolledText:
        """Create a standardized text widget"""
        return scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=(self.gui_config.font_family, self.gui_config.font_size),
            bg=self.gui_config.colors['panel_bg'],
            fg=self.gui_config.colors['text']
        )

    def _create_agent_panel(self, parent, title: str) -> AgentPanel:
        """Create a standardized agent panel"""
        text_widget = self._create_text_widget(parent)
        text_widget.pack(fill=tk.BOTH, expand=True)
        return AgentPanel(parent, title, text_widget)

    def run(self):
        """Démarrage de l'interface"""
        self.root.mainloop()




if __name__ == "__main__":
    config = {
        "anthropic_api_key": "your-api-key-here"
    }
    gui = ParallagonGUI(config)
    gui.run()
