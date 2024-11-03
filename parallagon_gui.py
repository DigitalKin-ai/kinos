"""
ParallagonGUI - Interface graphique pour le framework Parallagon
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
from section import Section
from collapsible_section import CollapsibleSection
from section_edit_dialog import SectionEditDialog
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
    TAB_NAMES = ["Demande", "Specification", "Management", "Evaluation", "Suivi Mission"]

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

        # Mapping entre les noms de fichiers et les noms de panneaux
        self.panel_mapping = {
            "specifications": "Specification",
            "management": "Management", 
            "production": "Production",  # Ajout de production
            "evaluation": "Evaluation"
        }

        self._setup_styles()
        
        # Configuration de la fenêtre
        self.root.configure(bg=self.gui_config.colors['bg'])
        
        # Configuration de la fenêtre principale
        self.root.state('zoomed')  # Pour Windows
        # self.root.attributes('-zoomed', True)  # Pour Linux
        self.setup_ui()
        
        # Initialisation du contenu des panneaux
        self.log_message("🚀 Initialisation des panneaux...")
        
        for file_key, file_path in self.FILE_PATHS.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Traitement spécial pour le panneau Demande
                    if file_key == "demande":
                        if hasattr(self, 'demand_text'):
                            self.demand_text.delete("1.0", tk.END)
                            self.demand_text.insert("1.0", content)
                            self.log_message(f"✓ Panneau Demande initialisé")
                    
                    # Traitement pour les autres panneaux
                    elif file_key in self.panel_mapping:
                        panel_name = self.panel_mapping[file_key]
                        if panel_name in self.agent_panels:
                            self.agent_panels[panel_name].text.delete("1.0", tk.END)
                            self.agent_panels[panel_name].text.insert("1.0", content)
                            self.log_message(f"✓ Panneau {panel_name} initialisé")
                
            except FileNotFoundError:
                self.log_message(f"⚠️ Fichier {file_path} non trouvé, utilisation du contenu par défaut")
                default_content = self.file_manager._get_initial_contents().get(file_key, "")
                
                if file_key == "demande" and hasattr(self, 'demand_text'):
                    self.demand_text.delete("1.0", tk.END)
                    self.demand_text.insert("1.0", default_content)
                elif file_key in self.panel_mapping:
                    panel_name = self.panel_mapping[file_key]
                    if panel_name in self.agent_panels:
                        self.agent_panels[panel_name].text.delete("1.0", tk.END)
                        self.agent_panels[panel_name].text.insert("1.0", default_content)
                    
            except Exception as e:
                self.log_message(f"❌ Erreur lors de l'initialisation de {file_key}: {str(e)}")
        
        self.log_message("✓ Initialisation des panneaux terminée")
        
        # Initialisation des agents après les panneaux
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
        
        # Configuration du style de base des tabs
        style.configure('TNotebook.Tab', padding=[10, 5])
        
        # Style pour les boutons ON
        style.configure('Success.TButton',
            background='green',
            foreground='white'
        )
        
        # Créer un style spécifique pour chaque état de tab
        for tab_name in self.TAB_NAMES:
            style.configure(
                f'Flash.{tab_name}.TNotebook.Tab',
                background="#e8f0fe",
                padding=[10, 5]
            )
            
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

    def _edit_section(self, section: Section):
        """Open edit dialog for a section"""
        dialog = SectionEditDialog(self.root, section)
        if dialog.result:
            self._update_section(section)
            
    def _update_section(self, section: Section):
        """Update section content in files"""
        try:
            # Update in production.md
            with open("production.md", 'r', encoding='utf-8') as f:
                content = f.read()
                
            result = SearchReplace.section_replace(
                content,
                section.title,
                section.content or "[En attente de contenu]"
            )
            
            if result.success:
                with open("production.md", 'w', encoding='utf-8') as f:
                    f.write(result.new_content)
                self.log_message(f"✓ Section '{section.title}' mise à jour")
            else:
                self.log_message(f"❌ Erreur lors de la mise à jour de la section: {result.message}")
                
        except Exception as e:
            self.log_message(f"❌ Erreur lors de la mise à jour: {str(e)}")
            
    def _create_text_widget(self, parent) -> scrolledtext.ScrolledText:
        """Create a standardized text widget"""
        return scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=(self.gui_config.font_family, self.gui_config.font_size),
            bg=self.gui_config.colors['panel_bg'],
            fg=self.gui_config.colors['text']
        )

    def _parse_sections(self, specs_content: str) -> dict:
        """Extrait les sections et leurs contraintes depuis specifications.md"""
        sections = {}
        current_section = None
        current_content = []
        constraints = ""
        
        for line in specs_content.split('\n'):
            # Gestion des titres de niveau 1
            if line.startswith('# '):
                # Sauvegarder la section précédente
                if current_section:
                    sections[current_section] = {
                        "constraints": constraints.strip(),
                        "content": "\n".join(current_content).strip(),
                        "subsections": {}
                    }
            
                # Nouvelle section
                current_section = line[2:].strip()
                current_content = []
                constraints = ""
                
            # Gestion des titres de niveau 2
            elif line.startswith('## '):
                # Sauvegarder la sous-section précédente
                if current_subsection and current_section:
                    sections[current_section]["subsections"][current_subsection] = {
                        "constraints": constraints.strip(),
                        "content": ""
                    }
            
                # Nouvelle sous-section
                current_subsection = line[3:].strip()
                constraints = ""
                if current_section:
                    if current_subsection not in sections[current_section]["subsections"]:
                        sections[current_section]["subsections"][current_subsection] = {
                            "constraints": "",
                            "content": ""
                        }
        
            # Gestion des contraintes
            elif line.startswith('[contraintes:'):
                constraints = line[12:-1].strip()
                if current_section:
                    if current_subsection:
                        sections[current_section]["subsections"][current_subsection]["constraints"] = constraints
                    else:
                        sections[current_section]["constraints"] = constraints

        # Sauvegarder la dernière section/sous-section
        if current_section:
            if current_subsection:
                sections[current_section]["subsections"][current_subsection] = {
                    "constraints": constraints.strip(),
                    "content": ""
                }
            else:
                sections[current_section]["constraints"] = constraints.strip()
                
        return sections

    def _add_production_content(self, sections_data: dict, prod_content: str):
        """Ajoute le contenu de production aux sections"""
        current_section = None
        current_subsection = None
        current_content = []
        
        for line in prod_content.split('\n'):
            # Gestion des titres de niveau 1
            if line.startswith('# '):
                if current_section:
                    if current_subsection:
                        if current_section in sections_data and current_subsection in sections_data[current_section]["subsections"]:
                            sections_data[current_section]["subsections"][current_subsection]["content"] = '\n'.join(current_content).strip()
                    else:
                        if current_section in sections_data:
                            sections_data[current_section]["content"] = '\n'.join(current_content).strip()
                current_section = line[2:].strip()
                current_subsection = None
                current_content = []
            
            # Gestion des titres de niveau 2
            elif line.startswith('## '):
                if current_section:
                    if current_subsection:
                        if current_section in sections_data and current_subsection in sections_data[current_section]["subsections"]:
                            sections_data[current_section]["subsections"][current_subsection]["content"] = '\n'.join(current_content).strip()
                    else:
                        if current_section in sections_data:
                            sections_data[current_section]["content"] = '\n'.join(current_content).strip()
                current_subsection = line[3:].strip()
                current_content = []
            
            # Ajout du contenu
            else:
                current_content.append(line)
        
        # Ajouter le dernier contenu
        if current_section:
            if current_subsection:
                if current_section in sections_data and current_subsection in sections_data[current_section]["subsections"]:
                    sections_data[current_section]["subsections"][current_subsection]["content"] = '\n'.join(current_content).strip()
            elif current_section in sections_data:
                sections_data[current_section]["content"] = '\n'.join(current_content).strip()
        
        # Ajout du contenu
        else:
            current_content.append(line)
        
        # Ajouter le dernier contenu
        if current_section:
            if current_subsection:
                if current_section in sections_data and current_subsection in sections_data[current_section]["subsections"]:
                    sections_data[current_section]["subsections"][current_subsection]["content"] = '\n'.join(current_content).strip()
            elif current_section in sections_data:
                sections_data[current_section]["content"] = '\n'.join(current_content).strip()

    def _update_sections_display(self, sections_data: dict):
        """Met à jour l'affichage des sections"""
        # Supprimer les sections qui n'existent plus
        for title in list(self.sections.keys()):
            if title not in sections_data:
                self.sections[title].destroy()
                del self.sections[title]
        
        # Mettre à jour ou créer les sections
        for title, data in sections_data.items():
            # Ignorer les sections vides
            if not data.get("constraints") and not data.get("content"):
                continue
                
            section = Section(
                title=title,
                constraints=data.get("constraints", ""),
                content=data.get("content", ""),
                todo=data.get("todo", [])
            )
            
            if title in self.sections:
                # Mettre à jour la section existante
                self.sections[title].update_content(data.get("content", ""))
                if hasattr(self.sections[title], 'update_todos'):
                    self.sections[title].update_todos(data.get("todo", []))
            else:
                # Créer une nouvelle section
                collapsible = CollapsibleSection(
                    self.sections_scrollable_frame,
                    section,
                    callbacks={
                        'on_edit': lambda s=section: self._edit_section(s),
                        'on_update': lambda s=section: self._update_section(s)
                    }
                )
                collapsible.pack(fill=tk.X, padx=5, pady=2)
                self.sections[title] = collapsible

    def _create_agent_panel(self, parent, title: str) -> AgentPanel:
        """Create a standardized agent panel"""
        text_widget = self._create_text_widget(parent)
        text_widget.pack(fill=tk.BOTH, expand=True)
        return AgentPanel(parent, title, text_widget)

    def toggle_agent(self, agent_name: str) -> None:
        """Active ou désactive un agent spécifique"""
        if agent_name in self.agent_states:
            state = self.agent_states[agent_name]
            if state["running"]:
                self.stop_single_agent(agent_name)
            else:
                self.start_single_agent(agent_name)

    def start_single_agent(self, agent_name: str) -> None:
        """Démarre un agent spécifique"""
        try:
            if agent_name in self.agents:
                # Démarrer l'agent
                thread = threading.Thread(
                    target=self.agents[agent_name].run,
                    daemon=True
                )
                thread.start()
                self.agent_threads[agent_name] = thread
                
                # Mettre à jour l'état et le bouton
                self.agent_states[agent_name]["running"] = True
                self.agent_states[agent_name]["button"].configure(
                    text="ON",
                    style="Success.TButton"
                )
                
                self.log_message(f"✓ Agent {agent_name} démarré")
        except Exception as e:
            self.log_message(f"❌ Erreur lors du démarrage de l'agent {agent_name}: {str(e)}")

    def stop_single_agent(self, agent_name: str) -> None:
        """Arrête un agent spécifique"""
        try:
            if agent_name in self.agents:
                # Arrêter l'agent
                self.agents[agent_name].stop()
                
                if agent_name in self.agent_threads:
                    self.agent_threads[agent_name].join(timeout=5)
                    del self.agent_threads[agent_name]
                
                # Mettre à jour l'état et le bouton
                self.agent_states[agent_name]["running"] = False
                self.agent_states[agent_name]["button"].configure(
                    text="OFF",
                    style="TButton"
                )
                
                self.log_message(f"✓ Agent {agent_name} arrêté")
        except Exception as e:
            self.log_message(f"❌ Erreur lors de l'arrêt de l'agent {agent_name}: {str(e)}")

    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Panneau de contrôle
        self.control_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Ajouter un sous-frame pour les contrôles globaux
        self.global_controls = ttk.Frame(self.control_frame)
        self.global_controls.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(
            self.global_controls, 
            text="Start All", 
            command=self.start_agents,
            style='Modern.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            self.global_controls, 
            text="Stop All", 
            command=self.stop_agents,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Ajouter un sous-frame pour les contrôles individuels des agents
        self.agent_controls = ttk.Frame(self.control_frame)
        self.agent_controls.pack(side=tk.LEFT, padx=20)
        
        # Dictionnaire pour stocker les états des agents
        self.agent_states = {}
        
        # Créer les boutons ON/OFF pour chaque agent
        for agent_name in ["Specification", "Management", "Production", "Evaluation"]:
            agent_frame = ttk.Frame(self.agent_controls)
            agent_frame.pack(side=tk.LEFT, padx=10)
            
            ttk.Label(agent_frame, text=agent_name).pack(side=tk.TOP)
            
            toggle_button = ttk.Button(
                agent_frame,
                text="OFF",
                width=8,
                command=lambda n=agent_name: self.toggle_agent(n)
            )
            toggle_button.pack(side=tk.TOP, pady=2)
            
            # Stocker l'état et le bouton
            self.agent_states[agent_name] = {
                "running": False,
                "button": toggle_button
            }
        
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
        
        # Configure tab style
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[10, 5])
        
        # Création des tabs
        self.tabs = {}
        self.agent_panels = {}
        for tab_name in ["Demande", "Specification", "Management", "Evaluation", "Suivi Mission"]:
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
                    font=('Segoe UI', 12),
                    bg=self.gui_config.colors['panel_bg'],
                    fg=self.gui_config.colors['text'],
                    padx=15,
                    pady=15
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

        # Créer un PanedWindow vertical pour diviser le panneau droit
        self.right_paned = ttk.PanedWindow(self.right_frame, orient=tk.VERTICAL)
        self.right_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panneau supérieur (Sections)
        self.sections_frame = ttk.LabelFrame(self.right_paned, text="Sections")
        self.sections = {}  # Dictionnaire des sections {titre: CollapsibleSection}
        self.sections = {}  # Dictionnaire des sections {titre: CollapsibleSection}
        
        # Conteneur scrollable pour les sections
        self.sections_canvas = tk.Canvas(self.sections_frame)
        self.sections_scrollbar = ttk.Scrollbar(
            self.sections_frame, 
            orient="vertical", 
            command=self.sections_canvas.yview
        )
        self.sections_scrollable_frame = ttk.Frame(self.sections_canvas)
        
        self.sections_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.sections_canvas.configure(
                scrollregion=self.sections_canvas.bbox("all")
            )
        )
        
        self.sections_canvas.create_window((0, 0), window=self.sections_scrollable_frame, anchor="nw")
        self.sections_canvas.configure(yscrollcommand=self.sections_scrollbar.set)
        
        # Packing
        self.sections_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sections_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialiser les sections avec le contenu de production.md
        try:
            with open("production.md", 'r', encoding='utf-8') as f:
                prod_content = f.read()
            with open("specifications.md", 'r', encoding='utf-8') as f:
                specs_content = f.read()
                
            # Extraire les sections et leurs contraintes depuis specifications.md
            sections_data = self._parse_sections(specs_content)
            
            # Ajouter le contenu depuis production.md
            self._add_production_content(sections_data, prod_content)
            
            # Créer les sections dans l'interface
            self._update_sections_display(sections_data)
            
            self.log_message("✓ Sections initialisées avec succès")
            
        except FileNotFoundError:
            self.log_message("⚠️ Fichiers de sections non trouvés, initialisation par défaut")
        except Exception as e:
            self.log_message(f"❌ Erreur lors de l'initialisation des sections: {str(e)}")

        # Panneau inférieur (Production)
        self.production_frame = ttk.LabelFrame(self.right_paned, text="Production")
        self.production_text = scrolledtext.ScrolledText(
            self.production_frame, 
            wrap=tk.WORD, 
            font=('Segoe UI', 10),
            bg=self.gui_config.colors['panel_bg'], 
            fg=self.gui_config.colors['text']
        )
        self.production_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ajouter les deux panneaux au PanedWindow
        self.right_paned.add(self.sections_frame, weight=1)
        self.right_paned.add(self.production_frame, weight=1)

        # Ajouter le panneau droit au conteneur principal
        self.main_container.add(self.left_frame, weight=1)
        self.main_container.add(self.right_frame, weight=1)

        # Mettre à jour la référence pour l'AgentPanel
        self.agent_panels["Production"] = AgentPanel(self.production_frame, "Production", self.production_text)
            
    def start_agents(self):
        """Démarrage de tous les agents"""
        self.running = True
        self.updating = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="● Running", foreground="green")
        
        # Démarrer tous les agents
        self.log_message("🚀 Démarrage des agents...")
        for agent_name in self.agents.keys():
            self.start_single_agent(agent_name)
        
        # Démarrage de la boucle de mise à jour
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        self.log_message("✓ Boucle de mise à jour démarrée")
        
    def stop_agents(self):
        """Arrêt de tous les agents"""
        self.running = False
        self.updating = False
        
        # Arrêter tous les agents
        for agent_name in list(self.agent_threads.keys()):
            self.stop_single_agent(agent_name)
        
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
        """Fait flasher un tab en bleu pendant 1 seconde"""
        if tab_name not in self.tab_flash_tasks:
            try:
                # Obtenir l'index du tab
                tab_id = self.tab_control.index(self.tabs[tab_name])
                
                # Appliquer le style de flash spécifique au tab
                self.tab_control.tab(tab_id, style=f'Flash.{tab_name}.TNotebook.Tab')
                
                # Programmer le retour au style normal
                self.tab_flash_tasks[tab_name] = self.root.after(
                    1000,
                    lambda: self._restore_tab_style(tab_name, tab_id)
                )
            except Exception as e:
                self.log_message(f"❌ Erreur lors du flash du tab {tab_name}: {str(e)}")

    def _restore_tab_style(self, tab_name, tab_id):
        """Restaure le style normal du tab"""
        if tab_name in self.tab_flash_tasks:
            try:
                self.tab_flash_tasks.pop(tab_name)
                self.tab_control.tab(tab_id, style='TNotebook.Tab')
            except Exception as e:
                self.log_message(f"❌ Erreur lors de la restauration du style du tab {tab_name}: {str(e)}")

    def update_all_panels(self):
        """Mise à jour de tous les panneaux d'agents"""
        def read_file_content(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None

        def update_sections(specs_content, prod_content):
            # Extraire les sections et leurs contraintes depuis specifications.md
            sections_data = self._parse_sections(specs_content)
            
            # Ajouter le contenu depuis production.md
            self._add_production_content(sections_data, prod_content)
            
            # Mettre à jour l'affichage des sections
            self._update_sections_display(sections_data)

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
                # Traitement pour les autres panneaux
                elif name in self.panel_mapping:
                    panel_name = self.panel_mapping[name]
                    panel = self.agent_panels.get(panel_name)
                    if panel:
                        old_content = panel.text.get("1.0", tk.END).strip()
                        if content.strip() != old_content:
                            panel.update_content(content)
                            updated_panels.append(panel_name)
                            changes[panel_name] = {"old": old_content, "new": content}
                            if panel_name != "Production":
                                self.flash_tab(panel_name)

                        # Si c'est le panneau Specification, mettre à jour les sections
                        if panel_name == "Specification":
                            specs_content = content
                            prod_content = file_contents.get("production", "")
                            if specs_content and prod_content:
                                # Extraire les sections et leurs contraintes depuis specifications.md
                                sections_data = self._parse_sections(specs_content)
                                # Ajouter le contenu depuis production.md
                                self._add_production_content(sections_data, prod_content)
                                # Mettre à jour l'affichage des sections
                                self._update_sections_display(sections_data)

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
        try:
            if self.file_manager.reset_files():
                # Forcer la mise à jour immédiate de tous les panneaux
                for file_key, file_path in self.FILE_PATHS.items():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Mise à jour du panneau Demande
                            if file_key == "demande":
                                self.demand_text.delete("1.0", tk.END)
                                self.demand_text.insert("1.0", content)
                                
                            # Mise à jour des autres panneaux
                            elif file_key in self.panel_mapping:
                                panel_name = self.panel_mapping[file_key]
                                if panel_name in self.agent_panels:
                                    self.agent_panels[panel_name].text.delete("1.0", tk.END)
                                    self.agent_panels[panel_name].text.insert("1.0", content)
                                    self.agent_panels[panel_name].highlight_changes()
                                    
                    except Exception as e:
                        self.log_message(f"❌ Erreur lors de la mise à jour du panneau {file_key}: {str(e)}")
                        
                self.log_message("✨ Tous les fichiers ont été réinitialisés")
                return True
            else:
                self.log_message("❌ Erreur lors de la réinitialisation des fichiers")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Erreur lors de la réinitialisation : {str(e)}")
            return False

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
